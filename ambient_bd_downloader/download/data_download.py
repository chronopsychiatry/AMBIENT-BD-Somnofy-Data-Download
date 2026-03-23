import datetime
import json
import pandas as pd
import logging
from pathlib import Path

from ambient_bd_downloader.sf_api.dom import Subject, Session
from ambient_bd_downloader.download.compliance import ComplianceChecker
from ambient_bd_downloader.download.quality_checker import QualityChecker
from ambient_bd_downloader.storage.paths_resolver import PathsResolver
from ambient_bd_downloader.sf_api.somnofy import Somnofy


class DataDownloader:
    def __init__(self,
                 somnofy: Somnofy,
                 resolver: PathsResolver,
                 qc: QualityChecker = None,
                 compliance: ComplianceChecker = None,
                 ignore_epoch_for_shorter_than_hours=2,
                 filter_shorter_than_hours=5):
        if not somnofy:
            raise ValueError('Somnofy connection must be provided')
        self._somnofy = somnofy
        self._resolver = resolver
        self.qc = qc or QualityChecker()
        self._timestamp = datetime.datetime.now().strftime('%Y-%m-%d')
        self._compliance_checker = compliance or ComplianceChecker()
        self._compliance_checker.flag_shorter_than_hours = filter_shorter_than_hours
        self.ignore_epoch_for_shorter_than_hours = ignore_epoch_for_shorter_than_hours
        self._logger = logging.getLogger('DataDownloader')

    def save_subject_data(self,
                          subject: Subject,
                          start_date: str | datetime.date = None,
                          end_date: str | datetime.date = None,
                          force_saved_date: bool = True):
        self._logger.info(f'{subject}')
        start_date = self.calculate_start_date(subject.identifier, start_date, force_saved_date)
        self._logger.info(f'Downloading data for subject {subject.identifier} starting from {start_date}')
        sessions = self._somnofy.get_all_sessions_for_subject(subject.id, start_date, end_date)

        if len(sessions) == 0:
            self._logger.info(f'No sessions found for subject {subject.identifier} between {start_date} and {end_date}')
            return

        self._logger.info(f'Found {len(sessions)} sessions for subject {subject.identifier} between {start_date} and {end_date}')

        reports = []
        epoch_reports = []
        last_session = None
        last_session_json = None

        for s in sessions:
            self._logger.debug(f'Downloading session {s.session_id} for subject {subject.identifier}')

            s_json = self._somnofy.get_session_json(s.session_id)
            self.save_raw_session_data(s_json, subject.identifier, s.session_id)

            self.append_session_data(reports, s_json)

            if self._should_store_epoch_data(s):
                self.append_epoch_data(epoch_reports, s_json)

            last_session = s
            last_session_json = s_json

        reports = pd.DataFrame(reports)
        reports.insert(0, 'participant_id', subject.identifier)
        if len(epoch_reports) > 0:
            epoch_data = pd.concat([pd.DataFrame.from_dict(e) for e in epoch_reports], ignore_index=True)
            epoch_data.insert(0, 'participant_id', subject.identifier)
            epoch_data.insert(2, 'session_id', epoch_data.pop('session_id'))
        else:
            epoch_data = pd.DataFrame()

        if not last_session or not last_session.session_end:
            return
        dates = self._report_to_date_range(reports)

        self.save_reports(reports, subject.identifier)
        self.append_to_global_reports(reports, subject.identifier)
        self.save_epoch_data(epoch_data, subject.identifier)
        compliance_info = self._compliance_checker.calculate_compliance(reports, dates)
        self.save_compliance_info(compliance_info, subject.identifier, dates)
        self.save_last_session(last_session_json, subject.identifier)

    def save_quality_reports(self,
                             subject_list: list[Subject],
                             start_date: str | datetime.date = None,
                             end_date: str | datetime.date = None):
        subject_qc = []
        session_qc = []
        
        for sub in subject_list:
            subject_flags = set()
            sessions = self._somnofy.get_all_sessions_for_subject(sub.id, start_date, end_date)

            sessions = [s for s in sessions if not s.data.get('time_asleep') == 0]
            long_sessions = [s for s in sessions if s.data.get('sleep_period') > 7200]
            
            if len(sessions) == 0:
                self._logger.info(f'No sessions found for subject {sub.identifier} between {start_date} and {end_date}')
                continue
            else:
                self._logger.info(f'Running quality report for subject {sub.identifier} between {start_date} and {end_date} ({len(sessions)} sessions)')

            last_session = None
            n_flags = 0
            n_short = len(sessions) - len(long_sessions)

            for s in long_sessions:
                s_json = self._somnofy.get_session_json(s.session_id).get('data')

                metrics = self.qc.get_metrics(s_json, last_session)
                flags = self.qc.get_flags(metrics)

                if len(flags) > 0:
                    n_flags += 1
                    subject_flags.update(flags)
                    session_qc = self.qc.update_session_qc(session_qc, metrics, flags, sub)

                last_session = s_json

            if len(subject_flags) > 0:
                subject_qc = self.qc.update_subject_qc(subject_qc, subject_flags, len(sessions), n_flags, n_short, sub)

        if len(session_qc) == 0:
            self._logger.info('No flags were raised! No quality reports to save.')
            return
        self.save_session_qc(session_qc, start_date, end_date)
        self.save_subject_qc(subject_qc, start_date, end_date)

    def _should_store_epoch_data(self, session: Session) -> bool:
        return (not self.ignore_epoch_for_shorter_than_hours or
                (session.duration_seconds and
                 session.duration_seconds >= self.ignore_epoch_for_shorter_than_hours * 60 * 60))

    def append_session_data(self, reports: list[dict], s_json: dict) -> list[dict]:
        session_data = s_json['data'].copy()
        session_data.pop('epoch_data', None)
        reports.append(session_data)

    def append_epoch_data(self, epoch_reports: list[dict], s_json: dict) -> list[dict]:
        e_json = s_json['data']['epoch_data']
        e_json['session_id'] = s_json['data']['id']
        epoch_reports.append(e_json)

    def _is_in_progress(self, session: Session, subject_id: str) -> bool:
        if session.state == 'IN_PROGRESS':
            self._logger.debug(f'Skipping session {session.session_id} for subject {subject_id} as it is in progress')
            return True
        return False

    def calculate_start_date(self,
                             subject_id: str,
                             proposed_date: datetime.date = None,
                             force_saved_date: bool = True) -> datetime.date:

        if force_saved_date:
            start_date = self._get_date_from_last_session(subject_id) or proposed_date
        else:
            start_date = proposed_date or self._get_date_from_last_session(subject_id)

        if not start_date:
            raise ValueError(f'No start date found for subject {subject_id} and none proposed')

        return start_date

    def _get_date_from_last_session(self, subject_id: str) -> datetime.date | None:
        if not self._resolver.has_last_session(subject_id):
            return None

        session_file = self._resolver.get_subject_last_session(subject_id)
        with session_file.open('r') as f:
            session = json.load(f)
            session_end = datetime.datetime.fromisoformat(session['data']['session_end'])
            session_start = datetime.datetime.fromisoformat(session['data']['session_start'])
            # some sessions have duration of 0 and are being re-downloaded even if saved as last session
            # we add one microsecond to end time to avoid re-downloading
            if session_end == session_start:
                session_end = session_end + datetime.timedelta(microseconds=1)
            return session_end

    def save_raw_session_data(self, s_json: dict, subject_id: str, session_id: str):
        with self._raw_session_file(s_json, subject_id, session_id).open('w') as f:
            json.dump(s_json, f)

    def _raw_session_file(self, s_json: dict, subject_id: str, session_id: str) -> Path:
        start_date = datetime.datetime.fromisoformat(s_json['data']['session_start']).date()
        return self._resolver.get_subject_raw_dir(subject_id) / f'{start_date}_{session_id}_raw.json'

    def save_last_session(self, last_session_json: dict, subject_id: str):
        if last_session_json:
            path = self._resolver.get_subject_last_session(subject_id)
            with path.open('w') as f:
                json.dump(last_session_json, f)

    def save_reports(self, reports: pd.DataFrame, subject_id: str):
        path = self._reports_file(subject_id)
        reports.to_csv(path, index=False)

    def save_session_qc(self, session_qc: list[dict], start_date: str, end_date: str):
        df = (pd.DataFrame(session_qc)
              .sort_values('participant_id')
              )
        df.insert(1, 'participant_id', df.pop('participant_id'))
        path = self._resolver.get_session_qc(start_date, end_date)
        df.to_csv(path, index=False)
        self._logger.info(f'Saved Session quality report: {path}')

    def save_subject_qc(self, subject_qc: list[dict], start_date: str, end_date: str):
        df = (pd.DataFrame(subject_qc)
              .sort_values('fraction_flagged', ascending=False)
              )
        path = self._resolver.get_subject_qc(start_date, end_date)
        df.to_csv(path, index=False)
        self._logger.info(f'Saved Subject quality report: {path}')

    def _reports_file(self, subject_id: str) -> Path:
        return self._resolver.get_subject_data_dir(subject_id) / f'{subject_id}_SOM-Sess_{self._timestamp}.csv'

    def _sessions_to_date_range(self, first_session: dict, last_session: dict) -> tuple[datetime.date, datetime.date]:
        start_date = first_session.session_start.date()
        end_date = last_session.session_end.date()
        return start_date, end_date

    def _report_to_date_range(self, report: pd.DataFrame) -> tuple[datetime.date, datetime.date]:
        start_date = datetime.datetime.fromisoformat(report['session_start'].min()).date()
        end_date = datetime.datetime.fromisoformat(report['session_end'].max()).date()
        return start_date, end_date

    def save_epoch_data(self, epoch_data: pd.DataFrame, subject_id: str):
        epoch_data.to_csv(self._epoch_data_file(subject_id), index=False)

    def _epoch_data_file(self, subject_id: str) -> Path:
        return self._resolver.get_subject_data_dir(subject_id) / f'{subject_id}_SOM-Epoc_{self._timestamp}.csv'

    def append_to_global_reports(self, reports: pd.DataFrame, subject_id: str):
        file = self._resolver.get_subject_global_report(subject_id)
        reports.to_csv(file, mode='a', header=not file.exists(), index=False)

    def save_compliance_info(self,
                             compliance_info: pd.DataFrame,
                             subject_id: str,
                             dates: tuple[datetime.date, datetime.date]):
        path = self._compliance_file(subject_id, dates)
        compliance_info.to_csv(path, index=False)

    def _compliance_file(self, subject_id: str, dates: tuple[datetime.date, datetime.date]) -> Path:
        return self._resolver.get_subject_data_dir(subject_id) / f'{dates[0]}_{dates[1]}_compliance_info.csv'

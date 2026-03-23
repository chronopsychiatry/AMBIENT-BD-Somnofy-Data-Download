import json
import os
import tempfile
import datetime
import pytest

from ambient_bd_downloader.download.data_download import DataDownloader
from ambient_bd_downloader.sf_api.dom import Session, Subject
from ambient_bd_downloader.sf_api.somnofy import Somnofy
from ambient_bd_downloader.storage.paths_resolver import PathsResolver


# make class TestSomnofy subclass of Somnofy
class MockSomnofy(Somnofy):

    def __init__(self):
        self.test_session_json = './tests/data/2024-12-25_RkdSRhgMGQ8XFQAA_raw.json'
        print(f'mock session_json: {os.path.abspath(self.test_session_json)}')

    def _read_test_session_json(self):
        with open(self.test_session_json, 'r') as f:
            return json.load(f)

    def get_subjects(self):
        # return list of dictionaries
        return [{'id': '1', 'identifier': 'subject1'},
                {'id': '2', 'identifier': 'subject2'},
                {'id': '3', 'identifier': 'subject3'}]

    def get_all_sessions_for_subject(self, subject_id, from_date=None, to_date=None):
        session = Session(self._read_test_session_json()['data'])
        # return list of dictionaries
        return [session]

    def get_session_json(self, session_id):
        session = self._read_test_session_json()
        return session


class TestDataDownloader():

    mock_somnofy = MockSomnofy()
    test_dir = tempfile.TemporaryDirectory()
    mock_resolver = PathsResolver(path=test_dir.name)
    data_downloader = DataDownloader(somnofy=mock_somnofy, resolver=mock_resolver)

    def test_init_without_somnofy_raises_error(self):
        with pytest.raises(ValueError):
            DataDownloader(somnofy=None, resolver=self.mock_resolver)

    def test_save_subject_data(self):
        subject = Subject({'id': '1',
                           'identifier': 'subject1',
                           'device': 'VTFAKE',
                           'created_at': '2023-01-01T00:00:00'
                           })

        self.data_downloader.save_subject_data(subject, start_date=datetime.datetime.now() - datetime.timedelta(days=1))

        s_json = self.mock_somnofy._read_test_session_json()
        session_id = s_json['data']['id']
        session = Session(s_json['data'])
        dates = self.data_downloader._sessions_to_date_range(session, session)

        # check if raw data was saved
        raw_data_file = self.data_downloader._raw_session_file(s_json, subject.identifier, session_id)
        assert os.path.isfile(raw_data_file)

        # check if epoch data was saved
        epoch_data_file = self.data_downloader._epoch_data_file(subject.identifier)
        assert os.path.isfile(epoch_data_file)

        # check if reports were saved
        reports_file = self.data_downloader._reports_file(subject.identifier)
        assert os.path.isfile(reports_file)

        # check if last session was saved
        last_session_file = self.mock_resolver.get_subject_last_session(subject.identifier)
        assert os.path.isfile(last_session_file)

        # check if compliance data was saved
        compliance_file = self.data_downloader._compliance_file(subject.identifier, dates)
        assert os.path.isfile(compliance_file)

    def test_save_quality_reports(self):
        subject_list = [Subject({'id': '1',
                                 'identifier': 'subject1',
                                 'device': 'VTFAKE',
                                 'created_at': '2023-01-01T00:00:00'
                                 })]
        start_date = datetime.datetime.fromisoformat("2024-12-24")
        end_date = datetime.datetime.today()
        self.data_downloader.save_quality_reports(subject_list, start_date, end_date)

        subject_qc = self.mock_resolver.get_subject_qc(start_date, end_date)
        assert subject_qc.exists()
        
        session_qc = self.mock_resolver.get_session_qc(start_date, end_date)
        assert session_qc.exists()

    def test_session_to_date_range(self):
        s_json = self.mock_somnofy._read_test_session_json()
        s_session = Session(s_json['data'])
        e_json = self.mock_somnofy._read_test_session_json()
        e_session = Session(e_json['data'])

        start_date, end_date = self.data_downloader._sessions_to_date_range(s_session, e_session)
        assert start_date == datetime.date.fromisoformat('2024-12-25')
        assert end_date == datetime.date.fromisoformat('2024-12-25')

    def test_calculate_start_date_with_proposed_date(self):
        with pytest.raises(ValueError):
            self.data_downloader.calculate_start_date(subject_id='test_subject')

        proposed_date = '2020-01-01'
        assert (self.data_downloader
                .calculate_start_date(subject_id='test_subject', proposed_date=proposed_date)) == proposed_date

    def test_calculate_start_date_with_saved_date(self):
        proposed_date = '2020-01-01'
        last_session_file = self.mock_resolver.get_subject_last_session(subject_id='test_subject')
        last_session = {'session_start': '2023-01-01T00:00:00', 'session_end': '2023-01-01T02:00:00'}
        try:
            with open(last_session_file, 'w') as f:
                json.dump({'data': last_session}, f)

            last_session['session_end'] = datetime.datetime.fromisoformat(last_session['session_end'])
            assert self.data_downloader.calculate_start_date(subject_id='test_subject',
                                                             proposed_date=proposed_date,
                                                             force_saved_date=True) == last_session['session_end']
        finally:
            os.remove(last_session_file)

    def test_calculate_start_date_with_session_duration_zero(self):
        proposed_date = '2020-01-01'
        last_session_file = self.mock_resolver.get_subject_last_session(subject_id='test_subject')
        last_session = {'session_start': '2023-01-01T00:00:00', 'session_end': '2023-01-01T00:00:00'}
        try:
            with open(last_session_file, 'w') as f:
                json.dump({'data': last_session}, f)

            last_session['session_end'] = datetime.datetime.fromisoformat(last_session['session_end'])
            start_date = self.data_downloader.calculate_start_date(subject_id='test_subject',
                                                                   proposed_date=proposed_date,
                                                                   force_saved_date=True)
            assert start_date > last_session['session_end']
            assert start_date.replace(microsecond=0) == last_session['session_end']
        finally:
            os.remove(last_session_file)

    def test_should_store_epoch_data(self):
        session = Session(self.mock_somnofy._read_test_session_json()['data'])
        session.duration_seconds = 3600
        self.data_downloader.ignore_epoch_for_shorter_than_hours = None

        result = self.data_downloader._should_store_epoch_data(session)
        assert result

        self.data_downloader.ignore_epoch_for_shorter_than_hours = 2
        result = self.data_downloader._should_store_epoch_data(session)
        assert not result

        self.data_downloader.ignore_epoch_for_shorter_than_hours = 1
        result = self.data_downloader._should_store_epoch_data(session)
        assert result

    def test_tearDown(self):
        self.test_dir.cleanup()

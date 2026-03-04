from pathlib import Path
import logging


class PathsResolver:

    def __init__(self, path: str | Path = '../downloaded_data'):
        path = Path(path)
        self._logger = logging.getLogger('PathsResolver')
        self._main_dir = None
        self.set_main_dir(path)

    def set_main_dir(self, path: str | Path):
        path = Path(path)
        if not path.exists():
            path.mkdir(parents=True)
        if not path.is_dir():
            raise ValueError(f'Main storage: {path} is not a directory')
        self._main_dir = path
        self._logger.info(f'Using storage dir: {self._main_dir.absolute()}')

    def get_main_dir(self):
        return self._main_dir

    def get_subject_dir(self, subject_id: str) -> Path:
        subject_dir = self._main_dir / subject_id
        if not subject_dir.exists():
            subject_dir.mkdir(parents=True)
        return subject_dir

    def get_subject_sys_dir(self, subject_id: str) -> Path:
        sys_dir = self.get_subject_dir(subject_id) / 'sys'
        if not sys_dir.exists():
            sys_dir.mkdir(parents=True)
        return sys_dir

    def get_subject_data_dir(self, subject_id: str) -> Path:
        data_dir = self.get_subject_dir(subject_id) / 'data'
        if not data_dir.exists():
            data_dir.mkdir(parents=True)
        return data_dir

    def get_subject_raw_dir(self, subject_id: str) -> Path:
        raw_dir = self.get_subject_dir(subject_id) / 'raw'
        if not raw_dir.exists():
            raw_dir.mkdir(parents=True)
        return raw_dir

    def get_subject_last_session(self, subject_id: str) -> Path:
        return self.get_subject_sys_dir(subject_id) / 'last_session.json'

    def has_last_session(self, subject_id: str) -> bool:
        last_path = self.get_subject_sys_dir(subject_id) / 'last_session.json'
        return last_path.exists()

    def get_subject_global_report(self, subject_id: str) -> Path:
        return self.get_subject_data_dir(subject_id) / 'all_sessions_report.csv'

    def get_session_qc(self, from_date: str, to_date: str) -> Path:
        from_date = from_date.strftime('%Y-%m-%d')
        to_date = to_date.strftime('%Y-%m-%d')
        return self._main_dir / f"Session_qc_{from_date}-{to_date}.csv"

    def get_subject_qc(self, from_date: str, to_date: str) -> Path:
        from_date = from_date.strftime('%Y-%m-%d')
        to_date = to_date.strftime('%Y-%m-%d')
        return self._main_dir / f"Participant_qc_{from_date}-{to_date}.csv"

import datetime
import configparser
from pathlib import Path


class Properties():
    def __init__(self,
                 client_id_file: str | Path = None,
                 zone: str | list[str] = None,
                 device: str | list[str] = None,
                 subject: str | list[str] = None,
                 exclude_subjects: str = None,
                 download_dir: str | Path = '../downloaded_data',
                 from_date: str | datetime.date = None,
                 to_date: str | datetime.date = None,
                 log_level:str = 'INFO',
                 ignore_epoch_for_shorter_than_hours: str | float = None,
                 flag_nights_with_sleep_under_hours: str | float = None,
                 min_distance: float = None,
                 max_distance: float = None,
                 min_signal_quality: float = None,
                 max_fraction_no_presence: float = None,
                 max_fraction_awake: float = None,
                 min_session_separation: float = None
                 ):

        self.client_id_file = Path(client_id_file or './client_id.txt')
        self.zone_name = [z.strip() for z in zone.split(',')]
        self.device_name = [d.strip() for d in device.split(',')] or '*'
        self.subject_name = [s.strip() for s in subject.split(',')] or '*'
        self.exclude_subjects = exclude_subjects or '*'
        self.download_folder = Path(download_dir or '../downloaded_data')
        with self.client_id_file.open('r') as f:
            self.client_id = f.readline().strip(' \t\n\r')
        from_date = from_date or datetime.datetime.now() - datetime.timedelta(days=14)
        if isinstance(from_date, str):
            from_date = datetime.datetime.fromisoformat(from_date)
        self.from_date = from_date
        to_date = to_date or datetime.datetime.now()
        if to_date == '*':
            to_date = datetime.datetime.now()
        if isinstance(to_date, str):
            to_date = datetime.datetime.fromisoformat(to_date)
        check_dates(from_date, to_date)
        self.to_date = to_date
        self.log_level = log_level
        self.ignore_epoch_for_shorter_than_hours = float(ignore_epoch_for_shorter_than_hours or 2)
        self.flag_nights_with_sleep_under_hours = float(flag_nights_with_sleep_under_hours or 5)
        self.min_distance = float(min_distance or 0)
        self.max_distance = float(max_distance or 100)
        self.min_signal_quality = float(min_signal_quality or 0)
        self.max_fraction_no_presence = float(max_fraction_no_presence or 1)
        self.max_fraction_awake = float(max_fraction_awake or 1)
        self.min_session_separation = float(min_session_separation or 0)

    def __str__(self):
        return f"Properties({', '.join(f'{k}={v}' for k, v in vars(self).items() if k != 'client_id')})"


def load_application_properties(file_path: str | Path = './ambient_downloader.properties', output_type: str = 'download'):
    file_path = Path(file_path)
    config = configparser.ConfigParser()
    if file_path.exists():
        config.read(file_path)
    else:
        raise ValueError(f"Properties file not found: {file_path}. Run generate_config to create it.")

    default = {k.replace('-', '_'): v for k, v in config['DEFAULT'].items()}
    
    if output_type == 'download':
        return Properties(**default)
    elif output_type == 'quality':
        if 'QUALITY_REPORT' not in config.keys():
            raise ValueError("ambient_downloader.properties must contain a [QUALITY_REPORT] section")
        quality = {k.replace('-', '_'): v for k, v in config['QUALITY_REPORT'].items()}
        return Properties(**quality)

def check_dates(from_date, to_date):
    if from_date > to_date:
        raise ValueError(f'from-date ({from_date}) cannot be after to-date ({to_date})')

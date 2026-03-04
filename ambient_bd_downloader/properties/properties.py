import datetime
import configparser
from pathlib import Path


class Properties():
    def __init__(self,
                 client_id_file: str | Path = None,
                 zone_name: str | list[str] = None,
                 device_name: str | list[str] = None,
                 subject_name: str | list[str] = None,
                 exclude_subjects: str = None,
                 download_folder: str | Path = '../downloaded_data',
                 from_date: str | datetime.date = None,
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
        self.zone_name = zone_name
        self.device_name = device_name or '*'
        self.subject_name = subject_name or '*'
        self.exclude_subjects = exclude_subjects or '*'
        self.download_folder = Path(download_folder or '../downloaded_data')
        with self.client_id_file.open('r') as f:
            self.client_id = f.readline().strip(' \t\n\r')

        if from_date is None:
            from_date = datetime.datetime.now() - datetime.timedelta(days=14)
        # if from_date is a string, convert it to datetime
        if isinstance(from_date, str):
            from_date = datetime.datetime.fromisoformat(from_date)
        self.from_date = from_date
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
    if output_type == 'download':
        return Properties(
            client_id_file=config['DEFAULT'].get('client-id-file', None),
            zone_name=[zone.strip() for zone in config['DEFAULT'].get('zone').split(',')],
            device_name=[device.strip() for device in config['DEFAULT'].get('device').split(',')],
            subject_name=[subject.strip() for subject in config['DEFAULT'].get('subject').split(',')],
            exclude_subjects=config['DEFAULT'].get('exclude-subjects', None),
            download_folder=config['DEFAULT'].get('download-dir', None),
            from_date=config['DEFAULT'].get('from-date', None),
            log_level=config['DEFAULT'].get('log-level', 'INFO'),
            ignore_epoch_for_shorter_than_hours=config['DEFAULT'].get('ignore-epoch-for-shorter-than-hours', None),
            flag_nights_with_sleep_under_hours=config['DEFAULT'].get('flag-nights-with-sleep-under-hours', None)
        )
    elif output_type == 'quality':
        if 'QUALITY_REPORT' not in config.keys():
            raise ValueError("ambient_downloader.properties must contain a [QUALITY_REPORT] section")
        return Properties(
            client_id_file=config['DEFAULT'].get('client-id-file', None),
            zone_name=[zone.strip() for zone in config['DEFAULT'].get('zone').split(',')],
            device_name=[device.strip() for device in config['DEFAULT'].get('device').split(',')],
            subject_name=[subject.strip() for subject in config['DEFAULT'].get('subject').split(',')],
            exclude_subjects=config['DEFAULT'].get('exclude-subjects', None),
            download_folder=config['DEFAULT'].get('download-dir', None),
            from_date=config['DEFAULT'].get('from-date', None),
            log_level=config['DEFAULT'].get('log-level', 'INFO'),
            min_distance=config['QUALITY_REPORT'].get('min-distance', None),
            max_distance=config['QUALITY_REPORT'].get('max-distance', None),
            min_signal_quality=config['QUALITY_REPORT'].get('min-signal-quality', None),
            max_fraction_no_presence=config['QUALITY_REPORT'].get('max-fraction-no-presence', None),
            max_fraction_awake=config['QUALITY_REPORT'].get('max-fraction-awake', None),
            min_session_separation=config['QUALITY_REPORT'].get('min-session-separation', None)
        )

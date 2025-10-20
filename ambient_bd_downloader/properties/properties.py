import datetime
import configparser
from pathlib import Path


class Properties():
    def __init__(self,
                 credentials_file: str | Path = None,
                 credentials: dict = None,
                 zone_name: str | list[str] = None,
                 device_name: str | list[str] = None,
                 subject_name: str | list[str] = None,
                 download_folder: str | Path = '../downloaded_data',
                 from_date: str | datetime.date = None,
                 ignore_epoch_for_shorter_than_hours: str | float = None,
                 flag_nights_with_sleep_under_hours: str | float = None):

        self.credentials_file = Path(credentials_file or './credentials.txt')
        self.credentials = credentials or {}
        self.zone_name = zone_name
        self.device_name = device_name or '*'
        self.subject_name = subject_name or '*'
        self.download_folder = Path(download_folder or '../downloaded_data')

        if from_date is None:
            from_date = datetime.datetime.now() - datetime.timedelta(days=14)
        # if from_date is a string, convert it to datetime
        if isinstance(from_date, str):
            from_date = datetime.datetime.fromisoformat(from_date)
        self.from_date = from_date

        self.ignore_epoch_for_shorter_than_hours = float(ignore_epoch_for_shorter_than_hours or 2)
        self.flag_nights_with_sleep_under_hours = float(flag_nights_with_sleep_under_hours or 5)

    def __str__(self):
        return f"Properties(credentials_file={self.credentials_file}, " \
               f"zone_name={self.zone_name}, " \
               f"device_name={self.device_name}, subject_name={self.subject_name}, " \
               f"download_folder={self.download_folder}, from_date={self.from_date}, " \
               f"ignore_epoch_for_shorter_than_hours={self.ignore_epoch_for_shorter_than_hours}, " \
               f"flag_nights_with_sleep_under_hours={self.flag_nights_with_sleep_under_hours})"


def load_application_properties(file_path: str | Path = './ambient_downloader.properties'):
    file_path = Path(file_path)
    config = configparser.ConfigParser()
    if file_path.exists():
        config.read(file_path)
    else:
        raise ValueError(f"Properties file not found: {file_path}. Run generate_config to create it.")
    return Properties(
        credentials_file=config['DEFAULT'].get('credentials-file', None),
        credentials=load_credentials(config['DEFAULT'].get('credentials-file', None)),
        zone_name=[zone.strip() for zone in config['DEFAULT'].get('zone').split(',')],
        device_name=[device.strip() for device in config['DEFAULT'].get('device').split(',')],
        subject_name=[subject.strip() for subject in config['DEFAULT'].get('subject').split(',')],
        download_folder=config['DEFAULT'].get('download-dir', None),
        from_date=config['DEFAULT'].get('from-date', None),
        ignore_epoch_for_shorter_than_hours=config['DEFAULT'].get('ignore-epoch-for-shorter-than-hours', None),
        flag_nights_with_sleep_under_hours=config['DEFAULT'].get('flag-nights-with-sleep-under-hours', None)
    )


def load_credentials(credentials_file: str | Path) -> dict:
    file_path = Path(credentials_file)
    if not file_path.exists():
        raise ValueError(f"Credentials file not found: {file_path}.")
    creds = {}
    with file_path.open('r') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line:
                key, value = line.split('=', 1)
                creds[key.strip()] = value.strip()
    return (creds)

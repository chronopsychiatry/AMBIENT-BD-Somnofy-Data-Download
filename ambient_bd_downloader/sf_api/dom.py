import datetime
from tabulate import tabulate
import pandas as pd


def datetime_from_iso_string(string: str) -> datetime.datetime:
    if string.endswith('Z'):
        dt = datetime.datetime.fromisoformat(string[:-1])
    else:
        dt = datetime.datetime.fromisoformat(string.split('+')[0])
    return dt.replace(microsecond=0)


def date_from_iso_string(date_string: str) -> datetime.date:
    return datetime.datetime.fromisoformat(date_string).date()


def get_subjects_table(subject_list: list) -> str:
    """
    Generate a formatted table from a list of subjects.

    Args:
        None
    Returns:
        str: Formatted table as a string.
    """
    data = []
    for sub in subject_list:
        data.append(vars(sub))
    df = pd.DataFrame.from_records(data)
    return tabulate(df,
                    headers='keys',
                    tablefmt='psql'
                    )


class Session:
    def __init__(self, session_data: dict):
        self.data = session_data
        self.epoch_data = session_data.get('epoch_data', None)
        self.session_id = session_data['id']
        self.device_serial_number = session_data['device_serial_number']
        self.state = session_data['state']
        self.subject_id = session_data['subject_id']

        self.session_start = datetime_from_iso_string(session_data['session_start'])
        if session_data['session_end']:  # end-time not available for in progress sessions
            self.session_end = datetime_from_iso_string(session_data['session_end'])
            # Calculate duration in seconds
            self.duration_seconds = (self.session_end - self.session_start).total_seconds()
        else:
            self.session_end = None
            self.duration_seconds = None

    def __str__(self):
        return f"Session ID: {self.session_id}, Device Serial Number: {self.device_serial_number}, " \
               f"Start Time: {self.session_start}, End Time: {self.session_end}, " \
               f"State: {self.state}, Subject ID: {self.subject_id}, " \
               f"Duration (seconds): {self.duration_seconds}"


class Subject:
    def __init__(self, subject_data: dict):
        self.id = subject_data.get('id')
        self.identifier = subject_data.get('identifier')
        self.sex = subject_data.get('sex')
        self.birth_year = subject_data.get('birth_year')
        self.created_at = datetime_from_iso_string(subject_data.get('created_at'))
        self.device = get_nested_value(subject_data, ['devices', 'data', 0, 'name'])

    def __str__(self):
        return f"Subject ID: {self.id}, Identifier: {self.identifier}, " \
               f"Sex: {self.sex}, Birth year: {self.birth_year}, " \
               f"Created At: {self.created_at}, " \
               f"Device: {self.device}"


def get_subject_by_id(subjects, subject_id: str) -> Subject | None:
    return next((subject for subject in subjects if subject.id == subject_id), None)


def get_nested_value(data, keys: list[str], default=None):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        elif isinstance(data, list) and len(data) > int(key):
            data = data[int(key)]
        else:
            return default
    return data

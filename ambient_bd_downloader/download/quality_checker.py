import numpy as np
import datetime
import logging

from ambient_bd_downloader.sf_api.dom import Subject

class QualityChecker:
    """
    Run quality checks on the Somnofy data and output flagged sessions in csv format
    """
    def __init__(self,
                 min_distance: float = 0.4,
                 max_distance: float = 1.5,
                 min_signal_quality: float = 4,
                 max_fraction_no_presence: float = 0.2,
                 max_fraction_awake: float = 0.3,
                 min_session_separation: float = 15):
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.min_signal_quality = min_signal_quality
        self.max_fraction_no_presence = max_fraction_no_presence
        self.max_fraction_awake = max_fraction_awake
        self.min_session_separation = min_session_separation
        self._logger = logging.getLogger('QualityChecker')

    def get_metrics(self, session_json: dict, last_session: dict) -> dict:
        """
        Calculate quality-control metrics for the session

        Parameters:
        session_json (dict): The session in json format
        last_session (dict): The previous session in json format

        Returns:
        dict: The computed metrics
        """
        metrics = dict()

        sleep_onset_latency = session_json.get('sleep_onset_latency', 0) or 0

        metrics['id'] = session_json.get('id')
        metrics['session_start'] = session_json.get('session_start')
        metrics['session_end'] = session_json.get('session_end')
        metrics['distance'] = session_json.get('distance_during_sleep_mean')
        metrics['signal_quality'] = session_json.get('epoch_data').get('signal_quality_mean')
        metrics['signal_quality_mean'] = np.mean(metrics['signal_quality'])
        metrics['frac_no_presence'] = session_json.get('time_in_no_presence') / session_json.get('time_in_bed')
        metrics['frac_awake'] = (session_json.get('time_in_bed') - session_json.get('time_asleep')) / session_json.get('time_in_bed')
        metrics['sleep_onset_latency'] = datetime.timedelta(seconds=sleep_onset_latency)

        if last_session:
            metrics['time_to_previous_session'] = self.get_session_separation(session_json, last_session)
        else:
            metrics['time_to_previous_session'] = 'NA'

        return metrics
        
    def get_flags(self, metrics) -> list:
        """
        Get a list of flags from metrics based on the QualityChecker thresholds.

        Args:
        metrics (dict): data quality metrics calculated with `get_metrics`

        Returns:
        list: a list of flags that were raised
        """
        flags = []

        if (metrics['distance'] < self.min_distance) or (metrics['distance'] > self.max_distance):
            flags.append("distance")

        if sum(i < self.min_signal_quality for i in metrics['signal_quality']) / len(metrics['signal_quality']) > 0.8:
            flags.append("signal_quality")

        if metrics['frac_no_presence'] > self.max_fraction_no_presence:
            flags.append("fraction_no_presence")

        if metrics['frac_awake'] > self.max_fraction_awake:
            flags.append("fraction_awake")

        if metrics['sleep_onset_latency'] < datetime.timedelta(minutes=1):
            flags.append("started_asleep")

        if (metrics['time_to_previous_session'] != 'NA' and
            metrics['time_to_previous_session'] < datetime.timedelta(minutes=self.min_session_separation)):
            flags.append("split_session")

        return flags

    def is_split_session(self, session_json, last_session) -> bool:
        """
        Determine if two sessions are split, i.e. separated by less than a threshold

        Parameters:
        session_json (dict): the current session
        last_session (dict): the previous session

        Returns:
        bool: whether the sessions are ''split''
        """
        sep = self.get_session_separation(session_json, last_session)
        return sep < datetime.timedelta(minutes=self.min_session_separation)

    def get_session_separation(self, session_json, last_session) -> datetime.timedelta:
        """
        Calculate the time that separates the end of one session from the beginning of the next

        Parameters:
        session_json (dict): the current session
        last_session (dict): the previous session

        Returns:
        datetime.timedetla: the time difference between the sessions
        """
        last_end = datetime.datetime.fromisoformat(last_session.get('session_end'))
        new_start = datetime.datetime.fromisoformat(session_json.get('session_start'))
        return new_start - last_end

    def update_session_qc(self, session_qc: list[dict], metrics: dict, flags: set, subject: Subject) -> list[dict]:
        """
        Update the sessions quality control dataframe with session data

        Parameters:
        session_qc (list[dict]): the list of rows to be updated
        metrics (dict): the computed metrics for the current session
        flags (set): the raised flags for the current session
        subject (Subject): the subject the session belongs to

        Returns:
        list[dict]: the session_qc list with a row added for the current session
        """
        new_row = metrics.copy()
        new_row.pop('signal_quality', None)
        new_row['participant_id'] = subject.identifier
        new_row['flags'] = ', '.join(flags)

        session_qc.append(new_row)

        return session_qc

    def update_subject_qc(self, subject_qc: list[dict], subject_flags: set, n_sessions: int, n_sessions_flagged: int, subject: Subject) -> list[dict]:
        """
        Update the subjects quality control DataFrame with data for the current subject

        Parameters:
        subject_qc (list[dict]): the list to be updated
        subject_flags (set): all flags raised for the subject
        n_sessions (int): the total number of sessions for the subject
        n_sessions_flagged (int): the number of sessions that were flagged for this subject
        subject (Subject): the current subject

        Returns:
        list[dict]: the subject_qc list with an item added for the current subject
        """
        new_row = dict()
        new_row['participant_id'] = subject.identifier
        new_row['n_sessions_flagged'] = n_sessions_flagged
        new_row['total_sessions'] = n_sessions
        new_row['fraction_flagged'] = round(n_sessions_flagged / n_sessions, 2)
        new_row['flags'] = ', '.join(subject_flags)

        subject_qc.append(new_row)

        return subject_qc

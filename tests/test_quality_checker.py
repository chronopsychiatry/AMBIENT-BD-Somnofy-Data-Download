import json
import datetime

from ambient_bd_downloader.download.quality_checker import QualityChecker
from ambient_bd_downloader.sf_api.dom import Subject

def _read_test_session_json():
    test_session_json = './tests/data/2024-12-25_RkdSRhgMGQ8XFQAA_raw.json'
    with open(test_session_json, 'r') as f:
        return json.load(f)

class TestQualityChecker():

    qc = QualityChecker()
    
    def test_get_metrics(self):
        session = _read_test_session_json()['data']
        metrics = self.qc.get_metrics(session, session)

        assert metrics['id'] == session['id']
        assert metrics['distance'] == session['distance_during_sleep_mean']

    def test_get_flags(self):
        metrics = {
            'id': 'session_id',
            'session_start': "2024-12-25T15:23:20.302000+00:00",
            'session_end': "2024-12-25T16:02:51.053000+00:00",
            'distance': 200,
            'signal_quality': [1, 1, 1, 1, 2, 2],
            'frac_no_presence': 0.1,
            'frac_awake': 0.15,
            'sleep_onset_latency': datetime.timedelta(seconds=120),
            'time_to_previous_session': datetime.timedelta(minutes=20)
        }

        flags = self.qc.get_flags(metrics)

        assert flags == ['distance', 'signal_quality']

    def test_get_session_separation(self):
        session = _read_test_session_json()['data']
        last_session = session.copy()
        last_session['session_end'] = "2024-12-25T14:23:20.302000+00:00"
        sep = self.qc.get_session_separation(session, last_session)

        assert sep == datetime.timedelta(hours=1)

    def test_update_session_qc(self):
        session_qc = []
        metrics = {
            'id': 'session_id',
            'session_start': "2024-12-25T15:23:20.302000+00:00",
            'session_end': "2024-12-25T16:02:51.053000+00:00",
            'distance': 200,
            'signal_quality': [1, 1, 1, 1, 2, 2],
            'frac_no_presence': 0.1,
            'frac_awake': 0.15,
            'sleep_onset_latency': datetime.timedelta(seconds=120),
            'time_to_previous_session': datetime.timedelta(minutes=20)
        }
        flags = ['distance', 'signal_quality']
        subject = Subject({'id': '1',
                           'identifier': 'subject1',
                           'device': 'VTFAKE',
                           'created_at': '2023-01-01T00:00:00'
                           })

        session_qc = self.qc.update_session_qc(session_qc, metrics, flags, subject)
        assert len(session_qc) == 1
        assert session_qc[0]['participant_id'] == 'subject1'

        session_qc = self.qc.update_session_qc(session_qc, metrics, flags, subject)
        assert len(session_qc) == 2
        assert session_qc[0] == session_qc[1]

    def test_subject_qc(self):
        subject_qc = []
        subject_flags = set(['distance', 'split_session'])
        n_sessions = 4
        n_sessions_flagged = 2
        subject = Subject({'id': '1',
                           'identifier': 'subject1',
                           'device': 'VTFAKE',
                           'created_at': '2023-01-01T00:00:00'
                           })
        subject_qc = self.qc.update_subject_qc(subject_qc, subject_flags, n_sessions, n_sessions_flagged, subject)
        assert len(subject_qc) == 1
        assert subject_qc[0]['fraction_flagged'] == 0.5

        subject_qc = self.qc.update_subject_qc(subject_qc, subject_flags, n_sessions, n_sessions_flagged, subject)
        assert len(subject_qc) == 2
        assert subject_qc[0] == subject_qc[1]

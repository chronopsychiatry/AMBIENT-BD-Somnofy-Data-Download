from unittest.mock import patch, MagicMock
from ambient_bd_downloader.sf_api.somnofy import Somnofy
from pathlib import Path


class MockProperties:
    def __init__(self, credentials, credentials_file, zone_name):
        self.credentials = credentials
        self.credentials_file = credentials_file
        self.zone_name = zone_name

    @staticmethod
    def load_credentials(credentials_file):
        return {
            'client-id': 'cid',
            'client-secret': 'csecret',
            'username': 'uname',
            'password': 'pw'
        }


class TestSomnofy:
    API_ENDPOINT = 'https://api.health.somnofy.com/api/v1'

    @patch('ambient_bd_downloader.sf_api.somnofy.requests.post')
    @patch('ambient_bd_downloader.sf_api.somnofy.Somnofy.get_zone_id', return_value=1)
    def test_init(self, mock_requests_post, mock_get_zone_id):
        properties = MockProperties(credentials={'client-id': 'test_client_id', 'client-secret': 'test_client_secret',
                                                 'username': 'test_username', 'password': 'test_password'},
                                    credentials_file=Path('/path/to/credentials_file.txt'),
                                    zone_name='test_zone')
        somnofy = Somnofy(properties)

        assert somnofy.subjects_url == self.API_ENDPOINT + '/subjects'
        assert somnofy.sessions_url == self.API_ENDPOINT + '/sessions'
        assert somnofy.reports_url == self.API_ENDPOINT + '/reports'
        assert somnofy.zones_url == self.API_ENDPOINT + '/zones'
        assert somnofy.date_start == '2023-08-01T00:00:00Z'
        assert somnofy.date_end is not None
        assert somnofy.LIMIT == 300

    @patch('ambient_bd_downloader.sf_api.somnofy.Somnofy.get_access_token')
    def test_get_headers(self, mock_get_access_token):
        mock_get_access_token.return_value = 'token123'
        properties = MockProperties(credentials={'client-id': 'cid', 'client-secret': 'csecret',
                                                 'username': 'uname', 'password': 'pw'},
                                    credentials_file=Path('/path/to/credentials_file.txt'),
                                    zone_name='test_zone')
        somnofy = Somnofy.__new__(Somnofy)  # bypass __init__
        headers = Somnofy.get_headers(somnofy, properties)
        assert headers['accept'] == 'application/json'
        assert headers['Authorization'] == 'Bearer token123'
        mock_get_access_token.assert_called_once_with(
            client_id='cid',
            client_secret='csecret',
            username='uname',
            password='pw'
        )

    @patch('requests.post')
    def test_get_access_token(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {'access_token': 'abc123'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        somnofy = Somnofy.__new__(Somnofy)
        somnofy.token_endpoint = 'https://auth.somnofy.com/oauth2/token'
        token = Somnofy.get_access_token(
            somnofy,
            client_id='cid',
            client_secret='csecret',
            username='uname',
            password='pw'
        )
        assert token == 'abc123'
        mock_post.assert_called_once_with(
            'https://auth.somnofy.com/oauth2/token',
            data={
                "grant_type": "password",
                "username": "uname",
                "password": "pw",
            },
            auth=('cid', 'csecret'),
        )
        mock_response.raise_for_status.assert_called_once()

    @patch('ambient_bd_downloader.sf_api.somnofy.requests.get')
    @patch('ambient_bd_downloader.sf_api.somnofy.requests.post')
    def test_select_subjects(self, mock_requests_post, mock_requests_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {'id': '1', 'identifier': 'subject1', 'created_at': '2023-01-01T00:00:00',
                 'devices': {'data': [{'name': 'VT001'}]}, 'device': 'VT001'},
                {'id': '2', 'identifier': 'subject2', 'created_at': '2023-01-02T00:00:00',
                 'devices': {'data': [{'name': 'VT002'}]}, 'device': 'VT002'},
                {'id': '3', 'identifier': 'subject3', 'created_at': '2023-01-03T00:00:00',
                 'devices': {'data': [{'name': 'VT003'}]}, 'device': 'VT003'}
            ]
        }
        mock_requests_get.return_value = mock_response

        properties = MockProperties(credentials={'client-id': 'test_client_id', 'client-secret': 'test_client_secret',
                                                 'username': 'test_username', 'password': 'test_password'},
                                    credentials_file=Path('/path/to/credentials_file.txt'),
                                    zone_name='test_zone')
        somnofy = Somnofy(properties)
        somnofy.get_zone_id = MagicMock(return_value='zone123')
        somnofy.headers = {}

        subjects = somnofy.select_subjects(zone_name='test_zone', subject_name='subject2', device_name='*')

        assert len(subjects) == 1
        assert subjects[0].identifier == 'subject2'

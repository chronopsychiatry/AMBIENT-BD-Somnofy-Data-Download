import pytest
from unittest.mock import patch, MagicMock, mock_open
from ambient_bd_downloader.sf_api.somnofy import Somnofy
from ambient_bd_downloader.sf_api.dom import Subject
from pathlib import Path


class MockProperties:
    def __init__(self, client_id=None, client_id_file=None, credentials=None, credentials_file=None, zone_name=None):
        self.client_id = client_id or None
        self.client_id_file = client_id_file or None
        self.credentials = credentials or None
        self.credentials_file = credentials_file or None
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

    @patch('ambient_bd_downloader.sf_api.somnofy.Somnofy.set_auth', return_value=MagicMock())
    @patch('ambient_bd_downloader.sf_api.somnofy.Somnofy.get_zone_id', return_value=1)
    def test_init_with_client_id(self, mock_get_zone_id, mock_set_auth):
        properties = MockProperties(client_id='test_client_id',
                                client_id_file=Path('/path/to/client_id_file.txt'),
                                zone_name='test_zone')

        somnofy = Somnofy(properties)

        assert somnofy.client_id == 'test_client_id'
        assert somnofy.token_file == Path('/path/to/token.txt')
        assert somnofy.subjects_url == self.API_ENDPOINT + '/subjects'
        assert somnofy.sessions_url == self.API_ENDPOINT + '/sessions'
        assert somnofy.reports_url == self.API_ENDPOINT + '/reports'
        assert somnofy.zones_url == self.API_ENDPOINT + '/zones'
        assert somnofy.date_start == '2023-08-01T00:00:00Z'
        assert somnofy.date_end is not None
        assert somnofy.LIMIT == 300
        mock_set_auth.assert_called_once_with('test_client_id')

    @patch('ambient_bd_downloader.sf_api.somnofy.requests.post')
    @patch('ambient_bd_downloader.sf_api.somnofy.Somnofy.get_zone_id', return_value=1)
    def test_init_with_credentials(self, mock_zone_id, mock_requests_post):
        properties = MockProperties(credentials = {
            'client-id': 'test_client_id',
            'client-secret': 'test_client_secret',
            'username': 'test_username',
            'password': 'test_password'
        },
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

    def test_init_no_id(self):
        properties = MockProperties(client_id_file='/path/to/client_id_file', zone_name='test_zone')
        with pytest.raises(ValueError, match='client_id or credentials must be provided'):
            Somnofy(properties)

    @patch('ambient_bd_downloader.sf_api.somnofy.Somnofy.get_access_token')
    def test_get_headers(self, mock_get_access_token):
        mock_get_access_token.return_value = 'token123'
        properties = MockProperties(credentials={
            'client-id': 'cid',
            'client-secret': 'csecret',
            'username': 'uname',
            'password': 'pw'
        },
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
        somnofy.token_url = 'https://auth.somnofy.com/oauth2/token'
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

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.open', new_callable=mock_open, read_data='test_token')
    @patch('ambient_bd_downloader.sf_api.somnofy.OAuth2Session')
    @patch('ambient_bd_downloader.sf_api.somnofy.Somnofy.get_zone_id', return_value=1)
    def test_set_auth_with_valid_token(self, mock_get_zone_id, mock_oauth2session, mock_open, mock_exists):
        properties = MockProperties(client_id='test_client_id',
                                    client_id_file=Path('/path/to/client_id_file.txt'),
                                    zone_name='test_zone')
        mock_oauth2session.return_value.get.return_value.status_code = 200
        somnofy = Somnofy(properties)
        oauth = somnofy.set_auth('test_client_id')

        mock_open.assert_called_with('r')
        mock_oauth2session.assert_called_with('test_client_id', token={'access_token': 'test_token',
                                                                       'token_type': 'Bearer'})
        assert oauth is not None

    @patch('ambient_bd_downloader.sf_api.somnofy.webbrowser.open')
    @patch('ambient_bd_downloader.sf_api.somnofy.input', return_value='https://example.com/callback?code=test_code')
    @patch('ambient_bd_downloader.sf_api.somnofy.OAuth2Session')
    @patch('pathlib.Path.open', new_callable=mock_open)
    @patch('ambient_bd_downloader.sf_api.somnofy.Somnofy.get_zone_id', return_value=1)
    def test_set_auth_new_authorization(self, mock_get_zone_id, mock_open,
                                        mock_oauth2session, mock_input, mock_webbrowser):
        properties = MockProperties(client_id='test_client_id',
                                    client_id_file='/path/to/client_id_file',
                                    zone_name='test_zone')
        mock_oauth2session.return_value.authorization_url.return_value = ('https://auth.somnofy.com/oauth2/authorize',
                                                                          'test_state')
        mock_oauth2session.return_value.fetch_token.return_value = {'access_token': 'new_test_token'}
        somnofy = Somnofy(properties)
        oauth = somnofy.set_auth('test_client_id')

        mock_webbrowser.assert_called_with('https://auth.somnofy.com/oauth2/authorize')
        mock_input.assert_called_with('Enter the full URL: ')
        mock_open.assert_called_with('w')
        mock_open().write.assert_called_with('new_test_token')
        assert oauth is not None

    @patch('ambient_bd_downloader.sf_api.somnofy.Somnofy.set_auth', return_value=MagicMock())
    @patch('ambient_bd_downloader.sf_api.somnofy.Somnofy.get_zone_id', return_value=1)
    @patch('ambient_bd_downloader.sf_api.somnofy.Somnofy.get_subjects', return_value=[
        Subject({'id': '1', 'identifier': 'subject1', 'created_at': '2023-01-01T00:00:00',
                 'devices': {'data': [{'name': 'VT001'}]}}),
        Subject({'id': '2', 'identifier': 'subject2', 'created_at': '2023-01-02T00:00:00',
                 'devices': {'data': [{'name': 'VT002'}]}}),
        Subject({'id': '3', 'identifier': 'Test subject3', 'created_at': '2023-01-03T00:00:00',
                 'devices': {'data': [{'name': 'VT003'}]}})
    ])
    def test_select_subjects(self, mock_get_subjects, mock_get_zone_id, mock_set_auth):
        properties = MockProperties(client_id='test_client_id',
                                    client_id_file='/path/to/client_id_file',
                                    zone_name='test_zone')
        somnofy = Somnofy(properties)

        subjects = somnofy.select_subjects(zone_name='test_zone', subject_name='subject2', device_name='*')
        assert len(subjects) == 1
        assert subjects[0].identifier == 'subject2'

        subjects = somnofy.select_subjects(zone_name='test_zone', exclude_subjects='Test')
        assert len(subjects) == 2

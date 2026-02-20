import datetime
from requests_oauthlib import OAuth2Session
from os import urandom
import base64
import hashlib
import webbrowser
import logging
from pathlib import Path

from ambient_bd_downloader.sf_api.dom import Subject, Session
from ambient_bd_downloader.properties.properties import Properties

# API
# https://api.health.somnofy.com/api/v1/docs#/


class Somnofy:
    API_ENDPOINT = 'https://api.health.somnofy.com/api/v1'

    def __init__(self, properties: Properties):
        self._logger = logging.getLogger('Somnofy')
        self.client_id = properties.client_id
        if not self.client_id:
            raise ValueError('Client ID must be provided')
        self.token_file = Path(properties.client_id_file).parent / 'token.txt'
        self.token_url = 'https://auth.somnofy.com/oauth2/token'
        self.subjects_url = self.API_ENDPOINT + '/subjects'
        self.sessions_url = self.API_ENDPOINT + '/sessions'
        self.reports_url = self.API_ENDPOINT + '/reports'
        self.zones_url = self.API_ENDPOINT + '/zones'
        self.devices_url = self.API_ENDPOINT + '/devices'
        self.date_start = '2023-08-01T00:00:00Z'
        self.date_end = datetime.datetime.now().isoformat()
        self.LIMIT = 300
        self.oauth = self.set_auth(properties.client_id)

    def set_auth(self, client_id: str):
        if (oauth := self.auth_with_old_token(client_id)):
            return oauth
        else:
            return self.auth_with_new_token(client_id)

    def auth_with_old_token(self, client_id: str) -> OAuth2Session | None:
        if self.token_file.exists():
            with self.token_file.open('r') as f:
                token = f.read()
            oauth = OAuth2Session(client_id, token={'access_token': token, 'token_type': 'Bearer'})
            r = oauth.get(self.subjects_url)  # Test if the token is still valid
            if r.status_code == 200:
                self._logger.info('Accessing API with stored token.')
                return oauth
            else:
                self.token_file.unlink(missing_ok=True)
                print('Token is no longer valid. Please reauthorize.')
                return None

    def auth_with_new_token(self, client_id: str) -> OAuth2Session:
        code_verifier = base64.urlsafe_b64encode(urandom(40)).rstrip(b'=').decode('utf-8')
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8'))
                                                  .digest()).rstrip(b'=').decode('utf-8')

        oauth = OAuth2Session(client_id, redirect_uri='https://api.health.somnofy.com/oauth2-redirect')
        authorization_url, state = oauth.authorization_url('https://auth.somnofy.com/oauth2/authorize',
                                                           code_challenge=code_challenge,
                                                           code_challenge_method='S256')
        print('Please authorize access in your web browser.')
        webbrowser.open(authorization_url)
        authorization_response = input('Enter the full URL: ')

        token = oauth.fetch_token(self.token_url,
                                  authorization_response=authorization_response,
                                  include_client_id=True,
                                  code_verifier=code_verifier)

        with self.token_file.open('w') as f:
            f.write(token['access_token'])
        return oauth

    def get_subjects(self, zone_name: str) -> list[Subject]:
        zone_id = self.get_zone_id(zone_name)
        r = self.oauth.get(self.subjects_url, params={'path': zone_id, 'embed': 'devices'})
        json_list = r.json()["data"]
        return [Subject(subject_data) for subject_data in json_list]

    def select_subjects(self, zone_name: str, subject_name: str = '*', device_name: str = '*') -> list[Subject]:
        subjects = self.get_subjects(zone_name)
        selected_subjects = []
        for subject in subjects:
            if ((subject.identifier in subject_name or '*' in subject_name)
                    and (subject.device in device_name or '*' in device_name)
                and ('Test' not in subject.identifier)):
                selected_subjects.append(subject)
        return selected_subjects

    def _make_sessions_params(self, limit: int = None,
                              from_date: datetime.date | str = None,
                              to_date: datetime.date | str = None) -> dict:
        if limit is None:
            limit = self.LIMIT
        if from_date is None:
            from_date = self.date_start
        if to_date is None:
            to_date = self.date_end

        # if data is passed to params as an object, the API does not take time part of the timestamp
        # and all sessions from the start date are turned
        # if start_time is explicitly converted to string than API behaves as expected
        if isinstance(from_date, datetime.datetime):
            from_date = from_date.isoformat()
        if isinstance(to_date, datetime.datetime):
            to_date = to_date.isoformat()

        return {
            'limit': limit,
            'from': from_date,
            'to': to_date,
            'sort': 'asc'
        }

    def get_all_sessions_for_subject(self,
                                     subject_id: str,
                                     from_date: datetime.date | str = None,
                                     to_date: datetime.date | str = None) -> list[Session]:
        params = self._make_sessions_params(from_date=from_date, to_date=to_date)
        params['subject_id'] = subject_id
        params['type'] = 'vitalthings-somnofy-sm100-session'
        are_more = True
        sessions = []
        while are_more:
            r = self.oauth.get(self.sessions_url, params=params)
            json_list = r.json()['data']
            sessions += [Session(data) for data in json_list]
            are_more = len(json_list) == self.LIMIT
            if are_more:
                params['from'] = datetime.datetime.fromisoformat(json_list[-1]['session_start'])
        return sessions

    def get_session_json(self, session_id: str) -> dict:
        url = f'{self.sessions_url}/{session_id}'
        params = {'include_epoch_data': True}
        r = self.oauth.get(url, params=params)
        return r.json()

    def get_session_report(self, subject_id: str, date: str) -> dict:
        params = {'subjects': subject_id, 'report_date': date}
        r = self.oauth.get(self.reports_url, params=params)
        return r.json()

    def get_zone_id(self, zone_name: str) -> str:
        r = self.oauth.get(self.zones_url)
        available_zones = {zone['name']: zone['id'] for zone in r.json()['data']}
        if zone_name not in available_zones:
            raise ValueError(f'Zone "{zone_name}" not found. Available zones: {list(available_zones.keys())}')
        return available_zones[zone_name]

    def get_all_zones(self) -> list[str]:
        r = self.oauth.get(self.zones_url)
        return [zone['name'] for zone in r.json()['data']]

    def has_zone_access(self, zone_name: str) -> bool:
        zone_id = self.get_zone_id(zone_name)
        r = self.oauth.get(self.subjects_url, params={'path': zone_id})
        return True if r.status_code == 200 else False

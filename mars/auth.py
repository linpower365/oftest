import requests
import config as cfg

URL = cfg.API_BASE_URL
GET_HEADER = {'Accept': 'application/json'}
POST_HEADER = {'Content-Type': 'application/json'}


class Authentication():
    def __init__(self):
        self._cookies = None

    def login(self):
        payload = {
            "user_name": "karaf",
            "password": "karaf"
        }

        if not self._cookies:
            response = requests.post(
                URL+"useraccount/v1/login", json=payload, headers=POST_HEADER)

            self._cookies = dict(
                marsGSessionId=response.headers['MARS_G_SESSION_ID'])
            response = requests.get(URL+"useraccount/v1/info",
                                    cookies=self._cookies, headers=GET_HEADER)

        return self

    def get_cookies(self):
        return self._cookies

"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test NTP Server RestAPI.
"""


import oftest.base_tests as base_tests
import config as test_config
import requests

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}


class NTPServerTest(base_tests.SimpleDataPlane):
    """
    Test NTP Server
        - GET /ntpserver/v1
        - GET /ntpserver/v1/<device_id>
        - PUT /ntpserver/v1
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def runTest(self):

        # Query NTP Server setting
        response = requests.get(URL+'ntpserver/v1', headers=GET_HEADER)
        assert response.status_code == 200, 'Query NTP setting FAIL!'

        # get a device_id
        response = requests.get(URL+"v1/devices", headers=GET_HEADER)
        assert response.status_code == 200, 'Query devices is FAIL!'
        assert len(response.json()['devices']) > 0, 'Test NTP Server RestAPI need at least one device'
        device_id = response.json()['devices'][0]['id']

        # get NTP setting on a device
        response = requests.get(URL+'ntpserver/v1/' + device_id, headers=GET_HEADER)
        assert response.status_code == 200, 'Query NTP setting on device_id = '+device_id+" is FAIL!"

        # put NTP setting
        payload = {
            "enabled": True,
            "ntp_servers": [
                "192.168.2.1"
            ]
        }
        response = requests.put(URL+'ntpserver/v1', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Put NTP setting FAIL!'

        # Check if put NTP setting successfully
        response = requests.get(URL+'ntpserver/v1', headers=GET_HEADER)
        assert response.status_code == 200, 'Query NTP setting FAIL!'
        assert response.json()['enabled'] == True, 'Put NTP setting FAIL!'

        # get NTP setting on a device
        response = requests.get(URL+'ntpserver/v1/' + device_id, headers=GET_HEADER)
        assert response.status_code == 200, 'Query NTP setting on device_id = '+device_id+' is FAIL!'

        # clear NTP settings
        payload = {
            "enabled": False,
            "ntp_servers": []
        }
        response = requests.put(URL+'ntpserver/v1', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Put NTP setting FAIL!'
        
        
        # Check if NTP Server setting successfully
        response = requests.get(URL+'ntpserver/v1', headers=GET_HEADER)
        assert response.status_code == 200, 'Query NTP setting FAIL!'
        assert response.json()['enabled'] == False, 'Clear NTP server setting is FAIL!'

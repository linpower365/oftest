"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test Storm Controls RestAPI.
"""


import oftest.base_tests as base_tests
import config as test_config
import requests

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}


class StormControlsTest(base_tests.SimpleDataPlane):
    """
    Test Storm Controls
        - GET /storm/v1
        - POST /storm/v1/<device_id>
        - GET /storm/v1/<device_id>
        - DELETE /storm/v1/<device_id>
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def runTest(self):

        # query all storm data
        response = requests.get(URL+"storm/v1", headers=GET_HEADER)
        assert response.status_code == 200, 'Query all storm settings is FAIL'

        # get a device_id
        response = requests.get(URL+"v1/devices", headers=GET_HEADER)
        assert response.status_code == 200, 'Query devices is FAIL!!'
        assert len(response.json()[
                   'devices']) > 0, 'Test Storm RestAPI need at least one device'
        device_id = response.json()['devices'][0]['id']

        # add storm setting on a device
        payload = {
            "unicast": 500,
            "unicast_enabled": True,
            "bcast": 500,
            "bcast_enabled": True,
            "mcast": 500,
            "mcast_enabled": True
        }
        response = requests.post(
            URL+'storm/v1/'+device_id, json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add storm setting on device_id = '+device_id+'is FAIL'

        # check if add storm setting success
        response = requests.get(URL+'storm/v1/'+device_id, headers=GET_HEADER)
        assert response.status_code == 200, 'Query storm setting on device_id = ' + \
            device_id+'is FAIL'
        result = response.json()
        assert payload == result, 'Add storm setting on device_id = '+device_id+'is FAIL'

        # delete storm setting on a device
        response = requests.delete(
            URL+'storm/v1/'+device_id, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete storm setting on device_id = ' + \
            device_id+'is FAIL'

        # check if delete success
        response = requests.get(URL+'storm/v1/'+device_id, headers=GET_HEADER)
        assert response.status_code == 200, 'Query storm setting on device_id = ' + \
            device_id+'is FAIL'
        result = response.json()
        assert result == {}, 'Delete storm setting on device_id = '+device_id+'is FAIL'

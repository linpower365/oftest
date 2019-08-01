"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test QoS RestAPI.
"""


import oftest.base_tests as base_tests
import config as test_config
import requests
import time, random

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}


class QosCosTest(base_tests.SimpleDataPlane):
    """
    Test Qos Cos API.
        - GET qos/cos/v1
        - GET qos/cos/v1/<queue_no>
        - PUT qos/cos/v1
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def runTest(self):

        # Query all cos data
        response = requests.get(URL+'qos/cos/v1', headers=GET_HEADER)
        assert response.status_code == 200, 'Query all cos data FAIL'

        # Query one cos data
        qno = str(random.randrange(0,8,1))
        response = requests.get(URL+'qos/cos/v1/'+qno, headers=GET_HEADER)
        assert response.status_code == 200, 'Query queue '+qno+ ' FAIL'

        # Update one cos config
        payload = {
            "queue": qno,
            "dscp": [
                3,5,7
            ]
        }
        response = requests.put(URL+'qos/cos/v1', headers=POST_HEADER, json=payload)
        assert response.status_code == 200, 'Update cos config on queue '+qno+' FAIL'

        # Check if update successfully
        response = requests.get(URL+'qos/cos/v1/'+qno, headers=GET_HEADER)
        assert response.status_code == 200, 'Query cos data on queue '+qno+' FAIL'
        dscp = response.json()['dscp']
        assert (3 in dscp) and (5 in dscp) and (7 in dscp), 'Update cos config on queue '+qno+ ' FAIL'


class QosEcnTest(base_tests.SimpleDataPlane):
    """
    Test Qos ECN API.
        GET qos/ecn/v1
        GET qos/ecn/v1/<queue_no>
        PUT qos/ecn/v1
        DELETE qos/ecn/v1/<queue_no>
    """
    def runTest(self):

        # Query all ECN data
        response = requests.get(URL+'qos/ecn/v1', headers=GET_HEADER)
        assert response.status_code == 200, 'Query all ECN data FAIL'

        # Query one ECN data
        qno = str(random.randrange(0,8,1))
        response = requests.get(URL+'qos/ecn/v1/'+qno, headers=GET_HEADER)
        assert response.status_code == 200, 'Query ECN data for queue '+qno+ ' FAIL'

        # Add ECN data
        threshold = random.randrange(1,100)
        payload = {
            "queue": qno,
            "ecn_threshold": threshold
        }
        response = requests.put(URL+'qos/ecn/v1', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add ECN data for queue '+qno+' FAIL'

        # Check if add successfully
        response = requests.get(URL+'qos/ecn/v1/'+qno, headers=GET_HEADER)
        assert response.status_code == 200, 'Query ECN data for queue '+qno+' FAIL'
        assert response.json()['queue'] == int(qno) , 'Add ECN data for queue '+qno+' FAIL'
        assert response.json()['ecn_threshold'] == int(threshold) , 'Add ECN data for queue '+qno+' FAIL'

        # Delete ecn data
        response = requests.delete(URL+'qos/ecn/v1/'+qno, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete ECN for queue '+qno+' FAIL'

        # Check if delete successfully
        response = requests.get(URL+'qos/ecn/v1', headers=GET_HEADER)
        assert response.status_code == 200, 'Query all ECN data FAIL'
        removed = True
        for item in response.json()['ecn']:
            if item['queue'] == int(qno):
                remove = False
                break
        assert removed, 'Delete ECN for queue '+qno+ ' FAIL'

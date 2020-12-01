"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test QoS RestAPI.
"""


import oftest.base_tests as base_tests
import config as test_config
import requests
import time
import random
import auth

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
# GET_HEADER = {'Authorization': AUTH_TOKEN}
# POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}
GET_HEADER = {'Accept': 'application/json'}
POST_HEADER = {'Content-Type': 'application/json'}
COOKIES = auth.Authentication().login().get_cookies()


class CoS(base_tests.SimpleDataPlane):
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
        response = requests.get(
            URL+'qos/cos/v1', cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query all cos data FAIL'

        # Query one cos data
        qno = str(random.randrange(0, 8, 1))
        response = requests.get(URL+'qos/cos/v1/'+qno,
                                cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query queue '+qno + ' FAIL'

        # Update one cos config
        payload = {
            "queue": qno,
            "dscp": [
                3, 5, 7
            ]
        }
        response = requests.put(
            URL+'qos/cos/v1', cookies=COOKIES, headers=POST_HEADER, json=payload)
        assert response.status_code == 200, 'Update cos config on queue '+qno+' FAIL'

        # Check if update successfully
        response = requests.get(URL+'qos/cos/v1/'+qno,
                                cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query cos data on queue '+qno+' FAIL'
        dscp = response.json()['dscp']
        assert (3 in dscp) and (5 in dscp) and (
            7 in dscp), 'Update cos config on queue '+qno + ' FAIL'


class ECN(base_tests.SimpleDataPlane):
    """
    Test Qos ECN API.
        - GET qos/ecn/v1
        - GET qos/ecn/v1/<queue_no>
        - PUT qos/ecn/v1
        - DELETE qos/ecn/v1/<queue_no>
    """

    def runTest(self):

        # Query all ECN data
        response = requests.get(
            URL+'qos/ecn/v1', cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query all ECN data FAIL'

        # Query one ECN data
        qno = str(random.randrange(0, 8, 1))
        response = requests.get(URL+'qos/ecn/v1/'+qno,
                                cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query ECN data for queue '+qno + ' FAIL'

        # Add ECN data
        threshold = random.randrange(1, 100)
        payload = {
            "queue": qno,
            "ecn_threshold": threshold
        }
        response = requests.put(
            URL+'qos/ecn/v1', json=payload, cookies=COOKIES, headers=POST_HEADER)
        assert response.status_code == 200, 'Add ECN data for queue '+qno+' FAIL'

        # Check if add successfully
        response = requests.get(URL+'qos/ecn/v1/'+qno,
                                cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query ECN data for queue '+qno+' FAIL'
        assert response.json()['queue'] == int(
            qno), 'Add ECN data for queue '+qno+' FAIL'
        assert response.json()['ecn_threshold'] == int(
            threshold), 'Add ECN data for queue '+qno+' FAIL'

        # Delete ecn data
        response = requests.delete(
            URL+'qos/ecn/v1/'+qno, cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete ECN for queue '+qno+' FAIL'

        # Check if delete successfully
        response = requests.get(
            URL+'qos/ecn/v1', cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query all ECN data FAIL'
        removed = True
        for item in response.json()['ecn']:
            if item['queue'] == int(qno):
                remove = False
                break
        assert removed, 'Delete ECN for queue '+qno + ' FAIL'


class PFC(base_tests.SimpleDataPlane):
    """
    Test Qos PFC API.
        - GET qos/pfc/v1/<device_id>
        - POST qos/pfc/v1/<device_id>
        - DELETE qos/pfc/v1/<device_id>/<port_no>
    """

    def runTest(self):

        # Query a device
        response = requests.get(
            URL+'v1/devices', cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query devices FAIL'
        assert len(response.json()[
                   'devices']) > 0, 'Test PFC RestAPI need at least one device'
        device_id = response.json()['devices'][0]['id']

        # Query a PFC data on a device
        response = requests.get(
            URL+'qos/pfc/v1/'+device_id, cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query PFC data on a device: '+device_id+' FAIL'

        # Add PFC on a device at port_no 1
        payload = {
            "queues": [
                2, 3, 4
            ],
            "port": 1
        }
        response = requests.post(
            URL+'qos/pfc/v1/'+device_id, cookies=COOKIES, headers=POST_HEADER, json=payload)
        assert response.status_code == 200, 'Add PFC on device at prot_no=1 FAIL, device_id='+device_id

        # Check if PFC add successfully
        response = requests.get(
            URL+'qos/pfc/v1/'+device_id, cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query PFC data on a device: '+device_id+' FAIL'
        exist = False
        for item in response.json()['pfcs']:
            if item['port'] == '1' and item['queues'] == [2, 3, 4]:
                exist = True
                break
        assert exist, 'Add PFC on device_id:'+device_id+' FAIL'

        # Delete PFC on a device at port_no 1
        response = requests.delete(
            URL+'qos/pfc/v1/'+device_id+'/1', cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete PFC on device_id:'+device_id+' FAIL'

        # Check if PFC delete successfully
        response = requests.get(
            URL+'qos/pfc/v1/'+device_id, cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query PFC data on a device: '+device_id+' FAIL'
        removed = True
        for item in response.json()['pfcs']:
            if item['port'] == '1':
                removed = False
                break
        assert removed, 'Delete PFC on device_id:'+device_id+' FAIL'


class Scheduler(base_tests.SimpleDataPlane):
    """
    Test Qos Scheduler API.
        - GET qos/scheduler/v1
        - PUT qos/scheduler/v1
    """

    def runTest(self):

        # Query QoS Scheduler
        response = requests.get(URL+'qos/scheduler/v1',
                                cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query QoS Scheduler FAIL'

        # Update QoS Scheduler
        payload = {
            "name": "bandwidth",
            "queue_weight": [
                1, 2, 3, 4, 5, 6, 7, 8
            ]
        }
        response = requests.put(URL+'qos/scheduler/v1',
                                cookies=COOKIES, headers=POST_HEADER, json=payload)
        assert response.status_code == 200, 'Update QoS Scheduler FAIL'

        # Check if Update successfully
        response = requests.get(URL+'qos/scheduler/v1',
                                cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query QoS Scheduler FAIL'
        assert len(response.json()['scheduler']
                   ) > 0, 'Query QoS Scheduler FAIL'
        for item in response.json()['scheduler']:
            if item['name'] == 'bandwidth':
                assert item['queue_weight'] == [1, 2, 3, 4, 5, 6, 7, 8]
                break


class Ratelimit(base_tests.SimpleDataPlane):
    """
    Test Qos Ratelimit API.
        - GET qos/ratelimit/v1
        - GET qos/ratelimit/v1/<queue_no>
        - POST qos/ratelimit/v1
        - DELETE qos/ratelimit/v1/<queue_no>
    """

    def runTest(self):

        # Query all Ratelimit data
        response = requests.get(URL+'qos/ratelimit/v1',
                                cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query all Ratelimit data FAIL'

        # Set a ratelimit on queue
        qno = random.randrange(0, 8, 1)
        payload = {
            "queue": qno,
            "min_rate": 20,
            "max_rate": 80
        }
        response = requests.post(
            URL+'qos/ratelimit/v1', cookies=COOKIES, headers=POST_HEADER, json=payload)
        assert response.status_code == 200, 'Set a ratelimit on queue_no:' + \
            str(qno)+' FAIL'

        # Check if set successfully
        response = requests.get(
            URL+'qos/ratelimit/v1/'+str(qno), cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query ratelimit on queue_no:' + \
            str(qno)+' FAIL'
        assert len(response.json()
                   ) > 0, 'Set a ratelimit on queue_no:'+str(qno)+' FAIL'
        rl = response.json()
        assert rl['queue'] == qno, 'Set a ratelimit on queue_no:' + \
            str(qno)+' FAIL'
        assert rl['min_rate'] == 20 and rl['max_rate'] == 80, 'Set a ratelimit on queue_no:' + \
            str(qno)+' FAIL'

        # Delete ratelimit
        response = requests.delete(
            URL+'qos/ratelimit/v1/'+str(qno), cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete ratelimit on queue_no:' + \
            str(qno)+' FAIL'

        # Check if delete successfully
        response = requests.get(
            URL+'qos/ratelimit/v1/'+str(qno), cookies=COOKIES, headers=GET_HEADER)
        assert response.status_code == 200, 'Query ratelimit on queue_no:' + \
            str(qno)+' FAIL'
        assert len(response.json()
                   ) == 0, 'Delete ratelimit on queue_no:'+str(qno)+' FAIL'

"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test Healthy Check RestAPI.

Controller
    - CPU
    - RAM
    - Disk
    - Port
Switch
    - CPU
    - RAM
    - Disk
    - Port
Sensors
    - temp
    - psu
    - fan
"""


import oftest.base_tests as base_tests
import config as test_config
import requests

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}


class ControllerCpu(base_tests.SimpleDataPlane):
    """
    Test HealthyCheck Controller CPU Threshold RestAPI
        - GET /healthycheck/v1/controller/cpu/threshold
        - POST /healthycheck/v1/controller/cpu/threshold
        - GET /healthycheck/v1/controller/cpu/threshold/<rule_name>
        - DELETE /healthycheck/v1/controller/cpu/threshold/<rule_name>
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def runTest(self):

        # Query Controller CPU threshold
        response = requests.get(URL+'healthycheck/v1/controller/cpu/threshold', headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller CPU threshold FAIL!'

        # Add threshold for Controller CPU
        rule_name = "test_rule_name"
        payload = {
            "name": rule_name,
            "status": "enabled",
            "alert_level": 1,
            "receive_group": "group name",
            "query": [
                {
                    "util": 10,
                    "condition": "gt",
                    "continue": 180
                }
            ]
        }
        response = requests.post(URL+'healthycheck/v1/controller/cpu/threshold', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add threshold for Controller CPU  FAIL!'

        # Query Controller CPU threshold for a rule_name
        response = requests.get(URL+'healthycheck/v1/controller/cpu/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller CPU threshold for a rule_name = '+rule_name+' FAIL!'
        assert response.json() == payload, 'Add threshold for Controller CPU  FAIL!'

        # Delete Controller CPU threshold by rule_name
        response = requests.delete(URL+'healthycheck/v1/controller/cpu/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete Controller CPU threshold by rule_name = '+rule_name+' FAIL!'

        # Check if delete successfully
        response = requests.get(URL+'healthycheck/v1/controller/cpu/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller CPU threshold for a rule_name = '+rule_name+' FAIL!'
        assert response.json() == {}, 'Delete Controller CPU threshold by rule_name = '+rule_name+' FAIL!'


class ControllerRam(base_tests.SimpleDataPlane):
    """
    Test HealthyCheck Controller RAM Threshold RestAPI
        - GET /healthycheck/v1/controller/ram/threshold
        - POST /healthycheck/v1/controller/ram/threshold
        - GET /healthycheck/v1/controller/ram/threshold/<rule_name>
        - DELETE /healthycheck/v1/controller/ram/threshold/<rule_name>
    """

    def runTest(self):

        # Query Controller RAM threshold
        response = requests.get(URL+'healthycheck/v1/controller/ram/threshold', headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller RAM threshold FAIL!'

        # Add threshold for Controller RAM
        rule_name = "test_rule_name"
        payload = {
            "name": rule_name,
            "status": "enabled",
            "alert_level": 1,
            "receive_group": "group name",
            "query": [
                {
                    "used_ratio": 10,
                    "condition": "gt",
                    "continue": 180
                }
            ]
        }
        response = requests.post(URL+'healthycheck/v1/controller/ram/threshold', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add threshold for Controller RAM FAIL!'

        # Query Controller RAM threshold for a rule_name
        response = requests.get(URL+'healthycheck/v1/controller/ram/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller RAM threshold for a rule_name = '+rule_name+' FAIL!'
        assert response.json() == payload, 'Add threshold for Controller RAM FAIL!'

        # Delete Controller RAM threshold by rule_name
        response = requests.delete(URL+'healthycheck/v1/controller/ram/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete Controller RAM threshold by rule_name = '+rule_name+' FAIL!'

        # Check if delete successfully
        response = requests.get(URL+'healthycheck/v1/controller/ram/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller RAM threshold for a rule_name = '+rule_name+' FAIL!'
        assert response.json() == {}, 'Delete Controller RAM threshold by rule_name = '+rule_name+' FAIL!'


class ControllerDisk(base_tests.SimpleDataPlane):
    """
    Test HealthyCheck Controller Disk Threshold RestAPI
        - GET /healthycheck/v1/controller/disk/threshold
        - POST /healthycheck/v1/controller/disk/threshold
        - GET /healthycheck/v1/controller/disk/threshold/<rule_name>
        - DELETE /healthycheck/v1/controller/disk/threshold/<rule_name>
    """

    def runTest(self):

        # Query Controller Disk threshold
        response = requests.get(URL+'healthycheck/v1/controller/disk/threshold', headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller Disk threshold FAIL!'

        # Add threshold for Controller Disk
        rule_name = "test_rule_name"
        payload = {
            "name": rule_name,
            "status": "enabled",
            "alert_level": 1,
            "receive_group": "group name",
            "query": [
                {
                    "root_used_ratio": 10,
                    "condition": "gt",
                    "continue": 180
                }
            ]
        }
        response = requests.post(URL+'healthycheck/v1/controller/disk/threshold', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add threshold for Controller Disk FAIL!'

        # Query Controller Disk threshold for a rule_name
        response = requests.get(URL+'healthycheck/v1/controller/disk/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller Disk threshold for a rule_name = '+rule_name+' FAIL!'

        # Delete Controller Disk threshold by rule_name
        response = requests.delete(URL+'healthycheck/v1/controller/disk/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete Controller Disk threshold by rule_name = '+rule_name+' FAIL!'

        # Check if delete successfully
        response = requests.get(URL+'healthycheck/v1/controller/disk/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller disk threshold for a rule_name = '+rule_name+' FAIL!'
        assert response.json() == {}, 'Delete Controller Disk threshold by rule_name = '+rule_name+' FAIL!'


class ControllerPort(base_tests.SimpleDataPlane):
    """
    Test HealthyCheck Controller Port Threshold RestAPI
        - GET /healthycheck/v1/controller/port/threshold
        - POST /healthycheck/v1/controller/port/threshold
        - GET /healthycheck/v1/controller/port/threshold/<rule_name>
        - DELETE /healthycheck/v1/controller/port/threshold/<rule_name>
    """

    def runTest(self):

        # Query Controller Port threshold
        response = requests.get(URL+'healthycheck/v1/controller/port/threshold', headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller Port threshold FAIL!'

        # Add threshold for Controller Port
        rule_name = "test_rule_name"
        payload = {
            "name": rule_name,
            "status": "enabled",
            "alert_level": 1,
            "receive_group": "group name",
            "query_rx": [
                {
                "rx_util": 10,
                "condition": "gt",
                "continue": 180
                }
            ],
            "query_tx": [
                {
                "tx_util": 10,
                "condition": "gt",
                "continue": 180
                }
            ]
        }
        response = requests.post(URL+'healthycheck/v1/controller/port/threshold', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add threshold for Controller Port  FAIL!'

        # Query Controller Port threshold for a rule_name
        response = requests.get(URL+'healthycheck/v1/controller/port/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller Port threshold for a rule_name = '+rule_name+' FAIL!'

        # Delete Controller Port threshold by rule_name
        response = requests.delete(URL+'healthycheck/v1/controller/port/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete Controller Port threshold by rule_name = '+rule_name+' FAIL!'

        # Check if delete successfully
        response = requests.get(URL+'healthycheck/v1/controller/port/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Controller Port threshold for a rule_name = '+rule_name+' FAIL!'
        assert response.json() == {}, 'Delete Controller Port threshold by rule_name = '+rule_name+' FAIL!'


class SwitchCpu(base_tests.SimpleDataPlane):
    """
    Test HealthyCheck Switch CPU Threshold RestAPI
        - GET /healthycheck/v1/switch/cpu/threshold
        - POST /healthycheck/v1/switch/cpu/threshold
        - GET /healthycheck/v1/switch/cpu/threshold/<rule_name>
        - DELETE /healthycheck/v1/switch/cpu/threshold/<rule_name>
    """

    def runTest(self):

        # Query Switch CPU threshold
        response = requests.get(URL+'healthycheck/v1/switch/cpu/threshold', headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch CPU threshold FAIL!'

        # Add threshold for Switch CPU
        rule_name = "test_rule_name"
        payload = {
            "name": rule_name,
            "status": "enabled",
            "alert_level": 1,
            "receive_group": "group name",
            "query": [
                {
                "util": 10,
                "condition": "gt",
                "continue": 180
                }
            ]
        }
        response = requests.post(URL+'healthycheck/v1/switch/cpu/threshold', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add threshold for Switch CPU FAIL!'

        # Query Switch CPU threshold for a rule_name
        response = requests.get(URL+'healthycheck/v1/switch/cpu/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch CPU threshold for a rule_name = '+rule_name+' FAIL!'

        # Delete Switch CPU threshold by rule_name
        response = requests.delete(URL+'healthycheck/v1/switch/cpu/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete Switch CPU threshold by rule_name = '+rule_name+' FAIL!'

        # Check if delete successfully
        response = requests.get(URL+'healthycheck/v1/switch/cpu/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch CPU threshold for a rule_name = '+rule_name+' FAIL!'
        assert response.json() == {}, 'Delete Switch CPU threshold by rule_name = '+rule_name+' FAIL!'


class SwitchRam(base_tests.SimpleDataPlane):
    """
    Test HealthyCheck Switch RAM Threshold RestAPI
        - GET /healthycheck/v1/switch/ram/threshold
        - POST /healthycheck/v1/switch/ram/threshold
        - GET /healthycheck/v1/switch/ram/threshold/<rule_name>
        - DELETE /healthycheck/v1/switch/ram/threshold/<rule_name>
    """

    def runTest(self):

        # Query Switch Ram threshold
        response = requests.get(URL+'healthycheck/v1/switch/ram/threshold', headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch Ram threshold FAIL!'

        # Add threshold for Switch RAM
        rule_name = "test_rule_name"
        payload = {
            "name": rule_name,
            "status": "enabled",
            "alert_level": 1,
            "receive_group": "group name",
            "query": [
                {
                "used_ratio": 10,
                "condition": "gt",
                "continue": 180
                }
            ]
        }
        response = requests.post(URL+'healthycheck/v1/switch/ram/threshold', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add threshold for Switch RAM FAIL!'

        # Query Switch RAM threshold for a rule_name
        response = requests.get(URL+'healthycheck/v1/switch/ram/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch RAM threshold for a rule_name = '+rule_name+' FAIL!'

        # Delete Switch RAM threshold by rule_name
        response = requests.delete(URL+'healthycheck/v1/switch/ram/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete Switch RAM threshold by rule_name = '+rule_name+' FAIL!'

        # Check if delete successfully
        response = requests.get(URL+'healthycheck/v1/switch/ram/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch ram threshold for a rule_name = '+rule_name+' FAIL!'
        assert response.json() == {}, 'Delete Switch RAM threshold by rule_name = '+rule_name+' FAIL!'


class SwitchDisk(base_tests.SimpleDataPlane):
    """
    Test HealthyCheck Switch Disk Threshold RestAPI
        - GET /healthycheck/v1/switch/disk/threshold
        - POST /healthycheck/v1/switch/disk/threshold
        - GET /healthycheck/v1/switch/disk/threshold/<rule_name>
        - DELETE /healthycheck/v1/switch/disk/threshold/<rule_name>
    """

    def runTest(self):

        # Query Switch Disk threshold
        response = requests.get(URL+'healthycheck/v1/switch/disk/threshold', headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch Disk threshold FAIL!'

        # Add threshold for Switch Disk
        rule_name = "test_rule_name"
        payload = {
            "name": rule_name,
            "status": "enabled",
            "alert_level": 1,
            "receive_group": "group name",
            "query": [
                {
                "root_used_ratio": 10,
                "condition": "gt",
                "continue": 180
                }
            ]
        }
        response = requests.post(URL+'healthycheck/v1/switch/disk/threshold', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add threshold for Switch Disk FAIL!'

        # Query Switch Disk threshold for a rule_name
        response = requests.get(URL+'healthycheck/v1/switch/disk/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch Disk threshold for a rule_name = '+rule_name+' FAIL!'

        # Delete Switch Disk threshold by rule_name
        response = requests.delete(URL+'healthycheck/v1/switch/disk/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete Switch Disk threshold by rule_name = '+rule_name+' FAIL!'

        # Check if delete successfully
        response = requests.get(URL+'healthycheck/v1/switch/disk/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch Disk threshold for a rule_name = '+rule_name+' FAIL!'
        assert response.json() == {}, 'Delete Switch Disk threshold by rule_name = '+rule_name+' FAIL!'


class SwitchPort(base_tests.SimpleDataPlane):
    """
    Test HealthyCheck Switch Port Threshold RestAPI
        - GET /healthycheck/v1/switch/port/threshold
        - POST /healthycheck/v1/switch/port/threshold
        - GET /healthycheck/v1/switch/port/threshold/<rule_name>
        - DELETE /healthycheck/v1/switch/port/threshold/<rule_name>
    """

    def runTest(self):

        # Query Switch Port threshold
        response = requests.get(URL+'healthycheck/v1/switch/port/threshold', headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch Port threshold FAIL!'

        # Add threshold for Switch Port
        rule_name = "test_rule_name"
        payload = {
            "name": rule_name,
            "status": "enabled",
            "alert_level": 1,
            "receive_group": "group name",
            "query_rx": [
                {
                "rx_util": 10,
                "condition": "gt",
                "continue": 180
                }
            ],
            "query_tx": [
                {
                "tx_util": 10,
                "condition": "gt",
                "continue": 180
                }
            ]
        }
        response = requests.post(URL+'healthycheck/v1/switch/port/threshold', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add threshold for Switch Port FAIL!'

        # Query Switch Port threshold for a rule_name
        response = requests.get(URL+'healthycheck/v1/switch/port/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch Port threshold for a rule_name = '+rule_name+' FAIL!'

        # Delete Switch Port threshold by rule_name
        response = requests.delete(URL+'healthycheck/v1/switch/port/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete Switch Port threshold by rule_name = '+rule_name+' FAIL!'

        # Check if delete successfully
        response = requests.get(URL+'healthycheck/v1/switch/port/threshold/'+rule_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query Switch Port threshold for a rule_name = '+rule_name+' FAIL!'
        assert response.json() == {}, 'Delete Switch Port threshold by rule_name = '+rule_name+' FAIL!'


class AllThreshold(base_tests.SimpleDataPlane):
    """
    Test HealthyCheck Get all threshold
        - GET /healthycheck/v1/threshold
    """

    def runTest(self):

        # Query all threshold
        response = requests.get(URL+'healthycheck/v1/threshold', headers=GET_HEADER)
        assert response.status_code == 200, 'Query all threshold FAIL!'


class SensorsGetter(base_tests.SimpleDataPlane):
    """
    Test Device Sensors RestAPI
        - GET /sensors/<device_id>/temp
        - GET /sensors/<device_id>/psu
        - GET /sensors/<device_id>/fan
    """

    def runTest(self):

        # Get a device_id
        response = requests.get(URL+"v1/devices", headers=GET_HEADER)
        assert response.status_code == 200, 'Query devices is FAIL!'
        assert len(response.json()['devices']) > 0, 'Test NTP Server RestAPI need at least one device'
        device_id = response.json()['devices'][0]['id']

        # Query temperature sensor of a device
        response = requests.get(URL+'healthycheck/v1/sensors/'+device_id+'/temp', headers=GET_HEADER)
        assert response.status_code == 200, 'Query temperature sensor of device_id = '+device_id+' FAIL!'

        # Query psu sensot of a device
        response = requests.get(URL+'healthycheck/v1/sensors/'+device_id+'/psu', headers=GET_HEADER)
        assert response.status_code == 200, 'Query psu sensor of device_id = '+device_id+' FAIL!'

        # Query fan sensot of a device
        response = requests.get(URL+'healthycheck/v1/sensors/'+device_id+'/fan', headers=GET_HEADER)
        assert response.status_code == 200, 'Query fan sensor of device_id = '+device_id+' FAIL!'

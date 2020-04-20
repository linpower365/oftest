"""
Test flow
"""

import oftest.base_tests as base_tests
from oftest import config
import config as test_config
import requests

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}


class FlowTest(base_tests.SimpleDataPlane):
    """
    Test add, get, delete flow
    """

    def runTest(self):
        response = requests.get(URL+"v1/devices", headers=GET_HEADER)
        assert(response.status_code == 200)
        assert(len(response.json()['devices']) > 0)
        device = response.json()['devices'][0]
        device_id = device['id']

        # add l2_interface_gorup
        p2_payload = """
        {
          "type": "INDIRECT",
          "appCookie": "0x10002",
          "groupId": 65538,
          "buckets": [
            {
              "treatment": {
                "instructions": [
                  {
                    "type": "OUTPUT",
                    "port": "2"
                  }
                ]
              }
            }
          ]
        }
     """
        response = requests.post(
            URL+"v1/groups/"+device_id,  headers=POST_HEADER, data=p2_payload)
        assert(response.status_code == 201)

        # add flow
        flow_payload = """
     {
      "flows": [
        {
          "priority": 40000,
          "timeout": 0,
          "isPermanent": true,
          "tableId": 60,
          "deviceId": "_DEVICE_ID_",
          "treatment": {
            "instructions": [
              {
                "type": "GROUP",
                "groupId": 65538
              }
            ]
          },
          "selector": {
            "criteria": [
              {
                "type": "IN_PORT",
                "port": "1"
              }
            ]
          }
        }
      ]
     }
     """
        flow_payload = flow_payload.replace("_DEVICE_ID_", device_id)
        response = requests.post(
            URL+"v1/flows?appId=org.onosproject.drivers",  headers=POST_HEADER, data=flow_payload)
        assert(response.status_code == 200)
        flowid = response.json()["flows"][0]["flowId"]

        # get flows
        response = requests.get(
            URL+"v1/flows/"+device_id+"/"+flowid,  headers=GET_HEADER)
        assert(response.status_code == 200)
        assert(len(response.json()["flows"]) == 1)

        # delete flow
        response = requests.delete(
            URL+"v1/flows/"+device_id+"/"+flowid,  headers=GET_HEADER)
        assert(response.status_code == 204)

        # delete group
        response = requests.delete(
            URL+"v1/groups/"+device_id+"/0x10002",  headers=GET_HEADER)
        assert(response.status_code == 204)

"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html
Get Test

Test each flow table can set entry, and packet rx correctly.
"""

import oftest.base_tests as base_tests
import config as test_config
import requests
import auth
from time import sleep

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}
GET_HEADER = {'Accept': 'application/json'}
POST_HEADER = {'Content-Type': 'application/json'}
COOKIES = auth.Authentication().login().get_cookies()


class IntentTest(base_tests.SimpleDataPlane):
    """
    Test
    """

    def runTest(self):
        response = requests.get(
            URL+"v1/devices", cookies=COOKIES, headers=GET_HEADER)
        assert(response.status_code == 200)
        assert(len(response.json()['devices']) > 0)
        device = response.json()['devices'][0]
        device_id = device['id']

        # add host1
        p1_payload = """
        {
          "mac": "46:E4:3C:A4:17:88",
          "vlan": "-1",
          "ipAddresses": [
            "192.168.1.1"
          ],
          "locations": [
            {
              "elementId": "_DEVICE_ID_",
              "port": "3"
            }
          ]
        }
     """
        p1_payload = p1_payload.replace("_DEVICE_ID_", device_id)
        response = requests.post(
            URL+"v1/hosts/", cookies=COOKIES, headers=POST_HEADER, data=p1_payload)
        assert(response.status_code == 201)
        # add host2
        p2_payload = """
        {
          "mac": "46:E4:3C:A4:17:99",
          "vlan": "-1",
          "ipAddresses": [
            "192.168.2.1"
          ],
          "locations": [
            {
              "elementId": "_DEVICE_ID_",
              "port": "3"
            }
          ]
        }
     """
        p2_payload = p2_payload.replace("_DEVICE_ID_", device_id)
        response = requests.post(
            URL+"v1/hosts/", cookies=COOKIES, headers=POST_HEADER, data=p2_payload)
        assert(response.status_code == 201)

        # add intents
        intent_payload = """
        {
          "type": "HostToHostIntent",
          "appId": "org.onosproject.ovsdb",
          "priority": 55,
          "one": "46:E4:3C:A4:17:88/-1",
          "two": "46:E4:3C:A4:17:99/-1"
        }
     """
        response = requests.post(
            URL+"v1/intents", cookies=COOKIES, headers=POST_HEADER, data=intent_payload)
        assert(response.status_code == 201)

        # we need to wait, or can't get any data
        sleep(3)
        response = requests.get(
            URL+"v1/intents/", cookies=COOKIES, headers=GET_HEADER)
        assert(response.status_code == 200)
        intent_id = 0
        for e in response.json()["intents"]:
            if e["type"] == "HostToHostIntent" and (e["resources"][0] == "46:E4:3C:A4:17:88/None" or e["resources"][1] == "46:E4:3C:A4:17:88/None"):
                intent_id = e["key"]
                break
        assert(intent_id != 0)

        # check flows
        response = requests.get(URL+"v1/flows/"+device_id,
                                cookies=COOKIES, headers=GET_HEADER)
        assert(response.status_code == 200)
        hit_flow = False
        for e in response.json()["flows"]:
            for c in e["selector"]["criteria"]:
                if c["type"] == "ETH_DST" and c["mac"] == "46:E4:3C:A4:17:88":
                    hit_flow = True
        assert(hit_flow == True)

        # delete intents
        sleep(3)
        response = requests.get(
            URL+"v1/intents/", cookies=COOKIES, headers=GET_HEADER)
        assert(response.status_code == 200)
        intent_id = 0
        for e in response.json()["intents"]:
            if e["type"] == "HostToHostIntent" and (e["resources"][0] == "46:E4:3C:A4:17:88/None" or e["resources"][1] == "46:E4:3C:A4:17:88/None"):
                intent_id = e["key"]
                break
        for e in response.json()["intents"]:
            if e["type"] == "HostToHostIntent" and (e["resources"][0] == "46:E4:3C:A4:17:88/None" or e["resources"][1] == "46:E4:3C:A4:17:88/None"):
                intent_id = e["key"]
                response = requests.delete(
                    URL+"v1/intents/"+"org.onosproject.ovsdb"+"/"+intent_id, cookies=COOKIES, headers=GET_HEADER)
                assert(response.status_code == 204)

        # check in deleting
        response = requests.get(
            URL+"v1/intents/", cookies=COOKIES, headers=GET_HEADER)
        assert(response.status_code == 200)
        sleep(2)
        intent_id = 0
        for e in response.json()["intents"]:
            if e["type"] == "HostToHostIntent" and (e["resources"][0] == "46:E4:3C:A4:17:88/None" or e["resources"][1] == "46:E4:3C:A4:17:88/None"):
                assert(e["state"] == "WITHDRAWN")

        # delete host
        response = requests.delete(
            URL+"v1/hosts/"+"46:E4:3C:A4:17:99"+"/None", cookies=COOKIES, headers=GET_HEADER)
        assert(response.status_code == 204)
        response = requests.delete(
            URL+"v1/hosts/"+"46:E4:3C:A4:17:88"+"/None", cookies=COOKIES, headers=GET_HEADER)
        assert(response.status_code == 204)

"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test Alert RestAPI.
"""


import oftest.base_tests as base_tests
import config as test_config
import requests

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}


class HistoryTest(base_tests.SimpleDataPlane):
    """
    Test History RestAPI
        - GET /alert/v1/history/list
        - DELETE /alert/v1/history/uuid/<uuid>
        - POST /alert/v1/history/select/delete
        - DELETE /alert/v1/history/all
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def runTest(self):
        
        # Get all history
        response = requests.get(URL+'alert/v1/history/list', headers=GET_HEADER)
        assert response.status_code == 200, 'Query all history FAIL!'

        # Delete an alert history of a uuid
        response = requests.delete(URL+'alert/v1/history/uuid/00000000-0000-0000-0000-000000000000', headers=GET_HEADER)
        assert response.status_code == 200, 'Delete an alert history of a uuid FAIL!'

        # Delete many history
        payload = {
            "uuid": [
                "00000000-0000-0000-0000-000000000000",
                "00000000-0000-0000-0000-000000000001"
            ]
        }
        response = requests.post(URL+'alert/v1/history/select/delete', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Delete many history FAIL!'

        # Delete all history
        response = requests.delete(URL+'alert/v1/history/all', headers=GET_HEADER)
        assert response.status_code == 200, 'Delete all history FAIL!'

        # Check if delete successfully
        response = requests.get(URL+'alert/v1/history/list', headers=GET_HEADER)
        assert response.status_code == 200, 'Query all history FAIL!'
        assert len(response.json()['history']) == 0, 'Delete all history FAIL!'


class BasicConfigTest(base_tests.SimpleDataPlane):
    """
    Test Basic Config RestAPI
        - GET /alert/v1/basicconfig
        - POST /alert/v1/basicconfig
        - DELETE /alert/v1/basicconfig
    """

    def runTest(self):

        # Get Basic Config
        response = requests.get(URL+'alert/v1/basicconfig', headers=GET_HEADER)
        assert response.status_code == 200, 'Get Basic Config FAIL!'

        # POST Basic Config
        payload = {
            "wechat": {
                "corpid": "ww8e2c422fcf314137",
                "host": "qyapi.weixin.qq.com",
                "send_url": "/cgi-bin/message/send",
                "token_url": "/cgi-bin/gettoken"
            },
            "smtp": {
                "smtp_host": "<SMTP_HOST>",
                "smtp_port": 25,
                "smtp_ssl": False,
                "password": "<EMAIL_PASSWORD>",
                "user": "<EMAIL_USER>"
            },
            "alert_level": {
                "resend_minutes": 10
            }
        }
        response = requests.post(URL+'alert/v1/basicconfig', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'POST Basic Config FAIL!'

        # Check if post successfully
        response = requests.get(URL+'alert/v1/basicconfig', headers=GET_HEADER)
        assert response.status_code == 200, 'Get Basic Config FAIL!'
        assert len(response.text) != 0, 'POST Basic Config FAIL!'

        # Delete Basic Config settings
        response = requests.delete(URL+'alert/v1/basicconfig', headers=GET_HEADER)
        assert response.status_code == 200, 'Delete Basic Config FAIL!'

        # Check if delete successfully
        response = requests.get(URL+'alert/v1/basicconfig', headers=GET_HEADER)
        assert response.status_code == 200, 'Get Basic Config FAIL!'
        assert response.json() == {}, 'Delete Basic Config FAIL!'


class GroupReceiverTest(base_tests.SimpleDataPlane):
    """
    Test Group Receiver RestAPI
        - GET /alert/v1/group/receiver/all
        - POST /alert/v1/group/receiver
        - GET /alert/v1/group/receiver/<group_name>
        - DELETE /alert/v1/group/receiver/<group_name>
    """

    def runTest(self):

        # Get all alert receiver group
        response = requests.get(URL+'alert/v1/group/receiver/all', headers=GET_HEADER)
        assert response.status_code == 200, 'Get all group FAIL!'

        # Add a receive group
        group_name = 'mytestgroup'
        payload = {
        "name": group_name,
            "receive": {
                "wechat": [
                    {
                        "department": "dep01",
                        "agentId": 1000000,
                        "agent_corpsecret": "0000000000000000000000000000000000000000000"
                    }
                ],
                "email": [
                    {
                        "name": "mail01",
                        "email": "mail01@gmail.com"
                    }
                ]
            }
        }
        response = requests.post(URL+'alert/v1/group/receiver', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add a new receive group FAIL!'

        # Check if add successfully
        response = requests.get(URL+'alert/v1/group/receiver/'+group_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Query group_name = '+group_name+' FAIL!'
        assert response.json() == payload, 'Add a new receiver group FAIL!'

        # Delete the group
        response = requests.delete(URL+'alert/v1/group/receiver/'+group_name, headers=GET_HEADER)
        assert response.status_code == 200, 'Delete group_name = '+group_name+' FAIL!'

        # Check if delete successfully
        response = requests.get(URL+'alert/v1/group/receiver/all', headers=GET_HEADER)
        assert response.status_code == 200, 'Get all group FAIL!'
        notexist = True
        for item in response.json()['group']:
            if item['name'] == group_name:
                notexist = False
                break
        assert notexist, 'Delete group_name = '+group_name+' FAIL!'

"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test UserAccount RestAPI.
"""


import oftest.base_tests as base_tests
import config as test_config
import requests
import time
import auth

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
# GET_HEADER = {'Authorization': AUTH_TOKEN}
# POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}
GET_HEADER = {'Accept': 'application/json'}
POST_HEADER = {'Content-Type': 'application/json'}
COOKIES = auth.Authentication().login().get_cookies()


class AccountTest(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)


class Getter(AccountTest):
    """
    Test useraccount GET method
        - /useraccount/v1
        - /useraccount/v1/group/{group_name}
        - /useraccount/v1/{user_name}
    """

    def runTest(self):
        response = requests.get(URL+"useraccount/v1/info",
                                cookies=COOKIES, headers=GET_HEADER)

        assert(response.status_code == 200)
        assert(len(response.json()['users']) != 0)

        response = requests.get(URL+"useraccount/v1/info/group/admingroup",
                                cookies=COOKIES, headers=GET_HEADER
                                )

        assert(response.status_code == 200)
        assert(len(response.json()['users']) != 0)

        response = requests.get(URL+"useraccount/v1/info/"+test_config.ADMIN_USERNAME,
                                cookies=COOKIES, headers=GET_HEADER
                                )

        assert(response.status_code == 200)
        assert(response.json()['user_name'] == test_config.ADMIN_USERNAME)


class AddAndDeleteUser(AccountTest):
    """
    Test add a new user and delete it
        POST /useraccount/v1
        DELETE /useraccount/v1/{user_name}
    """

    def runTest(self):
        username = 'test' + str(int(time.time()))

        # add a user
        payload = '{"user_name": "' + username + \
            '",  "groups": ["admingroup" ], "password": "testPassword"}'
        response = requests.post(URL+"useraccount/v1/info",
                                 cookies=COOKIES, headers=POST_HEADER, data=payload
                                 )
        assert(response.status_code == 200)

        response = requests.get(
            URL+"useraccount/v1/info/group/admingroup", cookies=COOKIES, headers=GET_HEADER
        )
        assert(response.status_code == 200)
        assert(username in response.json()['users'])

        # delete the user
        response = requests.delete(
            URL+"useraccount/v1/info/{}".format(username), cookies=COOKIES, headers=GET_HEADER
        )
        assert(response.status_code == 200)

        response = requests.get(
            URL+"useraccount/v1/info/group/admingroup", cookies=COOKIES, headers=GET_HEADER
        )
        assert(response.status_code == 200)
        assert(username not in response.json()['users'])


class EmptyQuery(AccountTest):
    """
    Test query empty data or wrong input
    """

    def runTest(self):

        # query not exist user
        response = requests.get(
            URL+"useraccount/v1/info/notexistuser999", cookies=COOKIES, headers=GET_HEADER
        )
        assert(response.status_code == 200)
        assert(len(response.json()) == 0)

        # query not exist group
        response = requests.get(
            URL + "useraccount/v1/info/group/notexistgroup999", cookies=COOKIES, headers=GET_HEADER
        )
        assert(response.status_code == 200)
        assert(len(response.json()["users"]) == 0)

        # delete not exist user
        response = requests.delete(
            URL+'useraccount/v1/info/notexistgroup999', cookies=COOKIES, headers=GET_HEADER
        )
        assert(response.status_code == 200)

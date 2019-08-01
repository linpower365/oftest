"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test TenantLogicalRouter RestAPI.
"""


import oftest.base_tests as base_tests
import config as test_config
import requests
import time

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}


class TenantLogicalRouterGetTest(base_tests.SimpleDataPlane):
    """
    Test tenantlogicalrouter GET method
        - /tenantlogicalrouter/v1
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def runTest(self):
        response = requests.get(URL+"tenantlogicalrouter/v1", headers=GET_HEADER)
        assert(response.status_code == 200)
        

class TenantLogicalRouterAddNewTest(base_tests.SimpleDataPlane):
    """
    Test tenantlogicalrouter add a new one and delete it
        - POST v1/tenants/v1
        - GET v1/tenants/v1
        - POST v1/tenants/v1/<tenant_name>/segments/
        - GET v1/tenants/v1/segments
        - POST tenantlogicalrouter/v1/tenants/<tenant_name>
        - GET tenantlogicalrouter/v1
        - DELETE v1/tenants/v1/<tenant_name>/segments/<segment_name>
        - DELETE tenantlogicalrouter/v1/tenants/<tenant_name>/<tenantlogicalrouter_name>
        - DELETE v1/tenants/v1/<tenant_name>
    """
    def runTest(self):

        # add a new tenant
        tenant_name = 'testTenant' + str(int(time.time()))
        payload = {
            "name": tenant_name,
            "type": "Normal"
        }
        response = requests.post(URL+"v1/tenants/v1", headers=POST_HEADER, json=payload)
        assert(response.status_code == 200)

        # check if tenant add succuss
        response = requests.get(URL+'v1/tenants/v1', headers=GET_HEADER)
        exist = False
        for item in response.json()['tenants']:
            if item['name'] == tenant_name:
                exist = True
                break
        assert(exist)

        # add a new segment on the tenant
        payload = {
            "name": "testsegment001",
            "type": "vlan",
            "value": 10,
            "ip_address": [
                "192.168.3.3"
            ]
        }
        response = requests.post(URL+'v1/tenants/v1/'+tenant_name+'/segments/', headers=POST_HEADER, json=payload)
        assert(response.status_code == 200)

        # check if segment add success
        response = requests.get(URL+"v1/tenants/v1/segments",headers=GET_HEADER)
        exist = False
        for item in response.json()['segments']:
            if item['segment_name'] == 'testsegment001':
                exist = True
                break
        assert(exist)


        # add new tenantlogicalrouter
        payload = {
            "name": "tenantlogicalrouter01",
            "interfaces":[
                "testsegment001"
            ]
        }
        response = requests.post(URL+"tenantlogicalrouter/v1/tenants/"+tenant_name, headers=POST_HEADER, json=payload)
        assert(response.status_code == 200)

        # check if tenantlogicalrouter add successfully
        response = requests.get(URL+"tenantlogicalrouter/v1", headers=GET_HEADER)
        exist = False
        for item in response.json()['routers']:
            if item['name'] == 'tenantlogicalrouter01':
                exist = True
                break
        assert(True)

        # delete segment
        response = requests.delete(URL+ 'v1/tenants/v1/'+tenant_name+'/segments/testsegment001', headers=GET_HEADER)
        assert(response.status_code == 200)
        
        # delete tenantlogicalrouter
        response = requests.delete(URL+'tenantlogicalrouter/v1/tenants/'+tenant_name+'/tenantlogicalrouter01', headers=GET_HEADER)
        assert(response.status_code == 200)

        # delete test tenant
        response = requests.delete(URL+'v1/tenants/v1/'+tenant_name, headers=GET_HEADER)
        assert(response.status_code == 200)

        # check segment delete successfully
        response = requests.get(URL+"v1/tenants/v1/segments",headers=GET_HEADER)
        assert(response.status_code == 200)
        removed = True
        for item in response.json()['segments']:
            if item['segment_name'] == 'testsegment001':
                removed = False
        assert(removed)

        # check tenantlogicalrouter delete successfully
        response = requests.get(URL+"tenantlogicalrouter/v1", headers=GET_HEADER)
        assert(response.status_code == 200)
        removed = True
        for item in response.json()['routers']:
            if item['name'] == 'tenantlogicalrouter01':
                removed = False
        assert(removed)

        # check tenant delete successfully
        response = requests.get(URL+'v1/tenants/v1', headers=GET_HEADER)
        assert(response.status_code == 200)
        removed = True
        for item in response.json()['tenants']:
            if item['name'] == tenant_name:
                removed = False
        assert(removed)


class TenantLogicalRouterNotExistTest(base_tests.SimpleDataPlane):
    """
    Test not exist data
    """
    # add new tenantlogicalrouter on not exist tenant
    payload = {
        "name": "tenantlogicalrouter01"
    }
    response = requests.post(URL+"tenantlogicalrouter/v1/tenants/testTenantNotExist999/", headers=POST_HEADER, json=payload)
    assert(response.status_code == 400)

    # list tenantlogicalrouters which tenant is not exist
    response = requests.get(URL+"tenantlogicalrouter/v1/tenants/testTenantNotExist999/", headers=GET_HEADER)
    assert(response.status_code == 200)
    assert(len(response.json()['routers']) == 0)

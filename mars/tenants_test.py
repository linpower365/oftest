"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test Tenants RestAPI.

Test environment

    +--------+     +--------+    
    | spine0 |     | spine1 |
    +--------+     +--------+
        |              |
        +--------------+     
        |              |
    +--------+     +--------+
    |  leaf0 |     |  leaf1 |
    +--------+     +--------+
      |    |         |    | 
      p0   p1        p2   p3

p0: port 46 of leaf0
p1: port 48 of leaf0
p2: port 46 of leaf1
p3: port 48 of leaf1
"""

import oftest.base_tests as base_tests
from oftest import config
from oftest.testutils import *
import config as test_config
import requests
import utils

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}

class TenantsGetTest(base_tests.SimpleDataPlane):
    """
    Test tenant GET method
        - /v1/tenants/v1
    """

    def runTest(self):
        response = requests.get(URL+"v1/tenants/v1", headers=GET_HEADER)
        assert(response.status_code == 200)

class TenantsAddNewTest(base_tests.SimpleDataPlane):
    """
    Test adding a new tenant and delete it
      - POST v1/tenants/v1
      - DELETE v1/tenants/v1/{tenant_name}
      - GET v1/tenants/v1
    """

    def runTest(self):
        utils.wait_for_system_stable()

        tenant_name = 'testTenant' + str(int(time.time()))
        # add a tenant
        payload = '{"name": "' + tenant_name + '", "type": "System"}'
        response = requests.post(
            URL+"v1/tenants/v1", headers=POST_HEADER, data=payload)
        assert(response.status_code == 200)

        # query tenants
        response = requests.get(URL + 'v1/tenants/v1', headers=GET_HEADER)
        assert(response.status_code == 200)
        found = False
        for t in response.json()['tenants']:
            if t['name'] == tenant_name:
                found = True
                break
        assert(found)

        # delete test tenant
        response = requests.delete(URL + 'v1/tenants/v1/{}'.format(tenant_name), headers=GET_HEADER)
        assert(response.status_code == 200)

        # query and check
        response = requests.get(URL + 'v1/tenants/v1', headers=GET_HEADER)
        assert(response.status_code == 200)
        not_exist = True
        if len(response.json()) > 0:
            for t in response.json()['tenants']:
                if t['name'] == tenant_name:
                    not_exist = False
                    break
        assert(not_exist)


class SegmentTest(base_tests.SimpleDataPlane):
    """
        Test Tenant Segment RestAPI
        - POST v1/tenants/v1/<tenant_name>/segments
        - GET v1/tenants/v1/segments
        - GET v1/tenants/v1/<tenant_name>/segments/<segment_name>
        - DELETE v1/tenants/v1/<tenant_name>/segments/<segment_name>
    """

    def runTest(self):
        utils.wait_for_system_stable()

        tenant_name = 'testTenant' + str(int(time.time()))
        segment_name = 'testSegment'

        # add a tenant
        payload = '{"name": "' + tenant_name + '", "type": "System"}'
        response = requests.post(URL+"v1/tenants/v1", headers=POST_HEADER, data=payload)
        assert response.status_code == 200, 'Add a tenant FAIL! '+ response.text

        # check if add tenant successfully
        response = requests.get(URL+'v1/tenants/v1', headers=GET_HEADER)
        assert response.status_code == 200, 'Query tenants FAIL!'

        find = False
        for item in response.json()['tenants']:
            if item['name'] == tenant_name:
                find = True
        assert find, 'Add a tenant FAIL!'

        # add a segment
        payload = {
            "name": segment_name,
            "type": "vlan",
            "ip_address": [
                "192.168.2.1"
            ],
            "value": "20"
        }
        response = requests.post(URL+'v1/tenants/v1/{}/segments'.format(tenant_name), json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add segment FAIL! ' + response.text

        # check if add segment successfully
        response = requests.get(URL+'v1/tenants/v1/segments', headers=GET_HEADER)
        assert response.status_code == 200, 'Query all segments FAIL!'
        find = False
        for item in response.json()['segments']:
            if item['segment_name'] == segment_name:
                find = True
        assert find, 'Add segment FAIL!'

        # check if add segment successfully with another API
        response = requests.get(URL+'v1/tenants/v1/{}/segments/{}'.format(tenant_name, segment_name), headers=GET_HEADER)
        assert response.status_code == 200, 'Query segment FAIL!'
        assert len(response.text) != 0, 'Add segment FAIL!'

        # Delete segment
        response = requests.delete(URL+'v1/tenants/v1/{}/segments/{}'.format(tenant_name, segment_name), headers=GET_HEADER)
        assert response.status_code == 200, 'Delete segment FAIL!'

        # check if delete segment successfully
        response = requests.get(URL+'v1/tenants/v1/{}/segments/{}'.format(tenant_name, segment_name), headers=GET_HEADER)
        assert response.status_code != 200, 'Delete segment FAIL!'

        # delete test tenant
        response = requests.delete(URL + 'v1/tenants/v1/{}'.format(tenant_name), headers=GET_HEADER)
        assert(response.status_code == 200)

@disabled
class LargeScaleTest(base_tests.SimpleDataPlane):
    """
        - Test 4K tenant each 1 segment
        - Test 1 tenant and 4k segment
    """

    def runTest(self):
        utils.wait_for_system_stable()

        # case 1: 4K tenant each 1 segmant
        for i in range(4000):
            # add tenant
            tenant_name = 'test_tenant_'+str(i)
            payload = {
                'name':  tenant_name,
                'type': 'Normal'
            }
            response = requests.post(URL+"v1/tenants/v1", headers=POST_HEADER, json=payload)
            assert response.status_code == 200, 'Add a tenant FAIL! '+ response.text
            # add segment
            segment_name = 'test_segment_+'+str(i)
            payload = {
                "name": segment_name,
                "type": "vlan",
                "ip_address": [
                    "192.168.2.1"
                ],
                "value": i
            }
            response = requests.post(URL+'v1/tenants/v1/{}/segments'.format(tenant_name), json=payload, headers=POST_HEADER)
            assert response.status_code == 200, 'Add segment FAIL! ' + response.text
            # delete segment
            response = requests.delete(URL+'v1/tenants/v1/{}/segments/{}'.format(tenant_name, segment_name), headers=GET_HEADER)
            assert response.status_code == 200, 'Delete segment FAIL!'
            # delete tenant
            response = requests.delete(URL + 'v1/tenants/v1/{}'.format(tenant_name), headers=GET_HEADER)
            assert(response.status_code == 200)
        
        # case 2: 1 tenant with 4k segment
        tenant_name = 'test_tenant'
        payload = {
            'name':  tenant_name,
            'type': 'Normal'
        }
        # add tenant
        response = requests.post(URL+"v1/tenants/v1", headers=POST_HEADER, json=payload)
        assert response.status_code == 200, 'Add a tenant FAIL! '+ response.text
        # add segment
        for i in range(4000):
            segment_name = 'test_segment_'+str(i)
            payload = {
                "name": segment_name,
                "type": "vlan",
                "ip_address": [
                    "192.168.2.1"
                ],
                "value": 10000+i
            }
            response = requests.post(URL+'v1/tenants/v1/{}/segments'.format(tenant_name), json=payload, headers=POST_HEADER)
            assert response.status_code == 200, 'Add segment FAIL! ' + response.text
            # delete segment
            response = requests.delete(URL+'v1/tenants/v1/{}/segments/{}'.format(tenant_name, segment_name), headers=GET_HEADER)
            assert response.status_code == 200, 'Delete segment FAIL!'
        # delete tenant
        response = requests.delete(URL + 'v1/tenants/v1/{}'.format(tenant_name), headers=GET_HEADER)
        assert response.status_code == 200, 'Delete tenant FAIL!' + response.text


class SegmentVlanTypeConnectionTest(base_tests.SimpleDataPlane):
    '''
    Test segment vlan type connection.
    '''

    def runTest(self):
        utils.wait_for_system_stable()

        tenant_name = 'testTenant'
        segment_name = 'testSegment'
        vlan_id = 3000
        ports = sorted(config["port_map"].keys())

        # add a tenant
        payload = {
            'name': tenant_name,
            'type': 'Normal'
        }
        response = requests.post(URL+"v1/tenants/v1", headers=POST_HEADER, json=payload)
        self.assertEqual(200, response.status_code, 'Add a tenant fail! '+ response.text)

        # add a segment on testenant
        payload = {
            "name": segment_name,
            "type": "vlan",
            "ip_address": ['192.168.1.1'],
            "value": vlan_id
        }
        response = requests.post(URL+'v1/tenants/v1/{}/segments'.format(tenant_name), json=payload, headers=POST_HEADER)
        self.assertEqual(200, response.status_code, 'Add segment fail! '+ response.text)

        # add segment member,
        payload = {
            "ports" : ["46/tag", "48/tag"],
        }
        device_id = 'rest:192.168.40.150:80'
        response = requests.post(URL+'v1/tenants/v1/{}/segments/{}/device/{}/vlan'.format(tenant_name, segment_name, device_id),
            json=payload, headers=POST_HEADER)
        self.assertEqual(200, response.status_code, 'Add segment member fail '+ response.text)

        payload = {
            "ports" : ["46/tag"],
        }
        device_id = 'rest:192.168.40.149:80'
        response = requests.post(URL+'v1/tenants/v1/{}/segments/{}/device/{}/vlan'.format(tenant_name, segment_name, device_id),
            json=payload, headers=POST_HEADER)
        self.assertEqual(200, response.status_code, 'Add segment member fail '+ response.text)

        utils.wait_for_system_stable()

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=100,
            dl_vlan_enable=True,
            vlan_vid=vlan_id,
            eth_dst='90:e2:ba:24:78:12',
            eth_src='00:00:00:11:22:33',
            ip_src='192.168.1.100',
            ip_dst='192.168.1.101'
        )

        pkt_from_p0_to_p2 = simple_tcp_packet(
            pktlen=100,
            dl_vlan_enable=True,
            vlan_vid=vlan_id,
            eth_dst='90:e2:ba:24:a2:70',
            eth_src='00:00:00:11:22:33',
            ip_src='192.168.1.100',
            ip_dst='192.168.1.110'
        )

        pkt_from_p0_to_p3 = simple_tcp_packet(
            pktlen=100,
            dl_vlan_enable=True,
            vlan_vid=vlan_id,
            eth_dst='90:e2:ba:24:a2:72',
            eth_src='00:00:00:11:22:33',
            ip_src='192.168.1.100',
            ip_dst='192.168.1.111'
        )

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
        verify_packet(self, str(pkt_from_p0_to_p1), ports[1])

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))
        verify_packet(self, str(pkt_from_p0_to_p2), ports[2])

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p3))
        verify_no_packet(self, str(pkt_from_p0_to_p3), ports[3])

        # delete segment
        response = requests.delete(URL+'v1/tenants/v1/{}/segments/{}'.format(tenant_name, segment_name), headers=GET_HEADER)
        self.assertEqual(200, response.status_code, 'Delete segment fail '+ response.text)

        # delete tenant
        response = requests.delete(URL+'v1/tenants/v1/{}'.format(tenant_name), headers=GET_HEADER)
        self.assertEqual(200, response.status_code, 'Delete tenant fail '+ response.text)

class SegmentVxlanTypeConnectionTest(base_tests.SimpleDataPlane):
    '''
    Test segment vxlan type connection.
    '''


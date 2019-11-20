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
import time
import utils
from telnetlib import Telnet

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}

def setup_configuration():
    for device in test_config.devices:
        if config_exists(device) == False:
            config_add(device)

def config_exists(device):
    response = requests.get(URL+"v1/devices/{}".format(device['id']), headers=GET_HEADER)

    if response.status_code == 404:
        return False
    elif response.status_code == 200:
        return True

def config_add(device):
    payload = {
        "id": device['id'],
        "name": device['name'],
        "type": device['type'],
        "available": "true",
        "mgmtIpAddress": device['mgmtIpAddress'],
        "mgmtPort": 0,
        "mac": device['mac'],
        "mfr": "Nocsys",
        "port": "80",
        "protocol": "rest",
        "rack_id": "1",
        "leaf_group": {
            "name": "",
            "switch_port": ""
        }
    }

    response = requests.post(URL+'v1/devices', json=payload, headers=POST_HEADER)
    assert response.status_code == 200, 'Add device fail! ' + response.text

def configure_spine(ip_address):
    command_list = [
        ("config", "(config)#"),
        ("vlan data", "(config-vlan)#"),
        ("vlan 100,200", "(config-vlan)#"),
        ("exit", "(config)#"),
        ("int vl 100", "(config-if)#"),
        ("ip add 192.168.100.2 255.255.255.0", "(config-if)#"),
        ("int vl 200", "(config-if)#"),
        ("ip add 192.168.200.2 255.255.255.0", "(config-if)#"),
        ("exit", "(config)#"),
        ("int eth 1/49", "(config-if)#"),
        ("switchport allowed vlan add 200 tagged", "(config-if)#"),
        ("int eth 1/50", "(config-if)#"),
        ("switchport allowed vlan add 100 tagged", "(config-if)#")
    ]

    telnet_and_execute(ip_address, command_list)

def configure_leaf(ip_address, src_if_vlan_id, access_vlan_id):
    command_list = [
        ("config", "(config)#"),
        ("vxlan source-interface vlan " + src_if_vlan_id, "(config)#"),
        ("vlan database", "(config-vlan)#"),
        ("vlan " + access_vlan_id, "(config-vlan)#"),
        ("exit", "(config)#"),
        ("int eth 1/48", "(config-if)#"),
        ("switchport allowed vlan add " + access_vlan_id + " untagged", "(config-if)#"),
    ]

    telnet_and_execute(ip_address, command_list)

def clear_configuration(access_vlan_id):
    clear_spine("192.168.40.147")
    clear_leaf("192.168.40.149", access_vlan_id)
    clear_leaf("192.168.40.150", access_vlan_id)

def clear_spine(ip_address):
    command_list = [
        ("config", "(config)#"),
        ("vlan data", "(config-vlan)#"),
        ("no vlan 100,200", "(config-vlan)#"),
    ]

    telnet_and_execute(ip_address, command_list)

def clear_leaf(ip_address, access_vlan_id):
    command_list = [
        ("config", "(config)#"),
        ("no vxlan source-interface vlan", "(config)#"),
        ("vlan database", "(config-vlan)#"),
        ("no vlan " + access_vlan_id, "(config-vlan)#"),
        ("exit", "(config)#"),
    ]

    telnet_and_execute(ip_address, command_list)

def telnet_and_execute(host_ip, cli_command_list, debug = False):
    tn = Telnet(host_ip)

    # login
    expect(tn, "Username:")
    send(tn, "admin")
    expect(tn, "Password:")
    send(tn, "admin")
    expect(tn, "#")

    if (debug):
        print ('\r\n')
        print ('telnet to : ' + host_ip)

    for (send_word, expect_word) in cli_command_list:
        if (debug):
            print (send_word, expect_word)

        send(tn, send_word)
        expect(tn, expect_word)

def send(tn, word):
   tn.write(word.encode('ascii') + b"\r\n")

def expect(tn, word):
   tn.read_until(word.encode('utf-8'))

class TenantsGetTest(base_tests.SimpleDataPlane):
    """
    Test tenant GET method
        - /v1/tenants/v1
    """

    def runTest(self):
        setup_configuration()

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
        setup_configuration()
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
        setup_configuration()
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
        setup_configuration()
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
    """
    Test segment vlan type connection.
    """

    def runTest(self):
        setup_configuration()
        utils.wait_for_system_stable()

        tenant_name = 't1'
        segment_name = 's1'
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
        response = requests.post(URL+'v1/tenants/v1/{}/segments/{}/device/{}/vlan'.format(tenant_name, segment_name, test_config.leaf0['id']),
            json=payload, headers=POST_HEADER)
        self.assertEqual(200, response.status_code, 'Add segment member fail '+ response.text)

        payload = {
            "ports" : ["46/tag"],
        }
        response = requests.post(URL+'v1/tenants/v1/{}/segments/{}/device/{}/vlan'.format(tenant_name, segment_name, test_config.leaf1['id']),
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
    """
    Test segment vxlan type connection.
    """

    def runTest(self):
        setup_configuration()
        utils.wait_for_system_stable()

        tenant_name = 't1'
        segment_name = 's1'
        uplink_segment_name = ['leaf0spine0', 'leaf1spine0']
        vlan_id = [200, 100]
        access_vlan_id = 20
        vni = 1000
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
            "type": "vxlan",
            "value": vni,
            "ip_address": [""]
        }
        response = requests.post(URL+'v1/tenants/v1/{}/segments'.format(tenant_name), json=payload, headers=POST_HEADER)
        self.assertEqual(200, response.status_code, 'Add segment fail! '+ response.text)

        # add uplink segment
        payload = [
            {
                "segment_name": uplink_segment_name[0],
                "device_id": test_config.leaf0['id'],
                "vlan": vlan_id[0],
                "ports": [
                    "49/tag"
                ],
                "gateway": "192.168.200.2",
                "gateway_mac": test_config.spine0['mac'],
                "ip_address": "192.168.200.1/24"
            },
            {
                "segment_name": uplink_segment_name[1],
                "device_id": test_config.leaf1['id'],
                "vlan": vlan_id[1],
                "ports": [
                    "49/tag"
                ],
                "gateway": "192.168.100.2",
                "gateway_mac": test_config.spine0['mac'],
                "ip_address": "192.168.100.1/24"
            }
        ]

        response = requests.post(URL+'topology/v1/uplink-segments', json=payload[0], headers=POST_HEADER)
        self.assertEqual(200, response.status_code, 'Add uplink segment fail! '+ response.text)

        response = requests.post(URL+'topology/v1/uplink-segments', json=payload[1], headers=POST_HEADER)
        self.assertEqual(200, response.status_code, 'Add uplink segment fail! '+ response.text)

        utils.wait_for_system_stable()

        # add access port and network port
        payload = [
            {
                "access_port": [
                    {
                    "name": "leaf0access",
                    "type": "normal",
                    "switch": test_config.leaf0['id'],
                    "port": 48,
                    "vlan": access_vlan_id
                    }
                ],
                "network_port": [
                    {
                    "name": "leaf0network",
                    "ip_addresses": [
                        "192.168.100.1"
                    ],
                    "uplink_segment": uplink_segment_name[0]
                    }
                ]
            },
            {
                "access_port": [
                    {
                    "name": "leaf1access",
                    "type": "normal",
                    "switch": test_config.leaf1['id'],
                    "port": 48,
                    "vlan": access_vlan_id
                    }
                ],
                "network_port": [
                    {
                    "name": "leaf1network",
                    "ip_addresses": [
                        "192.168.200.1"
                    ],
                    "uplink_segment": uplink_segment_name[1]
                    }
                ]
            }
        ]

        response = requests.post(URL+'v1/tenants/v1/{}/segments/{}/vxlan'.format(tenant_name, segment_name), json=payload[0], headers=POST_HEADER)
        self.assertEqual(200, response.status_code, 'Add access port and network port fail! '+ response.text)

        response = requests.post(URL+'v1/tenants/v1/{}/segments/{}/vxlan'.format(tenant_name, segment_name), json=payload[1], headers=POST_HEADER)
        self.assertEqual(200, response.status_code, 'Add access port and network port fail! '+ response.text)

        configure_spine(test_config.spine0['mgmtIpAddress'])
        configure_leaf(test_config.leaf0['mgmtIpAddress'], "200", str(access_vlan_id))
        configure_leaf(test_config.leaf1['mgmtIpAddress'], "100", str(access_vlan_id))

        utils.wait_for_system_stable()
        utils.wait_for_system_stable()

        pkt_from_p1_to_p3 = simple_tcp_packet(
            pktlen=100,
            dl_vlan_enable=True,
            vlan_vid=access_vlan_id,
            eth_dst='00:00:00:44:55:66',
            eth_src='00:00:00:11:22:33',
            ip_src='192.168.10.10',
            ip_dst='192.168.10.20'
        )

        self.dataplane.send(ports[1], str(pkt_from_p1_to_p3))
        verify_packet(self, str(pkt_from_p1_to_p3), ports[3])

        # delete uplink segment
        response = requests.delete(URL+'topology/v1/uplink-segments/{}'.format(uplink_segment_name[0]), headers=GET_HEADER)
        self.assertEqual(200, response.status_code, 'Delete uplink segment fail! '+ response.text)

        response = requests.delete(URL+'topology/v1/uplink-segments/{}'.format(uplink_segment_name[1]), headers=GET_HEADER)
        self.assertEqual(200, response.status_code, 'Delete uplink segment fail! '+ response.text)

        # delete segment
        response = requests.delete(URL+'v1/tenants/v1/{}/segments/{}'.format(tenant_name, segment_name), headers=GET_HEADER)
        self.assertEqual(200, response.status_code, 'Delete segment fail '+ response.text)

        # delete tenant
        response = requests.delete(URL+'v1/tenants/v1/{}'.format(tenant_name), headers=GET_HEADER)
        self.assertEqual(200, response.status_code, 'Delete tenant fail '+ response.text)

        clear_configuration(str(access_vlan_id))
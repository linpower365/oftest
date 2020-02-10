"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test Tenants RestAPI.

Test environment

    +--------+     +--------+
    | spine0 |     | spine1 |
    +--------+     +--------+
   49 |  | 50      49 |  | 50
      |  +------------+  |
   49 |  | 50      49 |  | 50
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
import config as cfg
import requests
import time
import utils
from utils import *

URL = cfg.API_BASE_URL
LOGIN = cfg.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}

class Tenants(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        self.port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)

    def port_configuration(self):
        cfg.leaf0['port46']  = (
            Port(cfg.leaf0['front_port'][0])
            .tagged(True)
            .nos(cfg.leaf0['nos'])
        )
        cfg.leaf0['port48'] = (
            Port(cfg.leaf0['front_port'][1])
            .tagged(True)
            .nos(cfg.leaf0['nos'])
        )
        cfg.leaf1['port46'] = (
            Port(cfg.leaf1['front_port'][0])
            .tagged(True)
            .nos(cfg.leaf1['nos'])
        )
        cfg.leaf1['port48'] = (
            Port(cfg.leaf1['front_port'][1])
            .tagged(True)
            .nos(cfg.leaf1['nos'])
        )

class TenantsGetTest(Tenants):
    """
    Test tenant GET method
        - /v1/tenants/v1
    """

    def runTest(self):
        response = requests.get(URL+"v1/tenants/v1", headers=GET_HEADER)
        assert(response.status_code == 200)

class TenantsAddNewTest(Tenants):
    """
    Test adding a new tenant and delete it
      - POST v1/tenants/v1
      - DELETE v1/tenants/v1/{tenant_name}
      - GET v1/tenants/v1
    """

    def runTest(self):
        tenant_name = 't1'
        t1 = (
            Tenant(tenant_name)
            .build()
        )

        # query tenants
        response = requests.get(URL + 'v1/tenants/v1', headers=GET_HEADER)
        assert(response.status_code == 200)
        found = False
        for t in response.json()['tenants']:
            if t['name'] == tenant_name:
                found = True
                break
        assert(found)

        t1.destroy()

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


class SegmentTest(Tenants):
    """
    Test Tenant Segment RestAPI
    - POST v1/tenants/v1/<tenant_name>/segments
    - GET v1/tenants/v1/segments
    - GET v1/tenants/v1/<tenant_name>/segments/<segment_name>
    - DELETE v1/tenants/v1/<tenant_name>/segments/<segment_name>
    """

    def runTest(self):
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
class LargeScaleTest(Tenants):
    """
    - Test 4K tenant each 1 segment
    - Test 1 tenant and 4k segment
    """

    def runTest(self):
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


class SegmentVlanTypeConnectionTest(Tenants):
    """
    Test segment vlan type connection.
    """

    def runTest(self):
        vlan_id = 3000
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', ['192.168.1.1'], vlan_id)
            .segment_member('s1', [cfg.leaf0['port46'].name, cfg.leaf0['port48'].name], cfg.leaf0['id'])
            .segment_member('s1', [cfg.leaf1['port46'].name], cfg.leaf1['id'])
            .build()
        )

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

        t1.delete_segment('s1')
        t1.destroy()


class SegmentVlanTypeRecoveryTest(Tenants):
    '''
    Test segment vlan type recovery feature.
    '''

    def runTest(self):
        vlan_id = 1000
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', ['192.168.1.1'], vlan_id)
            .segment_member('s1', [cfg.leaf0['port46'].name, cfg.leaf0['port48'].name], cfg.leaf0['id'])
            .segment_member('s1', [cfg.leaf1['port46'].name], cfg.leaf1['id'])
            .build()
        )

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

        # disconnect between spine0 and leaf1
        spine0_port_50 = DevicePort(50, cfg.spine0['id'])
        spine0_port_50.link_down()

        utils.wait_for_system_stable()

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
        verify_packet(self, str(pkt_from_p0_to_p1), ports[1])

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))
        verify_packet(self, str(pkt_from_p0_to_p2), ports[2])

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p3))
        verify_no_packet(self, str(pkt_from_p0_to_p3), ports[3])

        # resume connection between spine0 and leaf1
        spine0_port_50.link_up()

        # disconnection between spine1 and leaf1
        spine1_port_50 = DevicePort(50, cfg.spine1['id'])
        spine1_port_50.link_down()

        utils.wait_for_system_stable()

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
        verify_packet(self, str(pkt_from_p0_to_p1), ports[1])

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))
        verify_packet(self, str(pkt_from_p0_to_p2), ports[2])

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p3))
        verify_no_packet(self, str(pkt_from_p0_to_p3), ports[3])

        # resume connection between spine1 and leaf1
        spine1_port_50.link_up()

        t1.destroy()

        wait_for_system_stable()

class SegmentVxlanTypeConnectionTest(Tenants):
    """
    Test segment vxlan type connection.
    """

    def runTest(self):
        access_vlan_id_pairs_list = [(20, 20), (20, 30)]
        for leaf0_access_vlan_id, leaf1_access_vlan_id in access_vlan_id_pairs_list:
            setup_configuration()

            uplink_segment_name = ['leaf0spine0', 'leaf1spine0']
            access_vlan_id = 20
            vni = 1000
            ports = sorted(config["port_map"].keys())

            uplink_segment_leaf0spine0 = (
                UplinkSegment('leaf0spine0')
                .device_id(cfg.leaf0['id'])
                .vlan(200)
                .ports(["49/tag"])
                .gateway("192.168.200.2")
                .gateway_mac(cfg.spine0['mac'])
                .ip_address("192.168.200.1/24")
                .build()
            )

            uplink_segment_leaf1spine0 = (
                UplinkSegment('leaf1spine0')
                .device_id(cfg.leaf1['id'])
                .vlan(100)
                .ports(["49/tag"])
                .gateway("192.168.100.2")
                .gateway_mac(cfg.spine0['mac'])
                .ip_address("192.168.100.1/24")
                .build()
            )

            utils.wait_for_system_stable()

            t1 = (
                Tenant('t1')
                .segment('s1', 'vxlan', [], vni)
                .access_port('s1', 'leaf0access', cfg.leaf0['id'], 48, leaf0_access_vlan_id)
                .access_port('s1', 'leaf1access', cfg.leaf1['id'], 48, leaf1_access_vlan_id)
                .network_port('s1', 'leaf0network', ['192.168.100.1'], uplink_segment_name[0])
                .network_port('s1', 'leaf1network', ['192.168.200.1'], uplink_segment_name[1])
                .build()
            )

            utils.wait_for_system_stable()
            # utils.wait_for_system_stable()

            configure_spine(cfg.spine0['mgmtIpAddress'])
            configure_leaf(cfg.leaf0['mgmtIpAddress'], "200", str(leaf0_access_vlan_id))
            configure_leaf(cfg.leaf1['mgmtIpAddress'], "100", str(leaf1_access_vlan_id))

            utils.wait_for_system_stable()

            pkt_from_p1_to_p3 = simple_tcp_packet(
                pktlen=100,
                dl_vlan_enable=True,
                vlan_vid=leaf0_access_vlan_id,
                eth_dst='00:00:00:44:55:66',
                eth_src='00:00:00:11:22:33',
                ip_src='192.168.10.10',
                ip_dst='192.168.10.20'
            )

            # TODO: check test procedure for vlan 30
            if leaf1_access_vlan_id == 30:
                for i in range(5):
                    self.dataplane.send(ports[1], str(pkt_from_p1_to_p3))
                    wait_for_system_process()
                    print i
            else:
                self.dataplane.send(ports[1], str(pkt_from_p1_to_p3))

            verify_packet(self, str(pkt_from_p1_to_p3), ports[3])

            uplink_segment_leaf0spine0.destroy()
            uplink_segment_leaf1spine0.destroy()

            t1.delete_segment('s1')
            t1.destroy()

            clear_spine_configuration(cfg.spine0['mgmtIpAddress'])
            clear_leaf_configuration(cfg.leaf0['mgmtIpAddress'], str(leaf0_access_vlan_id))
            clear_leaf_configuration(cfg.leaf1['mgmtIpAddress'], str(leaf1_access_vlan_id))

            # clear queue packet
            self.dataplane.flush()

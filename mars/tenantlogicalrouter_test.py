"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test TenantLogicalRouter RestAPI.
"""


import oftest.base_tests as base_tests
import config as test_config
import requests
import time
import utils
from oftest import config
from oftest.testutils import *
from utils import *

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}

class TenantLogicalRouter(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)

class TenantLogicalRouterGetTest(TenantLogicalRouter):
    """
    Test tenantlogicalrouter GET method
        - /tenantlogicalrouter/v1
    """

    def runTest(self):
        response = requests.get(URL+"tenantlogicalrouter/v1", headers=GET_HEADER)
        assert(response.status_code == 200)
        

class TenantLogicalRouterAddNewTest(TenantLogicalRouter):
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


class TenantLogicalRouterNotExistTest(TenantLogicalRouter):
    """
    Test not exist data
    """
    def runTest(self):
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


class MisEnvironmentWithTwoSegmentsTest(TenantLogicalRouter):
    """
    Test MIS environment's connection with 2 segments
    """

    def runTest(self):
        s1_vlan_id = 10
        s2_vlan_id = 20
        ports = sorted(config["port_map"].keys())

        t1 = (
            tenant('t1')
            .segment('s1', 'vlan', ['192.168.10.1'], s1_vlan_id)
            .segment_member('s1', ['46/untag'], test_config.leaf0['id'])
            .segment('s2', 'vlan', ['192.168.20.1'], s2_vlan_id)
            .segment_member('s2', ['48/untag'], test_config.leaf0['id'])
            .segment_member('s2', ['46/untag', '48/untag'], test_config.leaf1['id'])
            .build()
        )

        # send arp reply to leaf0's p1
        host1_arp_reply = simple_arp_packet(
            eth_dst=test_config.leaf0['mac'],
            eth_src=test_config.host1['mac'],
            vlan_vid=s2_vlan_id,
            vlan_pcp=0,
            arp_op=2,
            ip_snd='192.168.20.20',
            ip_tgt='192.168.20.1',
            hw_snd=test_config.host1['mac'],
            hw_tgt=test_config.leaf0['mac'],
        )

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.leaf0['mac'],
            eth_src='00:00:00:11:22:33',
            ip_dst='192.168.20.20',
            ip_src='192.168.10.10'
        )

        # make leaf0 generate arp entry
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
        utils.wait_for_system_process()
        self.dataplane.send(ports[1], str(host1_arp_reply))

        # test connection from p0 to p1
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))

        pkt_rcv_from_p0_to_p1 = simple_packet(
            '00 00 01 00 00 02 8c ea 1b 8d 0e 3e 08 00 45 00 '
            '00 32 00 01 00 00 3f 06 dc 56 c0 a8 0a 0a c0 a8 '
            '14 14 04 d2 00 50 00 00 00 00 00 00 00 00 50 02 '
            '20 00 95 f2 00 00 44 44 44 44 44 44 44 44 44 44 '
        )

        verify_packet(self, str(pkt_rcv_from_p0_to_p1), ports[1])

        # send arp reply to leaf1's p2
        host2_arp_reply = simple_arp_packet(
            eth_dst=test_config.leaf1['mac'],
            eth_src=test_config.host2['mac'],
            vlan_vid=s2_vlan_id,
            vlan_pcp=0,
            arp_op=2,
            ip_snd='192.168.20.30',
            ip_tgt='192.168.20.1',
            hw_snd=test_config.host2['mac'],
            hw_tgt=test_config.leaf1['mac'],
        )

        pkt_from_p0_to_p2 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.leaf1['mac'],
            eth_src='00:00:00:11:22:33',
            ip_dst='192.168.20.30',
            ip_src='192.168.10.10'
        )

        # make leaf1 generate arp entry
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))
        utils.wait_for_system_process()
        self.dataplane.send(ports[2], str(host2_arp_reply))

        # test connection from p0 to p2
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))

        pkt_rcv_from_p0_to_p2 = simple_packet(
            '00 00 01 00 00 03 8c ea 1b 9b a4 30 08 00 45 00 '
            '00 32 00 01 00 00 3f 06 dc 4c c0 a8 0a 0a c0 a8 '
            '14 1e 04 d2 00 50 00 00 00 00 00 00 00 00 50 02 '
            '20 00 95 e8 00 00 44 44 44 44 44 44 44 44 44 44 '
        )

        verify_packet(self, str(pkt_rcv_from_p0_to_p2), ports[2])

        t1.destroy()

        reconnect_switch_port(test_config.leaf0['mgmtIpAddress'], '1/48')
        reconnect_switch_port(test_config.leaf1['mgmtIpAddress'], '1/46')

class MisEnvironmentWithThreeSegmentsTest(TenantLogicalRouter):
    """
    Test MIS environment's connection with 3 segments
    """

    def runTest(self):
        s1_vlan_id = 10
        s2_vlan_id = 20
        s3_vlan_id = 30
        ports = sorted(config["port_map"].keys())

        t1 = (
            tenant('t1')
            .segment('s1', 'vlan', ['192.168.10.1'], s1_vlan_id)
            .segment_member('s1', ['46/untag'], test_config.leaf0['id'])
            .segment('s2', 'vlan', ['192.168.20.1'], s2_vlan_id)
            .segment_member('s2', ['48/untag'], test_config.leaf0['id'])
            .segment_member('s2', ['46/untag'], test_config.leaf1['id'])
            .segment('s3', 'vlan', ['192.168.30.1'], s3_vlan_id)
            .segment_member('s3', ['48/untag'], test_config.leaf1['id'])
            .build()
        )

        # send arp reply to leaf0's p1
        host1_arp_reply = simple_arp_packet(
            eth_dst=test_config.leaf0['mac'],
            eth_src=test_config.host1['mac'],
            vlan_vid=s2_vlan_id,
            vlan_pcp=0,
            arp_op=2,
            ip_snd='192.168.20.20',
            ip_tgt='192.168.20.1',
            hw_snd=test_config.host1['mac'],
            hw_tgt=test_config.leaf0['mac'],
        )

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.leaf0['mac'],
            eth_src='00:00:00:11:22:33',
            ip_dst='192.168.20.20',
            ip_src='192.168.10.10'
        )

        # make leaf0 generate arp entry
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
        utils.wait_for_system_process()
        self.dataplane.send(ports[1], str(host1_arp_reply))

        # test connection from p0 to p1
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))

        pkt_rcv_from_p0_to_p1 = simple_packet(
            '00 00 01 00 00 02 8c ea 1b 8d 0e 3e 08 00 45 00 '
            '00 32 00 01 00 00 3f 06 dc 56 c0 a8 0a 0a c0 a8 '
            '14 14 04 d2 00 50 00 00 00 00 00 00 00 00 50 02 '
            '20 00 95 f2 00 00 44 44 44 44 44 44 44 44 44 44 '
        )

        verify_packet(self, str(pkt_rcv_from_p0_to_p1), ports[1])

        # send arp reply to leaf1's p2
        host2_arp_reply = simple_arp_packet(
            eth_dst=test_config.leaf1['mac'],
            eth_src=test_config.host2['mac'],
            vlan_vid=s2_vlan_id,
            vlan_pcp=0,
            arp_op=2,
            ip_snd='192.168.20.30',
            ip_tgt='192.168.20.1',
            hw_snd=test_config.host2['mac'],
            hw_tgt=test_config.leaf1['mac'],
        )

        pkt_from_p0_to_p2 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.leaf1['mac'],
            eth_src='00:00:00:11:22:33',
            ip_dst='192.168.20.30',
            ip_src='192.168.10.10'
        )

        # make leaf1 generate arp entry
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))
        utils.wait_for_system_process()
        self.dataplane.send(ports[2], str(host2_arp_reply))

        # test connection from p0 to p2
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))

        pkt_rcv_from_p0_to_p2 = simple_packet(
            '00 00 01 00 00 03 8c ea 1b 9b a4 30 08 00 45 00 '
            '00 32 00 01 00 00 3f 06 dc 4c c0 a8 0a 0a c0 a8 '
            '14 1e 04 d2 00 50 00 00 00 00 00 00 00 00 50 02 '
            '20 00 95 e8 00 00 44 44 44 44 44 44 44 44 44 44 '
        )

        verify_packet(self, str(pkt_rcv_from_p0_to_p2), ports[2])

        # send arp reply to leaf1's p3
        host3_arp_reply = simple_arp_packet(
            eth_dst=test_config.leaf1['mac'],
            eth_src=test_config.host3['mac'],
            vlan_vid=s3_vlan_id,
            vlan_pcp=0,
            arp_op=2,
            ip_snd='192.168.30.10',
            ip_tgt='192.168.30.1',
            hw_snd=test_config.host3['mac'],
            hw_tgt=test_config.leaf1['mac'],
        )

        pkt_from_p0_to_p3 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.leaf1['mac'],
            eth_src='00:00:00:11:22:33',
            ip_dst='192.168.30.10',
            ip_src='192.168.10.10'
        )

        # make leaf1 generate arp entry
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p3))
        utils.wait_for_system_process()
        self.dataplane.send(ports[3], str(host3_arp_reply))

        # test connection from p0 to p3
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p3))

        pkt_rcv_from_p0_to_p3 = simple_packet(
            '00 00 01 00 00 04 8c ea 1b 9b a4 30 08 00 45 00 '
            '00 32 00 01 00 00 3f 06 d2 60 c0 a8 0a 0a c0 a8 '
            '1e 0a 04 d2 00 50 00 00 00 00 00 00 00 00 50 02 '
            '20 00 8b fc 00 00 44 44 44 44 44 44 44 44 44 44 '
        )

        verify_packet(self, str(pkt_rcv_from_p0_to_p3), ports[3])

        t1.destroy()

        reconnect_switch_port(test_config.leaf0['mgmtIpAddress'], '1/48')
        reconnect_switch_port(test_config.leaf1['mgmtIpAddress'], '1/46')
        reconnect_switch_port(test_config.leaf1['mgmtIpAddress'], '1/48')      
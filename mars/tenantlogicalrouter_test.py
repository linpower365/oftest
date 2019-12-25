"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test TenantLogicalRouter RestAPI.

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
      |    |         |    |
    host0 host1    host2 host3

p0: port 46 of leaf0
p1: port 48 of leaf0
p2: port 46 of leaf1
p3: port 48 of leaf1

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

class OneSegmentWithoutIPaddressInSameLeaf(TenantLogicalRouter):
    '''
    Test connection in a segment without IP address in same leaf
    '''

    def runTest(self):
        s1_vlan_id = 10
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [''], s1_vlan_id)
            .segment_member('s1', ['46/tag', '48/tag'], test_config.leaf0['id'])
            .build()
        )

        pkt_from_p0_to_p1 = str(simple_tcp_packet(
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
        ))

        self.dataplane.send(ports[0], pkt_from_p0_to_p1)
        verify_packet(self, pkt_from_p0_to_p1, ports[1])

class OneSegmentWithoutIPaddressInDifferentLeaf(TenantLogicalRouter):
    '''
    Test connection in a segment without IP address in different leaf
    '''

    def runTest(self):
        s1_vlan_id = 20
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [''], s1_vlan_id)
            .segment_member('s1', ['46/tag'], test_config.leaf0['id'])
            .segment_member('s1', ['46/tag'], test_config.leaf1['id'])
            .build()
        )

        pkt_from_p0_to_p2 = str(simple_tcp_packet(
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
        ))

        self.dataplane.send(ports[0], pkt_from_p0_to_p2)
        verify_packet(self, pkt_from_p0_to_p2, ports[2])

class TwoSegmentsInSameLeafSameTenant(TenantLogicalRouter):
    '''
    Test logical router with 2 segments in same leaf and same tenent
    '''

    def runTest(self):
        s1_vlan_id = 10
        s2_vlan_id = 20
        ports = sorted(config["port_map"].keys())
        segment_ip_list = [
            (['192.168.10.1'], ['192.168.20.1']),
            ([''], [''])
        ]

        for (s1_ip, s2_ip) in segment_ip_list:
            t1 = (
                Tenant('t1')
                .segment('s1', 'vlan', s1_ip, s1_vlan_id)
                .segment_member('s1', ['46/untag'], test_config.leaf0['id'])
                .segment('s2', 'vlan', s2_ip, s2_vlan_id)
                .segment_member('s2', ['48/untag'], test_config.leaf0['id'])
                .build()
            )

            if s1_ip != [''] and s2_ip != ['']:
                lrouter = (
                    LogicalRouter('r1', 't1')
                    .interfaces(['s1', 's2'])
                    .build()
                )

            test_config.host0['ip'] = '192.168.10.10'
            test_config.host1['ip'] = '192.168.20.20'

            configure_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, '1/49', s1_vlan_id)

            pkt_from_p0_to_p1 = simple_tcp_packet(
                pktlen=68,
                dl_vlan_enable=True,
                vlan_vid=s1_vlan_id,
                eth_dst=test_config.spine0['mac'],
                eth_src=test_config.host0['mac'],
                ip_dst=test_config.host1['ip'],
                ip_src=test_config.host0['ip']
            )

            # check connection between 2 segments
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))

            pkt_expected = simple_tcp_packet(
                pktlen=64,
                eth_dst=test_config.host1['mac'],
                eth_src=test_config.spine0['mac'],
                ip_dst=test_config.host1['ip'],
                ip_src=test_config.host0['ip'],
                ip_ttl=63
            )

            if s1_ip == [''] and s2_ip == ['']:
                verify_no_packet(self, str(pkt_expected), ports[1])
            else:
                verify_packet(self, str(pkt_expected), ports[1])

            t1.destroy()
            lrouter.destroy()

            remove_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, s1_vlan_id)

            # clear queue packet
            self.dataplane.flush()

class TwoSegmentsInDifferentLeafSameTenent(TenantLogicalRouter):
    '''
    Test logical router with 2 segments in different leaf and same tenent
    '''

    def runTest(self):
        s1_vlan_id = 10
        s2_vlan_id = 20
        ports = sorted(config["port_map"].keys())
        segment_ip_list = [
            (['192.168.10.1'], ['192.168.20.1']),
            ([''], [''])
        ]

        for (s1_ip, s2_ip) in segment_ip_list:
            t1 = (
                Tenant('t1')
                .segment('s1', 'vlan', s1_ip, s1_vlan_id)
                .segment_member('s1', ['46/untag'], test_config.leaf0['id'])
                .segment('s2', 'vlan', s2_ip, s2_vlan_id)
                .segment_member('s2', ['46/untag'], test_config.leaf1['id'])
                .build()
            )

            if s1_ip != [''] and s2_ip != ['']:
                lrouter = (
                    LogicalRouter('r1', 't1')
                    .interfaces(['s1', 's2'])
                    .build()
                )

            test_config.host0['ip'] = '192.168.10.30'
            test_config.host2['ip'] = '192.168.20.30'

            configure_arp(test_config.spine0['mgmtIpAddress'], test_config.host2, '1/50', s2_vlan_id)

            pkt_from_p0_to_p2 = simple_tcp_packet(
                pktlen=68,
                dl_vlan_enable=True,
                vlan_vid=s1_vlan_id,
                eth_dst=test_config.spine0['mac'],
                eth_src=test_config.host0['mac'],
                ip_dst=test_config.host2['ip'],
                ip_src=test_config.host0['ip']
            )

            # check connection between 2 segments
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))

            pkt_expected = simple_tcp_packet(
                pktlen=64,
                eth_dst=test_config.host2['mac'],
                eth_src=test_config.spine0['mac'],
                ip_dst=test_config.host2['ip'],
                ip_src=test_config.host0['ip'],
                ip_ttl=63
            )

            if s1_ip == [''] and s2_ip == ['']:
                verify_no_packet(self, str(pkt_expected), ports[2])
            else:
                verify_packet(self, str(pkt_expected), ports[2])

            t1.destroy()
            lrouter.destroy()

            remove_arp(test_config.spine0['mgmtIpAddress'], test_config.host2, s2_vlan_id)

            # clear queue packet
            self.dataplane.flush()

class TwoSegmentsInSameLeafDifferentTenantWithoutSystemTenant(TenantLogicalRouter):
    '''
    Test logical router with 2 segments in same leaf and different tenent.
    Without system tenant configuration.
    '''

    def runTest(self):
        s1_vlan_id = 10
        s2_vlan_id = 20
        s1_ip = '192.168.10.1'
        s2_ip = '192.168.20.1'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], s1_vlan_id)
            .segment_member('s1', ['46/untag'], test_config.leaf0['id'])
            .build()
        )

        t2 = (
            Tenant('t2')
            .segment('s2', 'vlan', [s2_ip], s2_vlan_id)
            .segment_member('s2', ['48/untag'], test_config.leaf0['id'])
            .build()
        )

        test_config.host0['ip'] = '192.168.10.30'
        test_config.host1['ip'] = '192.168.20.30'

        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, '1/49', s2_vlan_id)

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.spine0['mac'],
            eth_src=test_config.host0['mac'],
            ip_dst=test_config.host1['ip'],
            ip_src=test_config.host0['ip']
        )

        # check connection between 2 segments
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))

        pkt_expected = simple_tcp_packet(
            pktlen=64,
            eth_dst=test_config.host1['mac'],
            eth_src=test_config.spine0['mac'],
            ip_dst=test_config.host1['ip'],
            ip_src=test_config.host0['ip'],
            ip_ttl=63
        )

        # no system tenant created, can not communicate with different tenants
        verify_no_packet(self, str(pkt_expected), ports[1])

        t1.destroy()
        t2.destroy()

        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.host2, s2_vlan_id)

class TwoSegmentsInSameLeafDifferentTenantWithSystemTenant(TenantLogicalRouter):
    '''
    Test logical router with 2 segments in same leaf and different tenent.
    With system tenant configuration.
    '''

    def tearDown(self):
        TenantLogicalRouter.tearDown(self)
        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, 20)

    def runTest(self):
        s1_vlan_id = 10
        s2_vlan_id = 20
        s1_ip = '192.168.10.1'
        s2_ip = '192.168.20.1'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], s1_vlan_id)
            .segment_member('s1', ['46/untag'], test_config.leaf0['id'])
            .build()
        )

        t2 = (
            Tenant('t2')
            .segment('s2', 'vlan', [s2_ip], s2_vlan_id)
            .segment_member('s2', ['48/untag'], test_config.leaf0['id'])
            .build()
        )

        system_tenant = (
            Tenant('system', 'System')
            .build()
        )

        lrouter_r1 = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1'])
            .build()
        )

        lrouter_r2 = (
            LogicalRouter('r2', 't2')
            .interfaces(['s2'])
            .build()
        )

        lrouter_system = (
            LogicalRouter('system')
            .tenant_routers(['t1/r1', 't2/r2'])
            .build()
        )

        test_config.host0['ip'] = '192.168.10.30'
        test_config.host1['ip'] = '192.168.20.30'

        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, '1/49', s2_vlan_id)

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.spine0['mac'],
            eth_src=test_config.host0['mac'],
            ip_dst=test_config.host1['ip'],
            ip_src=test_config.host0['ip']
        )

        # check connection between 2 segments
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))

        pkt_expected = simple_tcp_packet(
            pktlen=64,
            eth_dst=test_config.host1['mac'],
            eth_src=test_config.spine0['mac'],
            ip_dst=test_config.host1['ip'],
            ip_src=test_config.host0['ip'],
            ip_ttl=63
        )

        verify_packet(self, str(pkt_expected), ports[1])

        t1.destroy()
        t2.destroy()
        lrouter_r1.destroy()
        lrouter_r2.destroy()
        lrouter_system.destroy()
        system_tenant.destroy()

class TwoSegmentsInDifferentLeafDifferentTenantWithoutSystemTenant(TenantLogicalRouter):
    '''
    Test logical router with 2 segments in same leaf and different tenent.
    Without system tenant configuration.
    '''

    def runTest(self):
        s1_vlan_id = 10
        s2_vlan_id = 20
        s1_ip = '192.168.10.1'
        s2_ip = '192.168.20.1'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], s1_vlan_id)
            .segment_member('s1', ['46/untag'], test_config.leaf0['id'])
            .build()
        )

        t2 = (
            Tenant('t2')
            .segment('s2', 'vlan', [s2_ip], s2_vlan_id)
            .segment_member('s2', ['46/untag'], test_config.leaf1['id'])
            .build()
        )

        test_config.host0['ip'] = '192.168.10.30'
        test_config.host2['ip'] = '192.168.20.30'

        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, '1/50', s2_vlan_id)

        pkt_from_p0_to_p2 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.spine0['mac'],
            eth_src=test_config.host0['mac'],
            ip_dst=test_config.host2['ip'],
            ip_src=test_config.host0['ip']
        )

        # check connection between 2 segments
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))

        pkt_expected = simple_tcp_packet(
            pktlen=64,
            eth_dst=test_config.host2['mac'],
            eth_src=test_config.spine0['mac'],
            ip_dst=test_config.host2['ip'],
            ip_src=test_config.host0['ip'],
            ip_ttl=63
        )

        # no system tenant created, can not communicate with different tenants
        verify_no_packet(self, str(pkt_expected), ports[2])

        t1.destroy()
        t2.destroy()

        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, s2_vlan_id)

class TwoSegmentsInDifferentLeafDifferentTenantWithSystemTenant(TenantLogicalRouter):
    '''
    Test logical router with 2 segments in different leaf and different tenent.
    With system tenant configuration.
    '''

    def tearDown(self):
        TenantLogicalRouter.tearDown(self)
        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, 20)

    def runTest(self):
        s1_vlan_id = 10
        s2_vlan_id = 20
        s1_ip = '192.168.10.1'
        s2_ip = '192.168.20.1'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], s1_vlan_id)
            .segment_member('s1', ['46/untag'], test_config.leaf0['id'])
            .build()
        )

        t2 = (
            Tenant('t2')
            .segment('s2', 'vlan', [s2_ip], s2_vlan_id)
            .segment_member('s2', ['46/untag'], test_config.leaf1['id'])
            .build()
        )

        system_tenant = (
            Tenant('system', 'System')
            .build()
        )

        lrouter_r1 = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1'])
            .build()
        )

        lrouter_r2 = (
            LogicalRouter('r2', 't2')
            .interfaces(['s2'])
            .build()
        )

        lrouter_system = (
            LogicalRouter('system')
            .tenant_routers(['t1/r1', 't2/r2'])
            .build()
        )

        test_config.host0['ip'] = '192.168.10.30'
        test_config.host2['ip'] = '192.168.20.30'

        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.host2, '1/50', s2_vlan_id)

        pkt_from_p0_to_p2 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.spine0['mac'],
            eth_src=test_config.host0['mac'],
            ip_dst=test_config.host2['ip'],
            ip_src=test_config.host0['ip']
        )

        # check connection between 2 segments
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))

        pkt_expected = simple_tcp_packet(
            pktlen=64,
            eth_dst=test_config.host2['mac'],
            eth_src=test_config.spine0['mac'],
            ip_dst=test_config.host2['ip'],
            ip_src=test_config.host0['ip'],
            ip_ttl=63
        )

        # no system tenant created, can not communicate with different tenants
        verify_packet(self, str(pkt_expected), ports[2])

        lrouter_system.destroy()
        lrouter_r1.destroy()
        lrouter_r2.destroy()
        t1.destroy()
        t2.destroy()
        system_tenant.destroy()

class ExternalRouterTest(TenantLogicalRouter):
    '''
    Test logical router in external router environment
    '''

    def tearDown(self):
        TenantLogicalRouter.tearDown(self)
        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.external_router0, 50)

    def runTest(self):
        s1_vlan_id = 50
        s2_vlan_id = 60
        s1_ip = '192.168.50.1'
        s2_ip = '192.168.60.1'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], s1_vlan_id)
            .segment_member('s1', ['46/untag', '48/untag'], test_config.leaf0['id'])
            .segment('s2', 'vlan', [s2_ip], s2_vlan_id)
            .build()
        )

        wait_for_system_stable()

        test_config.host0['ip'] = '192.168.50.10'
        test_config.host1['ip'] = '10.10.10.10'
        test_config.external_router0['ip'] = '192.168.50.100'

        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.external_router0, '1/49', s1_vlan_id)

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .nexthop_group('n1', [test_config.external_router0['ip']])
            .static_route('static-r1', '10.10.10.1', 24, 'n1')
            .build()
        )

        wait_for_system_stable()
        wait_for_system_stable()

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.spine0['mac'],
            eth_src=test_config.host0['mac'],
            ip_dst=test_config.host1['ip'],
            ip_src=test_config.host0['ip']
        )

        # check connection between host0 and external_router0
        for i in range(5):
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
            wait_for_system_process()

        pkt_expected = simple_tcp_packet(
            pktlen=64,
            eth_dst=test_config.external_router0['mac'],
            eth_src=test_config.spine0['mac'],
            ip_dst=test_config.host1['ip'],
            ip_src=test_config.host0['ip'],
            ip_ttl=63
        )

        verify_packet(self, str(pkt_expected), ports[1])

        lrouter.destroy()
        t1.destroy()

        wait_for_system_process()

class PolicyRouteInSameLeafTest(TenantLogicalRouter):
    '''
    Test logical router with policy router configuration in same leaf
    '''

    def tearDown(self):
        TenantLogicalRouter.tearDown(self)
        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.external_router0, 50)

    def runTest(self):
        s1_vlan_id = 50
        s2_vlan_id = 60
        s1_ip = '192.168.50.1'
        s2_ip = '192.168.60.1'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], s1_vlan_id)
            .segment_member('s1', ['46/untag', '48/untag'], test_config.leaf0['id'])
            .segment('s2', 'vlan', [s2_ip], s2_vlan_id)
            .build()
        )

        wait_for_system_stable()

        test_config.host0['ip'] = '192.168.50.10'
        test_config.host1['ip'] = '10.10.10.10'
        test_config.external_router0['ip'] = '192.168.50.120'
        test_config.external_router0['mac'] = '00:00:02:00:00:11'

        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.external_router0, '1/49', s1_vlan_id)

        pr1 = (
            PolicyRoute('pr1')
            .ingress_segments(['s1'])
            .ingress_ports([
                '{}/{}'.format(test_config.leaf0['id'], 46)
                ])
            .action('permit')
            .sequence_no('1')
            .protocols(['tcp'])
            .match_ip('10.10.10.10/32')
            .nexthop(test_config.external_router0['ip'])
        )

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .policy_route(pr1)
            .build()
        )

        wait_for_system_stable()
        wait_for_system_stable()

        for dst_ip in [test_config.host1['ip'], '10.10.10.20']:
            pkt_from_p0_to_p1 = simple_tcp_packet(
                pktlen=68,
                dl_vlan_enable=True,
                vlan_vid=s1_vlan_id,
                eth_dst=test_config.spine0['mac'],
                eth_src=test_config.host0['mac'],
                ip_dst=dst_ip,
                ip_src=test_config.host0['ip']
            )

            # check connection between host0 and external_router0
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))

            pkt_expected = simple_tcp_packet(
                pktlen=64,
                eth_dst=test_config.external_router0['mac'],
                eth_src=test_config.spine0['mac'],
                ip_dst=dst_ip,
                ip_src=test_config.host0['ip'],
                ip_ttl=63
            )

            if dst_ip == test_config.host1['ip']:
                verify_packet(self, pkt_expected, ports[1])
            else:
                verify_no_packet(self, pkt_expected, ports[1])

            self.dataplane.flush()

        lrouter.destroy()
        t1.destroy()


class PolicyRouteInDifferentLeafTest(TenantLogicalRouter):
    '''
    Test logical router with policy router configuration in different leaf
    '''

    def tearDown(self):
        TenantLogicalRouter.tearDown(self)
        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.external_router0, 50)

    def runTest(self):
        s1_vlan_id = 50
        s2_vlan_id = 60
        s1_ip = '192.168.50.1'
        s2_ip = '192.168.60.1'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], s1_vlan_id)
            .segment_member('s1', ['46/untag'], test_config.leaf0['id'])
            .segment_member('s1', ['46/untag'], test_config.leaf1['id'])
            .segment('s2', 'vlan', [s2_ip], s2_vlan_id)
            .build()
        )

        wait_for_system_stable()

        test_config.host0['ip'] = '192.168.50.20'
        test_config.host2['ip'] = '10.10.10.20'
        test_config.external_router1['ip'] = '192.168.50.130'
        test_config.external_router1['mac'] = '00:00:02:00:00:22'

        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.external_router1, '1/50', s1_vlan_id)

        pr1 = (
            PolicyRoute('pr1')
            .ingress_segments(['s1'])
            .ingress_ports([
                '{}/{}'.format(test_config.leaf0['id'], 46)
                ])
            .action('permit')
            .sequence_no('1')
            .protocols(['udp'])
            .match_ip('10.10.10.20/32')
            .nexthop(test_config.external_router1['ip'])
        )

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .policy_route(pr1)
            .build()
        )

        wait_for_system_stable()
        wait_for_system_stable()

        for dst_ip in [test_config.host2['ip'], '10.10.10.50']:
            pkt_from_p0_to_p2 = simple_udp_packet(
                pktlen=68,
                dl_vlan_enable=True,
                vlan_vid=s1_vlan_id,
                eth_dst=test_config.spine0['mac'],
                eth_src=test_config.host0['mac'],
                ip_dst=dst_ip,
                ip_src=test_config.host0['ip']
            )

            # check connection between host0 and external_router0
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))

            pkt_expected = simple_udp_packet(
                pktlen=64,
                eth_dst=test_config.external_router1['mac'],
                eth_src=test_config.spine0['mac'],
                ip_dst=dst_ip,
                ip_src=test_config.host0['ip'],
                ip_ttl=63
            )

            if dst_ip == test_config.host2['ip']:
                verify_packet(self, pkt_expected, ports[2])
            else:
                verify_no_packet(self, pkt_expected, ports[2])

            self.dataplane.flush()

        lrouter.destroy()
        t1.destroy()


class MisEnvironmentWithTwoSegmentsTest(TenantLogicalRouter):
    """
    Test MIS environment's connection with 2 segments
    """

    def runTest(self):
        s1_vlan_id = 10
        s2_vlan_id = 20
        s1_ip = '192.168.10.1'
        s2_ip = '192.168.20.1'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], s1_vlan_id)
            .segment_member('s1', ['46/untag'], test_config.leaf0['id'])
            .segment('s2', 'vlan', [s2_ip], s2_vlan_id)
            .segment_member('s2', ['48/untag'], test_config.leaf0['id'])
            .segment_member('s2', ['46/untag', '48/untag'], test_config.leaf1['id'])
            .build()
        )

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .build()
        )

        test_config.host0['ip'] = '192.168.10.10'
        test_config.host1['ip'] = '192.168.20.20'

        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, '1/49', s2_vlan_id)

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.spine0['mac'],
            eth_src=test_config.host0['mac'],
            ip_dst=test_config.host1['ip'],
            ip_src=test_config.host0['ip']
        )

        # test connection from p0 to p1
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))

        pkt_expected = simple_tcp_packet(
            pktlen=64,
            eth_dst=test_config.host1['mac'],
            eth_src=test_config.spine0['mac'],
            ip_dst=test_config.host1['ip'],
            ip_src=test_config.host0['ip'],
            ip_ttl=63
        )

        verify_packet(self, str(pkt_expected), ports[1])

        test_config.host2['ip'] = '192.168.20.30'

        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.host2, '1/50', s2_vlan_id)

        pkt_from_p0_to_p2 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.spine0['mac'],
            eth_src=test_config.host0['mac'],
            ip_dst=test_config.host2['ip'],
            ip_src=test_config.host0['ip']
        )

        # test connection from p0 to p2
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))

        pkt_expected = simple_tcp_packet(
            pktlen=64,
            eth_dst=test_config.host2['mac'],
            eth_src=test_config.spine0['mac'],
            ip_dst=test_config.host2['ip'],
            ip_src=test_config.host0['ip'],
            ip_ttl=63
        )

        verify_packet(self, str(pkt_expected), ports[2])

        t1.destroy()
        lrouter.destroy()

        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, s2_vlan_id)
        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.host2, s2_vlan_id)

class MisEnvironmentWithThreeSegmentsTest(TenantLogicalRouter):
    """
    Test MIS environment's connection with 3 segments
    """

    def runTest(self):
        s1_vlan_id = 10
        s2_vlan_id = 20
        s3_vlan_id = 30
        s1_ip = '192.168.10.1'
        s2_ip = '192.168.20.1'
        s3_ip = '192.168.30.1'
        test_config.host0['ip'] = '192.168.10.10'
        test_config.host1['ip'] = '192.168.20.20'
        test_config.host2['ip'] = '192.168.20.30'
        test_config.host3['ip'] = '192.168.30.10'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], s1_vlan_id)
            .segment_member('s1', ['46/untag'], test_config.leaf0['id'])
            .segment('s2', 'vlan', [s2_ip], s2_vlan_id)
            .segment_member('s2', ['48/untag'], test_config.leaf0['id'])
            .segment_member('s2', ['46/untag'], test_config.leaf1['id'])
            .segment('s3', 'vlan', [s3_ip], s3_vlan_id)
            .segment_member('s3', ['48/untag'], test_config.leaf1['id'])
            .build()
        )

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2', 's3'])
            .build()
        )

        # case 1
        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, '1/49', s2_vlan_id)

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.spine0['mac'],
            eth_src=test_config.host0['mac'],
            ip_dst=test_config.host1['ip'],
            ip_src=test_config.host0['ip']
        )

        pkt_expected_for_host1 = simple_tcp_packet(
            pktlen=64,
            eth_dst=test_config.host1['mac'],
            eth_src=test_config.spine0['mac'],
            ip_dst=test_config.host1['ip'],
            ip_src=test_config.host0['ip'],
            ip_ttl=63
        )

        # case 2
        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.host2, '1/50', s2_vlan_id)

        pkt_from_p0_to_p2 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.spine0['mac'],
            eth_src=test_config.host0['mac'],
            ip_dst=test_config.host2['ip'],
            ip_src=test_config.host0['ip']
        )

        pkt_expected_for_host2 = simple_tcp_packet(
            pktlen=64,
            eth_dst=test_config.host2['mac'],
            eth_src=test_config.spine0['mac'],
            ip_dst=test_config.host2['ip'],
            ip_src=test_config.host0['ip'],
            ip_ttl=63
        )

        # case 3
        configure_arp(test_config.spine0['mgmtIpAddress'], test_config.host3, '1/50', s3_vlan_id)

        pkt_from_p0_to_p3 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=test_config.spine0['mac'],
            eth_src=test_config.host0['mac'],
            ip_dst=test_config.host3['ip'],
            ip_src=test_config.host0['ip']
        )

        pkt_expected_for_host3 = simple_tcp_packet(
            pktlen=64,
            eth_dst=test_config.host3['mac'],
            eth_src=test_config.spine0['mac'],
            ip_dst=test_config.host3['ip'],
            ip_src=test_config.host0['ip'],
            ip_ttl=63
        )

        # test connection between host0 and the ohter hosts
        case_list = [
            (pkt_from_p0_to_p1, pkt_expected_for_host1, ports[1]),
            (pkt_from_p0_to_p2, pkt_expected_for_host2, ports[2]),
            (pkt_from_p0_to_p3, pkt_expected_for_host3, ports[3])
        ]

        for (pkt_from_p0, pkt_expected, verify_port) in case_list:
            self.dataplane.send(ports[0], str(pkt_from_p0))
            verify_packet(self, str(pkt_expected), verify_port)

        t1.destroy()
        lrouter.destroy()

        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.host1, s2_vlan_id)
        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.host2, s2_vlan_id)
        remove_arp(test_config.spine0['mgmtIpAddress'], test_config.host3, s3_vlan_id)

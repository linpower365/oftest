"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test DHCP relay RestAPI.

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

p0: port A of leaf0
p1: port B of leaf0
p2: port A of leaf1
p3: port B of leaf1

"""

import oftest.base_tests as base_tests
import config as cfg
import requests
import time
import utils
from oftest import config
from oftest.testutils import *
from utils import *
# from oftest.packet import *
from scapy.layers.l2 import *
from scapy.layers.inet import *
from scapy.layers.dhcp import *


class DHCPRelayTest(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)


class SetterAndGetter(DHCPRelayTest):
    """
    Test DHCP relay set and get api
    """

    def runTest(self):

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', ['192.168.50.1'], '50')
            .build()
        )

        dhcp_relay = (
            DHCPRelay('t1', 's1')
            .servers(['192.168.200.10'])
            .build()
        )

        actual_dhcp_relay = dhcp_relay.get_content()
        assert(dhcp_relay._tenant ==
               actual_dhcp_relay['dhcpRelayServers'][0]['tenant'])
        assert(dhcp_relay._segment ==
               actual_dhcp_relay['dhcpRelayServers'][0]['segment'])
        assert(dhcp_relay._servers_list ==
               actual_dhcp_relay['dhcpRelayServers'][0]['servers'])


class TransmitPacket(DHCPRelayTest):
    """
    Test DHCP relay transimit packet
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        case_item_list = [
            # s1_vlan_id s2_vlan_id  s1_vlan_ip       s2_vlan_ip         dhcp_server_ip      allocated_ip
            (50,        100,        '192.168.50.1', '192.168.100.1',
             '192.168.100.20',   '192.168.50.51'),
            (60,        200,        '192.168.60.1',
             '192.168.200.1',    '192.168.200.20',   '192.168.60.51')
        ]

        for case_item in case_item_list:
            s1_vlan_id = case_item[0]
            s2_vlan_id = case_item[1]
            s1_vlan_ip = case_item[2]
            s2_vlan_ip = case_item[3]
            dhcp_server_ip = case_item[4]
            allocated_ip = case_item[5]

            t1 = (
                Tenant('t1')
                .segment('s1', 'vlan', [s1_vlan_ip], s1_vlan_id)
                .segment_member(SegmentMember('s1', cfg.leaf0['id']).ports([cfg.leaf0['portA'].name]))
                .segment('s2', 'vlan', [s2_vlan_ip], s2_vlan_id)
                .segment_member(SegmentMember('s2', cfg.leaf1['id']).ports([cfg.leaf1['portA'].name, cfg.leaf1['portB'].name]))
                .build()
            )

            lrouter = (
                LogicalRouter('r1', 't1')
                .interfaces(['s1', 's2'])
                .build()
            )

            dhcp_relay = (
                DHCPRelay('t1', 's1')
                .servers([dhcp_server_ip])
                .build()
            )

            cfg.dhcp_server['ip'] = dhcp_server_ip

            spine = get_master_spine(
                self.dataplane, cfg.dhcp_server, s1_vlan_ip, ports[3])
            send_icmp_echo_request(
                self.dataplane, cfg.dhcp_server, spine, s2_vlan_ip, ports[3])

            dhcp_pkt = DHCP_PKT()

            # verify dhcp discover
            dhcp_discover = dhcp_pkt.generate_discover_pkt(cfg.host0)
            expected_dhcp_discover = dhcp_pkt.generate_expected_discover_pkt(
                spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s2_vlan_ip)

            self.dataplane.send(ports[0], str(dhcp_discover))
            verify_packet(self, str(expected_dhcp_discover), ports[3])

            # verify dhcp offer
            dhcp_offer = dhcp_pkt.generate_offer_pkt(
                spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
            expected_dhcp_offer = dhcp_pkt.generate_expected_offer_pkt(
                spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)

            self.dataplane.send(ports[3], str(dhcp_offer))
            verify_packet(self, str(expected_dhcp_offer), ports[0])

            # verify dhcp request
            dhcp_request = dhcp_pkt.generate_request_pkt(
                cfg.dhcp_server, cfg.host0, allocated_ip)
            expected_dhcp_request = dhcp_pkt.generate_expected_request_pkt(
                spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s2_vlan_ip, allocated_ip)

            self.dataplane.send(ports[0], str(dhcp_request))
            verify_packet(self, str(expected_dhcp_request), ports[3])

            # verify dhcp ack
            dhcp_ack = dhcp_pkt.generate_ack_pkt(
                spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
            expected_dhcp_ack = dhcp_pkt.generate_expected_ack_pkt(
                spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)

            self.dataplane.send(ports[3], str(dhcp_ack))
            verify_packet(self, str(expected_dhcp_ack), ports[0])

            dhcp_relay.destroy()
            lrouter.destroy()
            t1.destroy()

            # clear queue packet
            self.dataplane.flush()

            wait_for_system_stable()


class MultipleServer(DHCPRelayTest):
    """
    Test DHCP relay with multiple server
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        s1_vlan_id = 50
        s2_vlan_id = 100
        s1_vlan_ip = '192.168.50.1'
        s2_vlan_ip = '192.168.100.1'
        allocated_ip = '192.168.50.51'

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_vlan_ip], s1_vlan_id)
            .segment_member(SegmentMember('s1', cfg.leaf0['id']).ports([cfg.leaf0['portA'].name]))
            .segment('s2', 'vlan', [s2_vlan_ip], s2_vlan_id)
            .segment_member(SegmentMember('s2', cfg.leaf1['id']).ports([cfg.leaf1['portA'].name, cfg.leaf1['portB'].name]))
            .build()
        )

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .build()
        )

        dhcp_relay = (
            DHCPRelay('t1', 's1')
            .servers(['192.168.100.20', '192.168.100.30', '192.168.100.40'])
            .build()
        )

        cfg.dhcp_server['ip'] = '192.168.100.20'

        spine = get_master_spine(
            self.dataplane, cfg.dhcp_server, s1_vlan_ip, ports[3])
        send_icmp_echo_request(
            self.dataplane, cfg.dhcp_server, spine, s2_vlan_ip, ports[3])

        dhcp_pkt = DHCP_PKT()

        # verify dhcp discover
        dhcp_discover = dhcp_pkt.generate_discover_pkt(cfg.host0)
        expected_dhcp_discover = dhcp_pkt.generate_expected_discover_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s2_vlan_ip)

        self.dataplane.send(ports[0], str(dhcp_discover))
        verify_packet(self, str(expected_dhcp_discover), ports[3])

        # verify dhcp offer
        dhcp_offer = dhcp_pkt.generate_offer_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        expected_dhcp_offer = dhcp_pkt.generate_expected_offer_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)

        self.dataplane.send(ports[3], str(dhcp_offer))
        verify_packet(self, str(expected_dhcp_offer), ports[0])

        # verify dhcp request
        dhcp_request = dhcp_pkt.generate_request_pkt(
            cfg.dhcp_server, cfg.host0, allocated_ip)
        expected_dhcp_request = dhcp_pkt.generate_expected_request_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s2_vlan_ip, allocated_ip)

        self.dataplane.send(ports[0], str(dhcp_request))
        verify_packet(self, str(expected_dhcp_request), ports[3])

        # verify dhcp ack
        dhcp_ack = dhcp_pkt.generate_ack_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        expected_dhcp_ack = dhcp_pkt.generate_expected_ack_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)

        self.dataplane.send(ports[3], str(dhcp_ack))
        verify_packet(self, str(expected_dhcp_ack), ports[0])

        dhcp_relay.destroy()
        lrouter.destroy()
        t1.destroy()


class CrossSystemTenant(DHCPRelayTest):
    """
    Test DHCP relay cross system tenant
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        s1_vlan_id = 50
        s2_vlan_id = 100
        s3_vlan_id = 60
        s4_vlan_id = 200
        s1_vlan_ip = '192.168.50.1'
        s2_vlan_ip = '192.168.100.1'
        s3_vlan_ip = '192.168.60.1'
        s4_vlan_ip = '192.168.200.1'
        dhcp_server_ip = '192.168.200.10'
        allocated_ip = '192.168.50.51'

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_vlan_ip], s1_vlan_id)
            .segment_member(SegmentMember('s1', cfg.leaf0['id']).ports([cfg.leaf0['portA'].name]))
            .segment('s2', 'vlan', [s2_vlan_ip], s2_vlan_id)
            .segment_member(SegmentMember('s2', cfg.leaf0['id']).ports([cfg.leaf0['portB'].name]))
            .build()
        )

        t2 = (
            Tenant('t2')
            .segment('s3', 'vlan', [s3_vlan_ip], s3_vlan_id)
            .segment_member(SegmentMember('s3', cfg.leaf1['id']).ports([cfg.leaf1['portA'].name]))
            .segment('s4', 'vlan', [s4_vlan_ip], s4_vlan_id)
            .segment_member(SegmentMember('s4', cfg.leaf1['id']).ports([cfg.leaf1['portB'].name]))
            .build()
        )

        lrouter_r1 = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .build()
        )

        lrouter_r2 = (
            LogicalRouter('r2', 't2')
            .interfaces(['s3', 's4'])
            .build()
        )

        system_tenant = (
            Tenant('system', 'System')
            .build()
        )

        lrouter_system = (
            LogicalRouter('system')
            .tenant_routers(['t1/r1', 't2/r2'])
            .build()
        )

        dhcp_relay = (
            DHCPRelay('t1', 's1')
            .servers([dhcp_server_ip])
            .build()
        )

        cfg.dhcp_server['ip'] = dhcp_server_ip

        # TODO: this case needs VRF feature
        spine = get_master_spine(
            self.dataplane, cfg.dhcp_server, s1_vlan_ip, ports[3])
        send_icmp_echo_request(
            self.dataplane, cfg.dhcp_server, spine, s2_vlan_ip, ports[3])

        dhcp_pkt = DHCP_PKT()

        # verify dhcp discover
        dhcp_discover = dhcp_pkt.generate_discover_pkt(cfg.host0)
        expected_dhcp_discover = dhcp_pkt.generate_expected_discover_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s4_vlan_ip)

        self.dataplane.send(ports[0], str(dhcp_discover))
        verify_packet(self, str(expected_dhcp_discover), ports[3])

        # verify dhcp offer
        dhcp_offer = dhcp_pkt.generate_offer_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        expected_dhcp_offer = dhcp_pkt.generate_expected_offer_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)

        self.dataplane.send(ports[3], str(dhcp_offer))
        verify_packet(self, str(expected_dhcp_offer), ports[0])

        # verify dhcp request
        dhcp_request = dhcp_pkt.generate_request_pkt(
            cfg.dhcp_server, cfg.host0, allocated_ip)
        expected_dhcp_request = dhcp_pkt.generate_expected_request_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s4_vlan_ip, allocated_ip)

        self.dataplane.send(ports[0], str(dhcp_request))
        verify_packet(self, str(expected_dhcp_request), ports[3])

        # verify dhcp ack
        dhcp_ack = dhcp_pkt.generate_ack_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        expected_dhcp_ack = dhcp_pkt.generate_expected_ack_pkt(
            spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)

        self.dataplane.send(ports[3], str(dhcp_ack))
        verify_packet(self, str(expected_dhcp_ack), ports[0])

        dhcp_relay.destroy()
        lrouter_r1.destroy()
        lrouter_r2.destroy()
        lrouter_system.destroy()
        system_tenant.destroy()
        t1.destroy()
        t2.destroy()


@disabled
class PhysicalServer(DHCPRelayTest):
    """
    Test DHCP relay with physical server for manual test
    """

    def tearDown(self):
        DHCPRelayTest.tearDown(self)

    def runTest(self):
        s1_vlan_id = 50
        s2_vlan_id = 100
        s1_vlan_ip = '192.168.50.1'
        s2_vlan_ip = '192.168.100.1'
        dhcp_server_ip = '192.168.100.10'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_vlan_ip], s1_vlan_id)
            .segment_member(SegmentMember('s1', cfg.leaf0['id']).ports([cfg.leaf0['portA'].name]))
            .segment('s2', 'vlan', [s2_vlan_ip], s2_vlan_id)
            .segment_member(SegmentMember('s2', cfg.leaf1['id']).ports([cfg.leaf1['portA'].name, cfg.leaf1['portB'].name]))
            .build()
        )

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .build()
        )

        dhcp_relay = (
            DHCPRelay('t1', 's1')
            .servers([dhcp_server_ip])
            .build()
        )

        cfg.dhcp_server['ip'] = dhcp_server_ip

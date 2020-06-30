"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test exception condition case

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


class RestartMarsException(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)

    def restart_mars(self, verify_func):
        verify_func()

        # save current config
        conf = Configuration()
        conf.save_as_boot_default_config(conf.get_current_json())

        os.system('docker restart mars > /dev/null')
        wait_for_seconds(100)

        verify_func()


class TenantLogicalRouterConfig(RestartMarsException):
    """
    Test tenant logical router config for restart mars exception
    """

    def runTest(self):
        s1_vlan_id = 38
        s2_vlan_id = 58
        ports = sorted(config["port_map"].keys())

        s1_ip = ['192.168.38.1']
        s2_ip = ['192.168.58.1']

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', s1_ip, s1_vlan_id)
            .segment_member(SegmentMember('s1', cfg.leaf0['id']).ports([cfg.leaf0['portA'].name]))
            .segment('s2', 'vlan', s2_ip, s2_vlan_id)
            .segment_member(SegmentMember('s2', cfg.leaf1['id']).ports([cfg.leaf1['portA'].name]))
            .build()
        )

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .build()
        )

        cfg.host0['ip'] = '192.168.38.30'
        cfg.host2['ip'] = '192.168.58.30'

        def test_by_packet():
            master_spine = get_master_spine(
                self.dataplane, cfg.host2, s2_ip, ports[2])
            send_icmp_echo_request(
                self.dataplane, cfg.host2, master_spine, s2_ip, ports[2])

            pkt_from_p0_to_p2 = simple_tcp_packet(
                pktlen=68,
                dl_vlan_enable=True,
                vlan_vid=s1_vlan_id,
                eth_dst=master_spine['mac'],
                eth_src=cfg.host0['mac'],
                ip_dst=cfg.host2['ip'],
                ip_src=cfg.host0['ip']
            )

            # check connection between 2 segments
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))

            pkt_expected = simple_tcp_packet(
                pktlen=64,
                eth_dst=cfg.host2['mac'],
                eth_src=master_spine['mac'],
                ip_dst=cfg.host2['ip'],
                ip_src=cfg.host0['ip'],
                ip_ttl=63
            )

            verify_packet(self, str(pkt_expected), ports[2])

            self.dataplane.flush()

        self.restart_mars(test_by_packet)

        lrouter.destroy()
        t1.destroy()


class DHCPRelayConfig(RestartMarsException):
    """
    Test DHCP relay config for restart mars exception
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        s1_vlan_id = 65
        s2_vlan_id = 115
        s1_vlan_ip = '192.168.65.1'
        s2_vlan_ip = '192.168.115.1'
        dhcp_server_ip = '192.168.115.20'
        allocated_ip = '192.168.65.51'

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

        def test_by_packet():
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

        self.restart_mars(test_by_packet)

        dhcp_relay.destroy()
        lrouter.destroy()
        t1.destroy()


class SpanConfig(RestartMarsException):
    """
    Test SPAN config for restart mars exception
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        session_id = 1
        source_port = cfg.leaf0['portA'].number
        target_port = cfg.leaf1['portA'].number
        direction = 'rx'

        wait_for_system_stable()

        span = (
            SPAN(session_id)
            .source(cfg.leaf0['id'], source_port, direction)
            .target(cfg.leaf1['id'], target_port)
            .build()
        )

        wait_for_system_stable()

        cfg.host0['ip'] = '192.168.10.10'
        cfg.host1['ip'] = '192.168.10.20'

        def test_by_packet():
            pkt_from_src = simple_tcp_packet(
                pktlen=68,
                dl_vlan_enable=True,
                vlan_vid=20,
                eth_dst=cfg.host1['mac'],
                eth_src=cfg.host0['mac'],
                ip_dst=cfg.host1['ip'],
                ip_src=cfg.host0['ip']
            )

            # check monitor status from source to target
            self.dataplane.send(ports[0], str(pkt_from_src))
            verify_no_packet(self, str(pkt_from_src), ports[1])
            verify_packet(self, str(pkt_from_src), ports[2])

        self.restart_mars(test_by_packet)

        span.destroy()

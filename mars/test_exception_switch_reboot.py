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


class RebootException(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)

    def reboot_switch(self):
        rp_spine0 = RemotePower(cfg.spine0_power)
        rp_spine1 = RemotePower(cfg.spine1_power)
        rp_leaf0 = RemotePower(cfg.leaf0_power)
        rp_leaf1 = RemotePower(cfg.leaf1_power)

        rp_spine0.OffOn()
        rp_spine1.OffOn()
        rp_leaf0.OffOn()
        rp_leaf1.OffOn()

        wait_for_seconds(60)

        links_inspect(cfg.spines, cfg.leaves)

        wait_for_seconds(60)


class SpineRole(RebootException):
    """
    Test spine switch reboot exception
    """

    def runTest(self):
        d0 = Device(cfg.spine0['id'])
        d1 = Device(cfg.spine1['id'])

        assert d0.available, "d0 device's avaiable shall be true"
        assert d1.available, "d1 device's avaiable shall be true"

        rp_spine0 = RemotePower(cfg.spine0_power)
        rp_spine1 = RemotePower(cfg.spine1_power)

        rp_spine0.OffOn()
        rp_spine1.OffOn()

        wait_for_seconds(60)

        assert d0.available == False, "d0 device's avaiable shall be false"
        assert d1.available == False, "d1 device's avaiable shall be false"

        links_inspect(cfg.spines, cfg.leaves)

        assert d0.available, "d0 device's avaiable shall be true"
        assert d1.available, "d1 device's avaiable shall be true"


class LeafRole(RebootException):
    """
    Test leaf switch reboot exception
    """

    def runTest(self):
        d0 = Device(cfg.leaf0['id'])
        d1 = Device(cfg.leaf1['id'])

        assert d0.available, "d0 device's avaiable shall be true"
        assert d1.available, "d1 device's avaiable shall be true"

        rp_leaf0 = RemotePower(cfg.leaf0_power)
        rp_leaf1 = RemotePower(cfg.leaf1_power)

        rp_leaf0.OffOn()
        rp_leaf1.OffOn()

        wait_for_seconds(60)

        assert d0.available == False, "d0 device's avaiable shall be false"
        assert d1.available == False, "d1 device's avaiable shall be false"

        links_inspect(cfg.spines, cfg.leaves)

        assert d0.available, "d0 device's avaiable shall be true"
        assert d1.available, "d1 device's avaiable shall be true"


class TenantConfig(RebootException):
    """
    Test tenant after switch reboot
    """

    def runTest(self):
        vlan_id = 99
        ports = sorted(config["port_map"].keys())

        cfg.leaf0['portA'].tagged(True)
        cfg.leaf0['portB'].tagged(True)
        cfg.leaf1['portA'].tagged(True)
        cfg.leaf1['portB'].tagged(True)

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', ['192.168.99.1'], vlan_id)
            .segment_member(SegmentMember('s1', cfg.leaf0['id']).ports([cfg.leaf0['portA'].name, cfg.leaf0['portB'].name]))
            .segment_member(SegmentMember('s1', cfg.leaf1['id']).ports([cfg.leaf1['portA'].name]))
            .build()
        )

        utils.wait_for_system_stable()

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=100,
            dl_vlan_enable=True,
            vlan_vid=vlan_id,
            eth_dst='90:e2:ba:24:78:12',
            eth_src='00:00:00:11:22:33',
            ip_src='192.168.99.100',
            ip_dst='192.168.99.101'
        )

        pkt_from_p0_to_p2 = simple_tcp_packet(
            pktlen=100,
            dl_vlan_enable=True,
            vlan_vid=vlan_id,
            eth_dst='90:e2:ba:24:a2:70',
            eth_src='00:00:00:11:22:33',
            ip_src='192.168.99.100',
            ip_dst='192.168.99.110'
        )

        pkt_from_p0_to_p3 = simple_tcp_packet(
            pktlen=100,
            dl_vlan_enable=True,
            vlan_vid=vlan_id,
            eth_dst='90:e2:ba:24:a2:72',
            eth_src='00:00:00:11:22:33',
            ip_src='192.168.99.100',
            ip_dst='192.168.99.111'
        )

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
        verify_packet(self, str(pkt_from_p0_to_p1), ports[1])

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))
        verify_packet(self, str(pkt_from_p0_to_p2), ports[2])

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p3))
        verify_no_packet(self, str(pkt_from_p0_to_p3), ports[3])

        self.reboot_switch()

        # check behavior again
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
        verify_packet(self, str(pkt_from_p0_to_p1), ports[1])

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))
        verify_packet(self, str(pkt_from_p0_to_p2), ports[2])

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p3))
        verify_no_packet(self, str(pkt_from_p0_to_p3), ports[3])

        t1.delete_segment('s1')
        t1.destroy()


class TenantLogicalRouterConfig(RebootException):
    """
    Test tenant logical router after switch reboot
    """

    def runTest(self):
        s1_vlan_id = 15
        s2_vlan_id = 25
        ports = sorted(config["port_map"].keys())

        s1_ip = ['192.168.15.1']
        s2_ip = ['192.168.25.1']

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

        cfg.host0['ip'] = '192.168.15.30'
        cfg.host2['ip'] = '192.168.25.30'

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

        test_by_packet()

        self.reboot_switch()

        test_by_packet()

        lrouter.destroy()
        t1.destroy()


class DHCPRelayConfig(RebootException):
    """
    Test DHCP relay after switch reboot
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        s1_vlan_id = 55
        s2_vlan_id = 105
        s1_vlan_ip = '192.168.55.1'
        s2_vlan_ip = '192.168.105.1'
        dhcp_server_ip = '192.168.105.20'
        allocated_ip = '192.168.55.51'

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

        test_by_packet()

        self.reboot_switch()

        test_by_packet()

        dhcp_relay.destroy()
        lrouter.destroy()
        t1.destroy()


class SpanConfig(RebootException):
    """
    Test SPAN after switch reboot
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        session_id = 1
        source_port = cfg.leaf0['portA'].number
        target_port = cfg.leaf1['portA'].number
        direction = 'rx'

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

        test_by_packet()

        self.reboot_switch()

        test_by_packet()

        span.destroy()


class LogicalPortConfig(RebootException):
    """
    Test logical port config after switch reboot
    """

    def runTest(self):
        lp1 = (
            LogicalPort('lp1')
            .group(1)
            .members([
                {"device_id": cfg.leaf0['id'], "port": 15},
                {"device_id": cfg.leaf0['id'], "port": 16}
            ])
            .build()
        )

        wait_for_seconds(2)

        sw_lp1 = SwitchLogicalPort(cfg.leaf0)
        switch_actual_lp1 = sw_lp1.get_portchannel(1)['result']

        assert(switch_actual_lp1['id'] == 1)
        assert(set(switch_actual_lp1['members']) == set([15, 16]))

        lp2 = (
            LogicalPort('lp2')
            .group(2)
            .members([
                {"device_id": cfg.leaf1['id'], "port": 1},
                {"device_id": cfg.leaf1['id'], "port": 2},
                {"device_id": cfg.leaf1['id'], "port": 3},
                {"device_id": cfg.leaf1['id'], "port": 4},
                {"device_id": cfg.leaf1['id'], "port": 5},
                {"device_id": cfg.leaf1['id'], "port": 6},
                {"device_id": cfg.leaf1['id'], "port": 7},
                {"device_id": cfg.leaf1['id'], "port": 8}
            ])
            .build()
        )

        wait_for_seconds(2)

        sw_lp2 = SwitchLogicalPort(cfg.leaf1)
        switch_actual_lp2 = sw_lp2.get_portchannel(2)['result']

        assert(switch_actual_lp2['id'] == 2)
        assert(set(switch_actual_lp2['members'])
               == set([1, 2, 3, 4, 5, 6, 7, 8]))

        self.reboot_switch()

        sw_lp1_reboot = SwitchLogicalPort(cfg.leaf0)
        switch_actual_lp1_reboot = sw_lp1_reboot.get_portchannel(1)['result']

        assert(switch_actual_lp1_reboot['id'] == 1)
        assert(set(switch_actual_lp1_reboot['members']) == set([15, 16]))

        sw_lp2_reboot = SwitchLogicalPort(cfg.leaf1)
        switch_actual_lp2_reboot = sw_lp2_reboot.get_portchannel(2)['result']

        assert(switch_actual_lp2_reboot['id'] == 2)
        assert(set(switch_actual_lp2_reboot['members'])
               == set([1, 2, 3, 4, 5, 6, 7, 8]))

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


class MacBasedVlan(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)

class BasicInSameLeaf(MacBasedVlan):
    """
    Test MAC based VLAN basic feature in same leaf
    """

    def runTest(self):
        s1_vlan_id = 80
        ports = sorted(config["port_map"].keys())

        cfg.leaf0['portB'].tagged(True)

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [], s1_vlan_id)
            .segment_member(
                SegmentMember('s1', cfg.leaf0['id'])
                .ports([cfg.leaf0['portB'].name])
                .mac_based_vlan(['{}/48'.format(cfg.host0['mac'])])
            )
            .build()
        )

        pkt_from_p0_to_p1 = str(simple_tcp_packet(
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=cfg.host1['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host1['ip'],
            ip_src=cfg.host0['ip']
        ))

        self.dataplane.send(ports[0], pkt_from_p0_to_p1)
        verify_packet(self, pkt_from_p0_to_p1, ports[1])

        t1.destroy()

class BasicInDifferentLeaf(MacBasedVlan):
    """
    Test MAC based VLAN basic feature in different leaf
    """

    def runTest(self):
        s1_vlan_id = 90
        ports = sorted(config["port_map"].keys())

        cfg.leaf1['portA'].tagged(True)

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [], s1_vlan_id)
            .segment_member(
                SegmentMember('s1', cfg.leaf0['id'])
                .mac_based_vlan(['{}/48'.format(cfg.host0['mac'])])
            )
            .segment_member(
                SegmentMember('s1', cfg.leaf1['id'])
                .ports([cfg.leaf1['portA'].name])
            )
            .build()
        )

        pkt_from_p0_to_p2 = str(simple_tcp_packet(
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=cfg.host2['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host2['ip'],
            ip_src=cfg.host0['ip']
        ))

        self.dataplane.send(ports[0], pkt_from_p0_to_p2)
        verify_packet(self, pkt_from_p0_to_p2, ports[2])

        t1.destroy()

class BasicWithDifferentPort(MacBasedVlan):
    """
    Test MAC based VLAN basic feature with different port
    """

    def runTest(self):
        s1_vlan_id = 100
        ports = sorted(config["port_map"].keys())

        cfg.leaf1['portA'].tagged(True)

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [], s1_vlan_id)
            .segment_member(
                SegmentMember('s1', cfg.leaf0['id'])
                .mac_based_vlan(['{}/48'.format(cfg.host0['mac'])])
            )
            .segment_member(
                SegmentMember('s1', cfg.leaf1['id'])
                .ports([cfg.leaf1['portA'].name])
            )
            .build()
        )

        pkt_to_p2_with_host0_mac = str(simple_tcp_packet(
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=cfg.host2['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host2['ip'],
            ip_src=cfg.host0['ip']
        ))

        self.dataplane.send(ports[1], pkt_to_p2_with_host0_mac)
        verify_packet(self, pkt_to_p2_with_host0_mac, ports[2])

        self.dataplane.send(ports[3], pkt_to_p2_with_host0_mac)
        verify_packet(self, pkt_to_p2_with_host0_mac, ports[2])

        t1.destroy()

class RoutingInSameLeaf(MacBasedVlan):
    """
    Test MAC based VLAN with routing in same leaf
    """

    def runTest(self):
        s1_vlan_id = 110
        s2_vlan_id = 120
        s1_ip = '192.168.110.1'
        s2_ip = '192.168.120.1'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], s1_vlan_id)
            .segment_member(
                SegmentMember('s1', cfg.leaf0['id'])
                .mac_based_vlan(['{}/48'.format(cfg.host0['mac'])])
            )
            .segment('s2', 'vlan', [s2_ip], s2_vlan_id)
            .segment_member(
                SegmentMember('s2', cfg.leaf0['id'])
                .ports([cfg.leaf0['portB'].name])
            )
            .build()
        )

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .build()
        )

        cfg.host0['ip'] = '192.168.110.30'
        cfg.host1['ip'] = '192.168.120.30'

        master_spine = get_master_spine(self.dataplane, cfg.host1, s2_ip, ports[1])
        send_icmp_echo_request(self.dataplane, cfg.host1, master_spine, s2_ip, ports[1])

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=master_spine['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host1['ip'],
            ip_src=cfg.host0['ip']
        )

        # check connection between 2 segments
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))

        pkt_expected = simple_tcp_packet(
            pktlen=64,
            eth_dst=cfg.host1['mac'],
            eth_src=master_spine['mac'],
            ip_dst=cfg.host1['ip'],
            ip_src=cfg.host0['ip'],
            ip_ttl=63
        )

        verify_packet(self, str(pkt_expected), ports[1])

        lrouter.destroy()
        t1.destroy()

class RoutingInDifferentLeaf(MacBasedVlan):
    """
    Test MAC based VLAN with routing in different leaf
    """

    def runTest(self):
        s1_vlan_id = 130
        s2_vlan_id = 140
        s1_ip = '192.168.130.1'
        s2_ip = '192.168.140.1'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], s1_vlan_id)
            .segment_member(
                SegmentMember('s1', cfg.leaf0['id'])
                .mac_based_vlan(['{}/48'.format(cfg.host0['mac'])])
            )
            .segment('s2', 'vlan', [s2_ip], s2_vlan_id)
            .segment_member(
                SegmentMember('s2', cfg.leaf1['id'])
                .ports([cfg.leaf1['portB'].name])
            )
            .build()
        )

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .build()
        )

        cfg.host0['ip'] = '192.168.130.30'
        cfg.host3['ip'] = '192.168.140.30'

        master_spine = get_master_spine(self.dataplane, cfg.host3, s2_ip, ports[3])
        send_icmp_echo_request(self.dataplane, cfg.host3, master_spine, s2_ip, ports[3])

        pkt_from_p0_to_p3 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=s1_vlan_id,
            eth_dst=master_spine['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host3['ip'],
            ip_src=cfg.host0['ip']
        )

        # check connection between 2 segments
        self.dataplane.send(ports[0], str(pkt_from_p0_to_p3))

        pkt_expected = simple_tcp_packet(
            pktlen=64,
            eth_dst=cfg.host3['mac'],
            eth_src=master_spine['mac'],
            ip_dst=cfg.host3['ip'],
            ip_src=cfg.host0['ip'],
            ip_ttl=63
        )

        verify_packet(self, str(pkt_expected), ports[3])

class RebootLeaf(MacBasedVlan):
    """
    Test MAC based VLAN after rebooting leaf
    """

    def runTest(self):
        s1_vlan_id = 200
        ports = sorted(config["port_map"].keys())

        cfg.leaf1['portA'].tagged(True)

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [], s1_vlan_id)
            .segment_member(
                SegmentMember('s1', cfg.leaf0['id'])
                .mac_based_vlan(['{}/48'.format(cfg.host0['mac'])])
            )
            .segment_member(
                SegmentMember('s1', cfg.leaf1['id'])
                .ports([cfg.leaf1['portA'].name])
            )
            .build()
        )

        def test_by_packet():
            pkt_from_p0_to_p2 = str(simple_tcp_packet(
                dl_vlan_enable=True,
                vlan_vid=s1_vlan_id,
                eth_dst=cfg.host2['mac'],
                eth_src=cfg.host0['mac'],
                ip_dst=cfg.host2['ip'],
                ip_src=cfg.host0['ip']
            ))

            self.dataplane.send(ports[0], pkt_from_p0_to_p2)
            verify_packet(self, pkt_from_p0_to_p2, ports[2])

        test_by_packet()

        d0 = Device(cfg.leaf0['id'])
        rp_leaf0 = RemotePower(cfg.leaf0_power)
        rp_leaf0.OffOn()

        wait_for_seconds(60)

        assert d0.available == False, "d0 device's avaiable shall be false"

        links_inspect(cfg.spines, cfg.leaves)

        test_by_packet()

        t1.destroy()

class RestartMars(MacBasedVlan):
    """
    Test MAC based VLAN after restarting Mars
    """

    def runTest(self):
        s1_vlan_id = 210
        ports = sorted(config["port_map"].keys())

        cfg.leaf1['portA'].tagged(True)

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [], s1_vlan_id)
            .segment_member(
                SegmentMember('s1', cfg.leaf0['id'])
                .mac_based_vlan(['{}/48'.format(cfg.host0['mac'])])
            )
            .segment_member(
                SegmentMember('s1', cfg.leaf1['id'])
                .ports([cfg.leaf1['portA'].name])
            )
            .build()
        )

        def test_by_packet():
            pkt_from_p0_to_p2 = str(simple_tcp_packet(
                dl_vlan_enable=True,
                vlan_vid=s1_vlan_id,
                eth_dst=cfg.host2['mac'],
                eth_src=cfg.host0['mac'],
                ip_dst=cfg.host2['ip'],
                ip_src=cfg.host0['ip']
            ))

            self.dataplane.send(ports[0], pkt_from_p0_to_p2)
            verify_packet(self, pkt_from_p0_to_p2, ports[2])

        test_by_packet()

        # save current config
        conf = Configuration()
        conf.save_as_boot_default_config(conf.get_current_json())

        os.system('docker restart mars > /dev/null')
        wait_for_seconds(100)

        test_by_packet()


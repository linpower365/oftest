"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test VLAN Rest API.

Test environment

    +--------+
    | spine0 |
    +--------+
   49 |  | 50
      |  +------------+
   49 |            49 |
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


class VLANTest(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)


class StaticVlanSetterAndGetter(VLANTest):
    """
    Test set and get VLAN rest API
    """

    def runTest(self):
        vlan_cfg = {}
        vlan_cfg['device-id'] = cfg.leaf0['id']
        vlan_cfg['ports'] = [
            {
                "port": 46,
                "native": 100,
                "mode": "access",
                "vlans": [
                    "100/untag", "200/untag"
                ]
            }
        ]

        vlan = StaticVLAN(vlan_cfg).build()
        actual_port = vlan.get_port(46)

        assert(vlan_cfg['ports'][0]['port'] == actual_port['port'])
        assert(vlan_cfg['ports'][0]['native'] == actual_port['native'])
        assert(vlan_cfg['ports'][0]['mode'] == actual_port['mode'])
        assert(['100/untag'] == actual_port['vlans'])

        vlan.delete({'port': 46, 'device-id': cfg.leaf0['id']})
        actual_port = vlan.get_port(46)

        assert(None == actual_port)

        vlan_cfg1 = {}
        vlan_cfg1['device-id'] = cfg.leaf0['id']
        vlan_cfg1['ports'] = [
            {
                "port": 48,
                "native": 100,
                "mode": "hybrid",
                "vlans": [
                    "50/untag", "200/untag"
                ]
            }
        ]

        vlan1 = StaticVLAN(vlan_cfg1).build()
        actual_port = vlan.get_port(48)

        assert(vlan_cfg1['ports'][0]['port'] == actual_port['port'])
        assert(vlan_cfg1['ports'][0]['native'] == actual_port['native'])
        assert(vlan_cfg1['ports'][0]['mode'] == actual_port['mode'])
        assert(set(vlan_cfg1['ports'][0]['vlans'])
               == set(actual_port['vlans']))

        vlan.delete({'port': 48, 'device-id': cfg.leaf0['id']})
        actual_port = vlan.get_port(48)

        assert(None == actual_port)


class StaticVlanWithSameLeaf(VLANTest):
    """
    Test static VLAN with same leaf
    """

    def runTest(self):
        vlan_id = 80
        ports = sorted(config["port_map"].keys())

        vlan_cfg_sw1 = {}
        vlan_cfg_sw1['device-id'] = cfg.leaf0['id']
        vlan_cfg_sw1['ports'] = [
            {
                "port": 46,
                "native": vlan_id,
                "mode": "hybrid",
                "vlans": [
                    str(vlan_id) + "/untag"
                ]
            },
            {
                "port": 48,
                "native": vlan_id,
                "mode": "hybrid",
                "vlans": [
                    str(vlan_id) + "/untag"
                ]
            }
        ]

        vlan_sw1 = StaticVLAN(vlan_cfg_sw1).build()

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=vlan_id,
            eth_dst=cfg.host1['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host1['ip'],
            ip_src=cfg.host0['ip']
        )

        expected_pkt = simple_tcp_packet(
            pktlen=64,
            dl_vlan_enable=False,
            eth_dst=cfg.host1['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host1['ip'],
            ip_src=cfg.host0['ip']
        )

        self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
        verify_packet(self, str(expected_pkt), ports[1])
        verify_no_packet(self, str(expected_pkt), ports[2])


class StaticVlanWithDiffLeaf(VLANTest):
    """
    Test static VLAN with different leaf
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        vlan_cfg_sw1 = {}
        vlan_cfg_sw1['device-id'] = cfg.leaf0['id']
        vlan_cfg_sw1['ports'] = [
            {
                "port": 46,
                "native": 100,
                "mode": "hybrid",
                "vlans": [
                    "100/untag", "200/untag"
                ]
            }
        ]

        vlan_cfg_sw2 = {}
        vlan_cfg_sw2['device-id'] = cfg.leaf1['id']
        vlan_cfg_sw2['ports'] = [
            {
                "port": 46,
                "native": 100,
                "mode": "hybrid",
                "vlans": [
                    "100/untag", "200/untag"
                ]
            }
        ]

        vlan_sw1 = StaticVLAN(vlan_cfg_sw1).build()
        vlan_sw2 = StaticVLAN(vlan_cfg_sw2).build()

        cfg.host0['ip'] = '192.168.100.1'
        cfg.host1['ip'] = '192.168.100.2'

        pkt_from_p0_to_p2 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=200,
            eth_dst=cfg.host1['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host1['ip'],
            ip_src=cfg.host0['ip']
        )

        expected_pkt = simple_tcp_packet(
            pktlen=64,
            dl_vlan_enable=False,
            eth_dst=cfg.host1['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host1['ip'],
            ip_src=cfg.host0['ip']
        )

        for i in range(5):
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))
            wait_for_seconds(1)

        verify_packet(self, str(expected_pkt), ports[2])
        verify_no_packet(self, str(expected_pkt), ports[3])


class DynamicVlanSetterAndGetter(VLANTest):
    """
    Test dynamic VLAN
    """

    def runTest(self):
        vlan_cfg = {}
        vlan_cfg['device-id'] = cfg.leaf0['id']
        vlan_cfg['dynamicvlans'] = [
            {
                "port": 46,
                "dynamicVlan": "disable"
            }
        ]

        dynamic_vlan_port_46 = DynamicVLAN(vlan_cfg).build()

        assert('disable' == dynamic_vlan_port_46.get_port(46))

        dynamic_vlan_port_46.enable()

        assert('enable' == dynamic_vlan_port_46.get_port(46))

        dynamic_vlan_port_46.disable()

        assert('disable' == dynamic_vlan_port_46.get_port(46))


class GuestVlanSetterAndGetter(VLANTest):
    """
    Test guest VLAN
    """

    def runTest(self):
        expected_guest_vlan = 99

        vlan_cfg = {}
        vlan_cfg['device-id'] = cfg.leaf0['id']
        vlan_cfg['guestvlans'] = [
            {
                "port": 46,
                "guestVlan": expected_guest_vlan
            }
        ]

        guest_vlan_port_46 = GuestVLAN(vlan_cfg).build()

        assert(expected_guest_vlan == guest_vlan_port_46.get_vlan())

        for vlan_id in [35, 0]:
            expected_guest_vlan = vlan_id
            guest_vlan_port_46.vlan(expected_guest_vlan)

            assert(expected_guest_vlan == guest_vlan_port_46.get_vlan())


class VlanIPSetterAndGetter(VLANTest):
    """
    Test VLAN IP setting
    """

    def runTest(self):
        vlan_cfg = {}
        vlan_cfg['device-id'] = cfg.leaf0['id']
        vlan_cfg['vlans'] = [
            {
                "vlan": 100,
                "ip": "192.168.100.1",
                "mask": "255.255.255.0"
            }
        ]

        vlan = VLAN(vlan_cfg).build()

        assert(vlan_cfg['vlans'][0] == vlan.get(100))

        expected_cfg = [
            {
                "vlan": 65,
                "ip": "192.168.65.1",
                "mask": "255.255.0.0"
            }
        ]

        vlan.set(expected_cfg)

        assert(expected_cfg[0] == vlan.get(65))

        vlan.delete(65)

        assert(None == vlan.get(65))


class VoiceVlanSetterAndGetter(VLANTest):
    """
    Test voice VLAN
    """

    def runTest(self):
        voice_vlan_cfg = {}
        voice_vlan_cfg['device-id'] = cfg.leaf0['id']
        voice_vlan_cfg['basic'] = {
            "vlan": 80,
            "aging": 1440,
            "status": "enable"
        }
        oui_cfg = [
            {
                "macAddress": "66-23-45-00-00-00",
                "maskAddress": "FF-FF-FF-FF-FF-FF",
                "description": "a test desc"
            }
        ]
        ports_cfg = [
            {
                "port": 48,
                "security": True,
                "rule": "lldp",
                "priority": 5,
                "mode": "auto"
            }
        ]

        voice_vlan = VoiceVLAN(voice_vlan_cfg).build()
        voice_vlan.set_oui(oui_cfg)
        voice_vlan.set_ports(ports_cfg)

        actual_value = voice_vlan.get()

        assert(voice_vlan_cfg['basic'] == actual_value['basic'])
        assert(oui_cfg == actual_value['ouis'])
        assert(ports_cfg == actual_value['ports'])

        voice_vlan.delete()
        actual_value = voice_vlan.get()

        assert({} == actual_value['basic'])
        assert([] == actual_value['ouis'])
        assert([] == actual_value['ports'])

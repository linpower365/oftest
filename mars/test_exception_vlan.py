"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test exception condition case

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


class VlanException(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)

    def reboot_spine0_switch(self):
        d0 = Device(cfg.spine0['id'])
        rp_spine0 = RemotePower(cfg.spine0_power)

        rp_spine0.OffOn()

        wait_for_seconds(60)

        links_inspect(cfg.spines, cfg.leaves)


class StaticVlan(VlanException):
    """
    Test static vlan setting shall not be changed while switch reboot
    """

    def runTest(self):
        vlan_cfg = {}
        vlan_cfg['device-id'] = cfg.spine0['id']
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

        self.reboot_spine0_switch()

        actual_port = vlan.get_port(46)

        assert(vlan_cfg['ports'][0]['port'] == actual_port['port'])
        assert(vlan_cfg['ports'][0]['native'] == actual_port['native'])
        assert(vlan_cfg['ports'][0]['mode'] == actual_port['mode'])
        assert(['100/untag'] == actual_port['vlans'])


class DynamicVlan(VlanException):
    """
    Test dynamic vlan setting shall not be changed while switch reboot
    """

    def runTest(self):
        vlan_cfg = {}
        vlan_cfg['device-id'] = cfg.spine0['id']
        vlan_cfg['dynamicvlans'] = [
            {
                "port": 46,
                "dynamicVlan": "disable"
            }
        ]

        dynamic_vlan_port_46 = DynamicVLAN(vlan_cfg).build()

        self.reboot_spine0_switch()

        assert('disable' == dynamic_vlan_port_46.get_port(46))


class GuestVlan(VlanException):
    """
    Test guest vlan setting shall not be changed while switch reboot
    """

    def runTest(self):
        expected_guest_vlan = 200

        vlan_cfg = {}
        vlan_cfg['device-id'] = cfg.spine0['id']
        vlan_cfg['guestvlans'] = [
            {
                "port": 46,
                "guestVlan": expected_guest_vlan
            }
        ]

        guest_vlan_port_46 = GuestVLAN(vlan_cfg).build()

        self.reboot_spine0_switch()

        assert(expected_guest_vlan == guest_vlan_port_46.get_vlan())


class VlanIp(VlanException):
    """
    Test vlan ip setting shall not be changed while switch reboot
    """

    def runTest(self):
        vlan_cfg = {}
        vlan_cfg['device-id'] = cfg.spine0['id']
        vlan_cfg['vlans'] = [
            {
                "vlan": 100,
                "ip": "192.168.100.1",
                "mask": "255.255.255.0"
            }
        ]

        vlan = VLAN(vlan_cfg).build()

        self.reboot_spine0_switch()

        assert(vlan_cfg['vlans'][0] == vlan.get(100))


class VoiceVlan(VlanException):
    """
    Test voice vlan setting shall not be changed while switch reboot
    """

    def runTest(self):
        voice_vlan_cfg = {}
        voice_vlan_cfg['device-id'] = cfg.spine0['id']
        voice_vlan_cfg['basic'] = {
            "vlan": 90,
            "aging": 600,
            "status": "enable"
        }
        oui_cfg = [
            {
                "macAddress": "00-11-22-33-44-55",
                "maskAddress": "FF-FF-FF-FF-FF-FF",
                "description": "test-voice-vlan"
            }
        ]
        ports_cfg = [
            {
                "port": 46,
                "security": True,
                "rule": "lldp",
                "priority": 4,
                "mode": "manual"
            }
        ]

        voice_vlan = VoiceVLAN(voice_vlan_cfg).build()
        voice_vlan.set_oui(oui_cfg)
        voice_vlan.set_ports(ports_cfg)

        self.reboot_spine0_switch()

        actual_value = voice_vlan.get()

        assert(voice_vlan_cfg['basic'] == actual_value['basic'])
        assert(oui_cfg == actual_value['ouis'])
        assert(ports_cfg == actual_value['ports'])

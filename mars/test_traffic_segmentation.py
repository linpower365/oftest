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
import paramiko
import pexpect
from oftest import config
from oftest.testutils import *
from utils import *


class TrafficSegmentationTest(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)


class SetterAndGetter(TrafficSegmentationTest):
    """
    Test basic setter and getter rest API
    """

    def runTest(self):
        session_id = 5
        uplink_port = ['46']
        downlink_port = ['48']

        ts1 = (
            TrafficSegmentation(cfg.leaf0['id'])
            .session(session_id)
            .uplinks(uplink_port)
            .downlinks(downlink_port)
            .build()
        )

        actual_value = ts1.get()[cfg.leaf0['id']][0]

        assert(session_id == actual_value['sessionId'])
        assert(uplink_port == actual_value['uplinks'])
        assert(downlink_port == actual_value['downlinks'])

        ts1.delete()


class OneSessionWithSpineType(TrafficSegmentationTest):
    """
    Test one session with spine type
    """

    def tearDown(self):
        TrafficSegmentationTest.tearDown(self)
        config_remove(cfg.spine0)
        config_remove(cfg.leaf0)

    def runTest(self):
        config_remove(cfg.spine0)
        config_remove(cfg.leaf0)

        cfg.spine0['type'] = 'leaf'
        cfg.leaf0['type'] = 'spine'

        config_add(cfg.spine0)
        config_add(cfg.leaf0)

        links = [(cfg.spine0, cfg.leaf0), (cfg.spine0, cfg.leaf1)]

        links_inspect2(links, True)

        ports = sorted(config["port_map"].keys())
        session_id = 1
        uplink_port = ['46']
        downlink_port = ['48']

        ts1 = (
            TrafficSegmentation(cfg.leaf0['id'])
            .session(session_id)
            .uplinks(uplink_port)
            .downlinks(downlink_port)
            .build()
        )

        # cfg.host0['ip'] = '192.168.10.10'
        # cfg.host0['ip'] = '192.168.10.20'

        # pkt_from_p1_to_p0 = simple_tcp_packet(
        #     pktlen=64,
        #     eth_dst=cfg.host1['mac'],
        #     eth_src=cfg.host0['mac'],
        #     ip_dst=cfg.host1['ip'],
        #     ip_src=cfg.host0['ip']
        # )

        # self.dataplane.send(ports[1], str(pkt_from_p1_to_p0))
        # verify_packet(self, str(pkt_from_p1_to_p0), ports[0])

        ts1.delete()


class OneSessionWithLeafType(TrafficSegmentationTest):
    """
    Test one session with leaf type
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())
        session_id = 1
        uplink_port = ['46']
        downlink_port = ['48']

        ts1 = (
            TrafficSegmentation(cfg.leaf0['id'])
            .session(session_id)
            .uplinks(uplink_port)
            .downlinks(downlink_port)
            .build()
        )

        cfg.host0['ip'] = '192.168.10.10'
        cfg.host0['ip'] = '192.168.10.20'

        pkt_from_p1_to_p0 = simple_tcp_packet(
            pktlen=64,
            eth_dst=cfg.host1['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host1['ip'],
            ip_src=cfg.host0['ip']
        )

        self.dataplane.send(ports[1], str(pkt_from_p1_to_p0))
        verify_packet(self, str(pkt_from_p1_to_p0), ports[0])

        ts1.delete()


class TelnetTest(TrafficSegmentationTest):
    """
    Test one session with leaf type
    """

    def runTest(self):
        child = pexpect.spawn('telnet 192.168.40.109')
        i = 0
        while (i < 5):
            index = child.expect(
                ['Username:', 'Password:', '#', pexpect.EOF, pexpect.TIMEOUT])
            print index
            if (index == 0):
                child.sendline('admin')
            elif (index == 1):
                child.sendline('admin')
            elif (index == 2):
                child.sendline('\r')
            else:
                child.close()

            i = i + 1

        child.expect(['#'])
        print '------------------------------'
        child.sendline('show traffic-segmentation')
        i = 0
        while (i < 5):
            index = child.expect(
                ['Others to exit ---', '#', pexpect.EOF, pexpect.TIMEOUT])
            print index
            if (index == 0):
                child.sendline('a')
            elif (index == 1):
                child.sendline('\r')

            i = i + 1

        print child.before
        print '------------------------------'
        child.close()

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
from oftest import config
from oftest.testutils import *
from utils import *

URL = cfg.API_BASE_URL
LOGIN = cfg.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}


class VRF(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)


class MultipleTenant(VRF):
    """
    Test multiple tenant with VRF feature
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        s1_ip = '192.168.10.1'
        s2_ip = '192.168.20.1'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_ip], 100)
            .segment_member(SegmentMember('s1', cfg.leaf0['id']).ports([cfg.leaf0['portC'].name]))
            .segment('s2', 'vlan', [s2_ip], 200)
            .segment_member(SegmentMember('s2', cfg.leaf1['id']).ports([cfg.leaf1['portC'].name]))
            .build()
        )

        t2 = (
            Tenant('t2')
            .segment('s1', 'vlan', [s1_ip], 101)
            .segment_member(SegmentMember('s1', cfg.leaf0['id']).ports([cfg.leaf0['portD'].name]))
            .segment('s2', 'vlan', [s2_ip], 201)
            .segment_member(SegmentMember('s2', cfg.leaf1['id']).ports([cfg.leaf1['portD'].name]))
            .build()
        )

        wait_for_system_stable()

        lrouter_r1 = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .build()
        )

        wait_for_system_stable()

        lrouter_r2 = (
            LogicalRouter('r2', 't2')
            .interfaces(['s1', 's2'])
            .build()
        )

        wait_for_system_stable()

        cfg.host0['ip'] = '192.168.10.10'
        cfg.host1['ip'] = '192.168.20.10'
        cfg.host2['ip'] = '192.168.10.20'
        cfg.host3['ip'] = '192.168.20.20'

        testhost_configuration()

        route_add(cfg.host0, '192.168.20.0', s1_ip)
        route_add(cfg.host1, '192.168.10.0', s2_ip)
        route_add(cfg.host2, '192.168.20.0', s1_ip)
        route_add(cfg.host3, '192.168.10.0', s2_ip)

        ping_result = ping_test(cfg.host0, cfg.host1['ip'])

        assert(ping_verify('64 bytes from ' +
                           cfg.host1['ip'], ping_result))

        ping_result1 = ping_test(cfg.host2, cfg.host3['ip'])

        assert(ping_verify('64 bytes from ' +
                           cfg.host3['ip'], ping_result1))

        lrouter_r1.destroy()
        lrouter_r2.destroy()
        t1.destroy()
        t2.destroy()

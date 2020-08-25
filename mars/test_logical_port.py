"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test Tenants RestAPI.

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

p0: port A of leaf0
p1: port B of leaf0
p2: port A of leaf1
p3: port B of leaf1
"""

import oftest.base_tests as base_tests
from oftest import config
from oftest.testutils import *
import config as cfg
import requests
import time
import utils
from utils import *


class LogicalPortTest(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)


class SetterAndGetter(LogicalPortTest):
    """
    Test logical port setter and getter
    """

    def runTest(self):
        lp1 = (
            LogicalPort('lp1')
            .group(1)
            .members([{"device_id": cfg.leaf0['id'], "port": 5}])
            .build()
        )

        actual_lp1 = lp1.get()

        assert(actual_lp1['name'] == 'lp1')
        assert(actual_lp1['group'] == 1)
        assert(actual_lp1['members'][0]['device_id'] == cfg.leaf0['id'])
        assert(actual_lp1['members'][0]['port'] == 5)

        lp2 = (
            LogicalPort('lp2')
            .group(2)
            .members([
                {"device_id": cfg.leaf0['id'], "port": 10},
                {"device_id": cfg.leaf0['id'], "port": 11}
            ])
            .build()
        )

        actual_lp2 = lp2.get()

        assert(actual_lp2['name'] == 'lp2')
        assert(actual_lp2['group'] == 2)
        assert(actual_lp2['members'][0]['device_id'] == cfg.leaf0['id'])
        assert(actual_lp2['members'][1]['device_id'] == cfg.leaf0['id'])
        assert(set([actual_lp2['members'][0]['port'],
                    actual_lp2['members'][1]['port']]) == set([10, 11]))

        lp1.delete()
        lp2.delete()


class LeafCondition(LogicalPortTest):
    """
    Test logical port for leaf and confirm switch's status
    """

    def runTest(self):
        lp1 = (
            LogicalPort('lp1')
            .group(1)
            .members([
                {"device_id": cfg.leaf1['id'], "port": 15},
                {"device_id": cfg.leaf1['id'], "port": 16}
            ])
            .build()
        )

        wait_for_seconds(2)

        sw_lp1 = SwitchLogicalPort(cfg.leaf1)
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

        lp1.delete()
        lp2.delete()


class SpineCondition(LogicalPortTest):
    """
    Test logical port for spine and confirm switch's status
    """

    def runTest(self):
        lp1 = (
            LogicalPort('lp1')
            .group(6)
            .members([
                {"device_id": cfg.spine0['id'], "port": 25},
                {"device_id": cfg.spine0['id'], "port": 26}
            ])
            .build()
        )

        wait_for_seconds(2)

        sw_lp1 = SwitchLogicalPort(cfg.spine0)
        switch_actual_lp1 = sw_lp1.get_portchannel(6)['result']

        assert(switch_actual_lp1['id'] == 6)
        assert(set(switch_actual_lp1['members']) == set([25, 26]))

        lp1.delete()


class MaxNumberGroup(LogicalPortTest):
    """
    Test logical port with maxmium number group for each device
    """

    def runTest(self):
        lp1 = (
            LogicalPort('lp1')
            .group(1)
            .members([
                {"device_id": cfg.leaf0['id'], "port": 1},
                {"device_id": cfg.leaf0['id'], "port": 2}
            ])
            .build()
        )

        lp2 = (
            LogicalPort('lp2')
            .group(2)
            .members([
                {"device_id": cfg.leaf0['id'], "port": 3},
                {"device_id": cfg.leaf0['id'], "port": 4}
            ])
            .build()
        )

        lp3 = (
            LogicalPort('lp3')
            .group(3)
            .members([
                {"device_id": cfg.leaf0['id'], "port": 5},
                {"device_id": cfg.leaf0['id'], "port": 6}
            ])
            .build()
        )

        lp4 = (
            LogicalPort('lp4')
            .group(4)
            .members([
                {"device_id": cfg.leaf0['id'], "port": 7},
                {"device_id": cfg.leaf0['id'], "port": 8}
            ])
            .build()
        )

        lp5 = (
            LogicalPort('lp5')
            .group(5)
            .members([
                {"device_id": cfg.leaf0['id'], "port": 9},
                {"device_id": cfg.leaf0['id'], "port": 10}
            ])
            .build()
        )

        lp6 = (
            LogicalPort('lp6')
            .group(6)
            .members([
                {"device_id": cfg.leaf0['id'], "port": 11},
                {"device_id": cfg.leaf0['id'], "port": 12}
            ])
            .build()
        )

        wait_for_seconds(2)

        sw_lp = SwitchLogicalPort(cfg.leaf0)
        switch_actual_lp1 = sw_lp.get_portchannel(1)['result']
        switch_actual_lp2 = sw_lp.get_portchannel(2)['result']
        switch_actual_lp3 = sw_lp.get_portchannel(3)['result']
        switch_actual_lp4 = sw_lp.get_portchannel(4)['result']
        switch_actual_lp5 = sw_lp.get_portchannel(5)['result']
        switch_actual_lp6 = sw_lp.get_portchannel(6)['result']

        assert(switch_actual_lp1['id'] == 1)
        assert(set(switch_actual_lp1['members']) == set([1, 2]))
        assert(switch_actual_lp2['id'] == 2)
        assert(set(switch_actual_lp2['members']) == set([3, 4]))
        assert(switch_actual_lp3['id'] == 3)
        assert(set(switch_actual_lp3['members']) == set([5, 6]))
        assert(switch_actual_lp4['id'] == 4)
        assert(set(switch_actual_lp4['members']) == set([7, 8]))
        assert(switch_actual_lp5['id'] == 5)
        assert(set(switch_actual_lp5['members']) == set([9, 10]))
        assert(switch_actual_lp6['id'] == 6)
        assert(set(switch_actual_lp6['members']) == set([11, 12]))

"""
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


class Stability(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)


class SpineChange(Stability):
    '''
    Test topology while spine changed
    '''

    def runTest(self):
        d0 = Device(cfg.spine0['id'])
        d1 = Device(cfg.spine1['id'])

        assert d0.available, "d0 device's avaiable shall be true"
        assert d1.available, "d1 device's avaiable shall be true"

        rp_spine0 = RemotePower(cfg.spine0_power)
        rp_spine1 = RemotePower(cfg.spine1_power)

        # turn off spine0
        rp_spine0.Off()
        wait_for_seconds(60)
        rp_spine0.On()

        assert d0.available == False, "d0 device's avaiable shall be false"

        links_inspect([cfg.spine1], [cfg.leaf0, cfg.leaf1])

        assert d1.available, "d1 device's avaiable shall be true"

        # wait for spine0 resume
        links_inspect([cfg.spine0, cfg.spine1], [cfg.leaf0, cfg.leaf1])

        assert d0.available, "d0 device's avaiable shall be true"
        assert d1.available, "d1 device's avaiable shall be true"

        # turn off spine1
        rp_spine1.Off()
        wait_for_seconds(60)
        rp_spine1.On()

        links_inspect([cfg.spine0], [cfg.leaf0, cfg.leaf1])

        assert d0.available, "d1 device's avaiable shall be true"

        # wait for spine1 resume
        links_inspect([cfg.spine0, cfg.spine1], [cfg.leaf0, cfg.leaf1])

        assert d0.available, "d0 device's avaiable shall be true"
        assert d1.available, "d1 device's avaiable shall be true"


class LeafChange(Stability):
    '''
    Test topology while leaf changed
    '''

    def runTest(self):
        d0 = Device(cfg.leaf0['id'])
        d1 = Device(cfg.leaf1['id'])

        assert d0.available, "d0 device's avaiable shall be true"
        assert d1.available, "d1 device's avaiable shall be true"

        rp_leaf0 = RemotePower(cfg.leaf0_power)
        rp_leaf1 = RemotePower(cfg.leaf1_power)

        # turn off leaf0
        rp_leaf0.Off()
        wait_for_seconds(60)
        rp_leaf0.On()

        assert d0.available == False, "d0 device's avaiable shall be false"

        links_inspect([cfg.spine0, cfg.spine1], [cfg.leaf1])

        assert d1.available, "d1 device's avaiable shall be true"

        # wait for leaf0 resume
        links_inspect([cfg.spine0, cfg.spine1], [cfg.leaf0, cfg.leaf1])

        assert d0.available, "d0 device's avaiable shall be true"
        assert d1.available, "d1 device's avaiable shall be true"

        # turn off leaf1
        rp_leaf1.Off()
        wait_for_seconds(60)
        rp_leaf1.On()

        links_inspect([cfg.spine0, cfg.spine1], [cfg.leaf0])

        assert d0.available, "d1 device's avaiable shall be true"

        # wait for leaf1 resume
        links_inspect([cfg.spine0, cfg.spine1], [cfg.leaf0, cfg.leaf1])

        assert d0.available, "d0 device's avaiable shall be true"
        assert d1.available, "d1 device's avaiable shall be true"

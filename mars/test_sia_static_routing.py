"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test SIA static routing

Test environment

               +------+65       49+-------+51
               | 6700 +-----------+ 4610*1+------>PC0
               +------+           +-------+
                 66|
                   |
                 47|
             43+------+34
     +---------+ 5812 +----------+
     |         +------+          |
     |           33|             |
     |             |             |
   49|           25|           49|
 +-------+     +-------+     +-------+1   1+-------+
 | 4610*2|     | 4610*3|     | 4610*4+-----+ 4100  |
 +-------+     +-------+     +-------+     +-------+
23|   50|     27|   28|        51|         9|   10|
  |     |       |     |          |          |     |
  v     v       v     v          v          v     v
 PC6   PC5     PC1   PC4        PC2        PC3   PC7


mgmt ip address
PC0: 192.168.40.120     4610*1: sw46*223
PC1: 192.168.40.63      4610*2: sw46*185
PC2: 192.168.40.118     4610*3: sw46*126
PC3: 192.168.40.115     4610*4: sw46*188
PC4: 192.168.40.83
PC5: 192.168.40.103
PC6: 192.168.40.119
PC7: 192.168.40.30

"""


import oftest.base_tests as base_tests
import config as cfg
import requests
import time
import utils
from oftest import config
from oftest.testutils import *
from utils import *

host0 = {
    'id': 'host0',
    'mac': '24:6e:96:05:07:4a',
    'ip': '192.168.2.118',
    'mgmt_ip': '192.168.40.118',
    'username': 'mars',
    'password': 'accton',
    'nic_name': 'enp1s0'
}

host1 = {
    'id': 'host1',
    'mac': '24:6e:96:05:07:4d',
    'ip': '192.168.0.119',
    'mgmt_ip': '192.168.40.119',
    'username': 'mars',
    'password': 'accton',
    'nic_name': 'enp1s0'
}

host2 = {
    'id': 'host2',
    'mac': '90:e2:ba:24:79:84',
    'ip': '192.168.5.103',
    'mgmt_ip': '192.168.40.103',
    'username': 'mars',
    'password': 'accton',
    'nic_name': 'enp1s0'
}

host3 = {
    'id': 'host3',
    'mac': '24:6e:96:05:07:48',
    'ip': '192.168.253.120',
    'mgmt_ip': '192.168.40.120',
    'username': 'mars',
    'password': 'accton',
    'nic_name': 'enp1s0'
}

host4 = {
    'id': 'host4',
    'mac': '90:e2:ba:24:a1:34',
    'ip': '192.168.0.83',
    'mgmt_ip': '192.168.40.83',
    'username': 'mars',
    'password': 'accton',
    'nic_name': 'enp1s0'
}

host5 = {
    'id': 'host5',
    'mac': '90:e2:ba:24:a0:86',
    'ip': '192.168.0.63',
    'mgmt_ip': '192.168.40.63',
    'username': 'mars',
    'password': 'accton',
    'nic_name': 'enp1s0'
}

host6 = {
    'id': 'host6',
    'mac': '24:6e:96:04:e1:15',
    'ip': '192.168.0.115',
    'mgmt_ip': '192.168.40.115',
    'username': 'mars',
    'password': 'accton',
    'nic_name': 'ens16'
}

host7 = {
    'id': 'host7',
    'mac': '24:6e:96:05:0c:cd',
    'ip': '192.168.0.30',
    'mgmt_ip': '192.168.40.30',
    'username': 'mars',
    'password': 'accton',
    'nic_name': 'enp6s16'
}

untag_cmd_list = [
    ("config", "#"),
    ("int eth 1/9", "#"),
    ("switchport allowed vlan add 60 untagged", "#"),
    ("int eth 1/10", "#"),
    ("switchport allowed vlan add 70 untagged", "#"),
]

tag_cmd_list = [
    ("config", "#"),
    ("int eth 1/9", "#"),
    ("switchport allowed vlan add 60 tagged", "#"),
    ("int eth 1/10", "#"),
    ("switchport allowed vlan add 70 tagged", "#"),
]


class SIAStaticRouting(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)
        sia_clear_env([cfg.sw67_205])

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)


# class RebootSwitchProcess(SIAStaticRouting):
#     """
#     Reboot all switches
#     """

#     def runTest(self):
#         reboot_switch_list = [
#             RebootSwitch(cfg.sw46_188['id']),
#             RebootSwitch(cfg.sw67_205['id'])
#         ]

#         for switch in reboot_switch_list:
#             switch.reboot()


class UntagHostWithDifferentSubnetInDifferentLeaf(SIAStaticRouting):
    """
    Test untagged host static routing
    """

    def runTest(self):
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 2,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_188['front_port_A']]
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': 10,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_185['front_port_A']]
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 2, ["192.168.2.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 10, ["192.168.0.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        host0['ip'] = '192.168.2.118'
        host1['ip'] = '192.168.0.119'

        h0 = Host(host0).set_ip()
        h1 = Host(host1).set_ip()

        assert('success' == h0.ping(host1['ip']))


class UntagHostWithDifferentSubnetInSameLeaf(SIAStaticRouting):
    """
    Test untagged host static routing
    """

    def runTest(self):
        host1_vlan = 8
        host2_vlan = 20

        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': host1_vlan,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_185['front_port_A']]
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': host2_vlan,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_185['front_port_B']]
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], host1_vlan, ["192.168.8.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], host2_vlan, ["192.168.20.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        host1['ip'] = '192.168.8.119'
        host2['ip'] = '192.168.20.103'

        h1 = Host(host1).set_ip()
        h2 = Host(host2).set_ip()

        assert('success' == h1.ping(host2['ip']))

        sr1.del_host_vlan(cfg.sw46_185['id'], 8)

        host_vlan_cfg1['vlanId'] = 18

        sr2 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 18, ["192.168.18.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .build()
        )

        host1['ip'] = '192.168.18.119'

        h1 = Host(host1).set_ip()

        assert('success' == h2.ping(host1['ip']))


class UntagHostWithSameSubnetInDifferentLeaf(SIAStaticRouting):
    """
    Test untagged host static routing with same subnet in different leaf
    """

    def runTest(self):
        # no vlan test
        host0['ip'] = '192.168.0.118'
        host1['ip'] = '192.168.0.119'

        h0 = Host(host0).set_ip()
        h1 = Host(host1).set_ip()

        assert('success' == h0.ping(host1['ip']))

        # vlan test
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 2,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_188['front_port_A']]
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': 10,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_185['front_port_A']]
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 10, ["192.168.0.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        assert('success' == h0.ping(host1['ip']))


class UntagHostWithSameSubnetInSameLeaf(SIAStaticRouting):
    """
    Test untagged host static routing with same subnet in same leaf
    """

    def runTest(self):
        # no vlan test
        host1['ip'] = '192.168.10.119'
        host2['ip'] = '192.168.10.103'

        h1 = Host(host1).set_ip()
        h2 = Host(host2).set_ip()

        assert('success' == h1.ping(host2['ip']))

        # vlan test
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': 10,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_185['front_port_A']]
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': 10,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_185['front_port_B']]
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 10, ["192.168.10.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        assert('success' == h1.ping(host2['ip']))


class TagHostWithDifferentSubnetInDifferentLeaf(SIAStaticRouting):
    """
    Test tagged host static routing with different subnet in different leaf
    """

    def runTest(self):
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 2,
            'tagPorts': [cfg.sw46_188['front_port_A']],
            'untagPorts': []
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': 10,
            'tagPorts': [cfg.sw46_185['front_port_A']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 2, ["192.168.2.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 10, ["192.168.0.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        host0['ip'] = '192.168.2.118'
        host1['ip'] = '192.168.0.119'

        h0 = Host(host0).set_ip(vlan=2)
        h1 = Host(host1).set_ip(vlan=10)

        assert('success' == h0.ping(host1['ip']))


class TagHostWithDifferentSubnetInSameLeaf(SIAStaticRouting):
    """
    Test untagged host static routing
    """

    def runTest(self):
        host1_vlan = 8
        host2_vlan = 20

        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': host1_vlan,
            'tagPorts': [cfg.sw46_185['front_port_A']],
            'untagPorts': []
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': host2_vlan,
            'tagPorts': [cfg.sw46_185['front_port_B']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], host1_vlan, ["192.168.8.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], host2_vlan, ["192.168.20.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        host1['ip'] = '192.168.8.119'
        host2['ip'] = '192.168.20.103'

        h1 = Host(host1).set_ip(vlan=8)
        h2 = Host(host2).set_ip(vlan=20)

        assert('success' == h1.ping(host2['ip']))

        sr1.del_host_vlan(cfg.sw46_185['id'], 8)

        host_vlan_cfg1['vlanId'] = 18

        sr2 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 18, ["192.168.18.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .build()
        )

        host1['ip'] = '192.168.18.119'
        h1 = Host(host1).set_ip(vlan=18)

        assert('success' == h2.ping(host1['ip']))


class TagHostWithSameSubnetInDifferentLeaf(SIAStaticRouting):
    """
    Test tagged host static routing with same subnet in different leaf
    """

    def runTest(self):
        # no vlan test
        host0['ip'] = '192.168.0.118'
        host1['ip'] = '192.168.0.119'

        h0 = Host(host0).set_ip(vlan=100)
        h1 = Host(host1).set_ip(vlan=100)

        assert('success' == h0.ping(host1['ip']))

        # vlan test
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 100,
            'tagPorts': [cfg.sw46_188['front_port_A']],
            'untagPorts': []
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': 100,
            'tagPorts': [cfg.sw46_185['front_port_A']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 100, ["192.168.0.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        assert('success' == h0.ping(host1['ip']))


class TagHostWithSameSubnetInSameLeaf(SIAStaticRouting):
    """
    Test tagged host static routing with same subnet in same leaf
    """

    def runTest(self):
        # no vlan test
        host1['ip'] = '192.168.200.119'
        host2['ip'] = '192.168.200.103'

        h1 = Host(host1).set_ip(vlan=200)
        h2 = Host(host2).set_ip(vlan=200)

        assert('success' == h1.ping(host2['ip']))

        # vlan test
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': 200,
            'tagPorts': [cfg.sw46_185['front_port_A'], cfg.sw46_185['front_port_B']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 200, ["192.168.200.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .build()
        )

        assert('success' == h1.ping(host2['ip']))


class UntagClientToServerWithSameSubnet(SIAStaticRouting):
    """
    Test untag client to server with same subnet
    """

    def runTest(self):
        # no vlan test
        host2['ip'] = '192.168.50.103'
        host3['ip'] = '192.168.50.117'

        h2 = Host(host2).set_ip()
        h3 = Host(host3).set_ip()

        assert('success' == h2.ping(host3['ip']))

        # vlan test
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': 50,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_185['front_port_B']]
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_223['id'],
            'vlanId': 50,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_223['front_port_A']]
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 50, ["192.168.50.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        assert('success' == h2.ping(host3['ip']))


class UntagClientToServerWithDifferentSubnet(SIAStaticRouting):
    """
    Test untag client to server with different subnet
    """

    def runTest(self):
        host2['ip'] = '192.168.5.103'
        host3['ip'] = '192.168.253.120'

        h2 = Host(host2).set_ip()
        h3 = Host(host3).set_ip()

        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': 5,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_185['front_port_B']]
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_223['id'],
            'vlanId': 253,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_223['front_port_A']]
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 5, ["192.168.5.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 253, ["192.168.253.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        assert('success' == h2.ping(host3['ip']))


class TagClientToServerWithSameSubnet(SIAStaticRouting):
    """
    Test tag client to server with same subnet
    """

    def runTest(self):
        # no vlan test
        host2['ip'] = '192.168.60.103'
        host3['ip'] = '192.168.60.117'

        h2 = Host(host2).set_ip(vlan=60)
        h3 = Host(host3).set_ip(vlan=60)

        assert('success' == h2.ping(host3['ip']))

        # vlan test
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': 60,
            'tagPorts': [cfg.sw46_185['front_port_B']],
            'untagPorts': []
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_223['id'],
            'vlanId': 60,
            'tagPorts': [cfg.sw46_223['front_port_A']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 60, ["192.168.60.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        assert('success' == h2.ping(host3['ip']))


class TagClientToServerWithDifferentSubnet(SIAStaticRouting):
    """
    Test tag client to server with different subnet
    """

    def runTest(self):
        host2['ip'] = '192.168.5.103'
        host3['ip'] = '192.168.253.120'

        h2 = Host(host2).set_ip(vlan=5)
        h3 = Host(host3).set_ip(vlan=253)

        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': 5,
            'tagPorts': [cfg.sw46_185['front_port_B']],
            'untagPorts': []
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_223['id'],
            'vlanId': 253,
            'tagPorts': [cfg.sw46_223['front_port_A']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 5, ["192.168.5.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 253, ["192.168.253.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        assert('success' == h2.ping(host3['ip']))


class UntagHostWithSameSubnetInSameLeafFor30T(SIAStaticRouting):
    """
    Test untag host with same subnet in same leaf for 4610-30T
    """

    def runTest(self):
        # no vlan test
        host4['ip'] = '192.168.0.83'
        host5['ip'] = '192.168.0.63'

        h4 = Host(host4).set_ip()
        h5 = Host(host5).set_ip()

        assert('success' == h4.ping(host5['ip']))

        # vlan test
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_126['id'],
            'vlanId': 55,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_126['front_port_A'], cfg.sw46_126['front_port_B']]
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 55, ["192.168.0.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .build()
        )

        assert('success' == h4.ping(host5['ip']))


class UntagHostWithSameSubnetInDifferentLeafFor30T(SIAStaticRouting):
    """
    Test untag host with same subnet in different leaf for 4610-30T
    """

    def runTest(self):
        # no vlan test
        host0['ip'] = '192.168.0.118'
        host1['ip'] = '192.168.0.119'
        host3['ip'] = '192.168.0.120'
        host4['ip'] = '192.168.0.83'
        host5['ip'] = '192.168.0.63'

        h0 = Host(host0).set_ip()
        h1 = Host(host1).set_ip()
        h3 = Host(host3).set_ip()
        h4 = Host(host4).set_ip()
        h5 = Host(host5).set_ip()

        assert('success' == h4.ping(host0['ip']))
        assert('success' == h4.ping(host1['ip']))
        assert('success' == h4.ping(host3['ip']))
        assert('success' == h4.ping(host5['ip']))

        # vlan test
        vlan_id = 155
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_126['id'],
            'vlanId': vlan_id,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_126['front_port_B']]
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': vlan_id,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_188['front_port_A']]
        }

        host_vlan_cfg3 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': vlan_id,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_185['front_port_A']]
        }

        host_vlan_cfg4 = {
            'deviceId': cfg.sw46_223['id'],
            'vlanId': vlan_id,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_223['front_port_A']]
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], vlan_id, ["192.168.0.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .add_host_vlan(host_vlan_cfg3)
            .add_host_vlan(host_vlan_cfg4)
            .build()
        )

        assert('success' == h4.ping(host0['ip']))
        assert('success' == h4.ping(host1['ip']))
        assert('success' == h4.ping(host3['ip']))
        # assert('failure' == h4.ping(host5['ip']))


class TagHostWithSameSubnetInSameLeafFor30T(SIAStaticRouting):
    """
    Test tag host with same subnet in same leaf for 4610-30T
    """

    def runTest(self):
        host4['ip'] = '192.168.10.83'
        host5['ip'] = '192.168.10.63'

        h4 = Host(host4).set_ip(vlan=10)
        h5 = Host(host5).set_ip(vlan=10)

        assert('success' == h4.ping(host5['ip']))

        # vlan test
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_126['id'],
            'vlanId': 10,
            'tagPorts': [cfg.sw46_126['front_port_A'], cfg.sw46_126['front_port_B']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 10, ["192.168.10.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .build()
        )

        assert('success' == h4.ping(host5['ip']))


class TagHostWithSameSubnetInDifferentLeafFor30T(SIAStaticRouting):
    """
    Test tag host with same subnet in different leaf for 4610-30T
    """

    def runTest(self):
        host0['ip'] = '192.168.0.118'
        host1['ip'] = '192.168.0.119'
        host3['ip'] = '192.168.0.120'
        host4['ip'] = '192.168.0.83'
        host5['ip'] = '192.168.0.63'

        h0 = Host(host0).set_ip(vlan=100)
        h1 = Host(host1).set_ip(vlan=100)
        h3 = Host(host3).set_ip(vlan=100)
        h4 = Host(host4).set_ip(vlan=100)
        h5 = Host(host5).set_ip()

        assert('success' == h4.ping(host0['ip']))
        assert('success' == h4.ping(host1['ip']))
        assert('success' == h4.ping(host3['ip']))
        # assert('failure' == h4.ping(host5['ip']))

        # vlan test
        vlan_id = 100
        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_126['id'],
            'vlanId': vlan_id,
            'tagPorts': [cfg.sw46_126['front_port_B']],
            'untagPorts': []
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': vlan_id,
            'tagPorts': [cfg.sw46_188['front_port_A']],
            'untagPorts': []
        }

        host_vlan_cfg3 = {
            'deviceId': cfg.sw46_185['id'],
            'vlanId': vlan_id,
            'tagPorts': [cfg.sw46_185['front_port_A']],
            'untagPorts': []
        }

        host_vlan_cfg4 = {
            'deviceId': cfg.sw46_223['id'],
            'vlanId': vlan_id,
            'tagPorts': [cfg.sw46_223['front_port_A']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], vlan_id, ["192.168.0.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .add_host_vlan(host_vlan_cfg3)
            .add_host_vlan(host_vlan_cfg4)
            .build()
        )

        assert('success' == h4.ping(host0['ip']))
        assert('success' == h4.ping(host1['ip']))
        assert('success' == h4.ping(host3['ip']))
        # assert('failure' == h4.ping(host5['ip']))


class UntagHostWithLegacySwitchInTagLeafPort_ClientToServer(SIAStaticRouting):
    """
    Test untag host with legacy switch in tag leaf port
    """

    def runTest(self):
        telnet_and_execute(cfg.legacy_1['mgmtIpAddress'], untag_cmd_list)

        host3['ip'] = '192.168.253.120'
        host5['ip'] = '192.168.10.63'
        host6['ip'] = '192.168.60.115'

        h3 = Host(host3).set_ip()
        h5 = Host(host5).set_ip()
        h6 = Host(host6).set_ip()

        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 60,
            'tagPorts': [cfg.sw46_188['front_port_B']],
            'untagPorts': []
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_223['id'],
            'vlanId': 253,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_223['front_port_A']]
        }

        host_vlan_cfg3 = {
            'deviceId': cfg.sw46_126['id'],
            'vlanId': 10,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_126['front_port_A']]
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 253, ["192.168.253.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 60, ["192.168.60.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 10, ["192.168.10.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .add_host_vlan(host_vlan_cfg3)
            .build()
        )

        assert('success' == h5.ping(host3['ip']))
        assert('success' == h6.ping(host3['ip']))


class UntagHostWithLegacySwitchInTagLeafPort_SameSubnet(SIAStaticRouting):
    """
    Test untag host with legacy switch in tag leaf port
    """

    def runTest(self):
        telnet_and_execute(cfg.legacy_1['mgmtIpAddress'], untag_cmd_list)

        host0['ip'] = '192.168.60.118'
        host6['ip'] = '192.168.60.115'
        host7['ip'] = '192.168.70.30'

        h0 = Host(host0).set_ip()
        h6 = Host(host6).set_ip()
        h7 = Host(host7).set_ip()

        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 60,
            'tagPorts': [cfg.sw46_188['front_port_B']],
            'untagPorts': [cfg.sw46_188['front_port_A']]
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 70,
            'tagPorts': [cfg.sw46_188['front_port_B']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 60, ["192.168.60.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 70, ["192.168.70.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        assert('success' == h7.ping(host6['ip']))
        assert('success' == h6.ping(host0['ip']))


class UntagHostWithLegacySwitchInTagLeafPort_DifferentSubnet(SIAStaticRouting):
    """
    Test untag host with legacy switch in tag leaf port
    """

    def runTest(self):
        telnet_and_execute(cfg.legacy_1['mgmtIpAddress'], untag_cmd_list)

        host0['ip'] = '192.168.90.118'
        host6['ip'] = '192.168.60.115'
        host7['ip'] = '192.168.70.30'

        h0 = Host(host0).set_ip()
        h6 = Host(host6).set_ip()
        h7 = Host(host7).set_ip()

        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 60,
            'tagPorts': [cfg.sw46_188['front_port_B']],
            'untagPorts': []
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 70,
            'tagPorts': [cfg.sw46_188['front_port_B']],
            'untagPorts': []
        }

        host_vlan_cfg3 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 90,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_188['front_port_A']]
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 60, ["192.168.60.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 70, ["192.168.70.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 90, ["192.168.90.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .add_host_vlan(host_vlan_cfg3)
            .build()
        )

        assert('success' == h7.ping(host6['ip']))
        assert('success' == h7.ping(host0['ip']))


class TagHostWithLegacySwitchInTagLeafPort_ClientToServer(SIAStaticRouting):
    """
    Test tag host with legacy switch in tag leaf port
    """

    def runTest(self):
        telnet_and_execute(cfg.legacy_1['mgmtIpAddress'], tag_cmd_list)

        host3['ip'] = '192.168.253.120'
        host5['ip'] = '192.168.10.63'
        host6['ip'] = '192.168.60.115'

        h3 = Host(host3).set_ip()
        h5 = Host(host5).set_ip(vlan=10)
        h6 = Host(host6).set_ip(vlan=60)

        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 60,
            'tagPorts': [cfg.sw46_188['front_port_B']],
            'untagPorts': []
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_223['id'],
            'vlanId': 253,
            'tagPorts': [],
            'untagPorts': [cfg.sw46_223['front_port_A']]
        }

        host_vlan_cfg3 = {
            'deviceId': cfg.sw46_126['id'],
            'vlanId': 10,
            'tagPorts': [cfg.sw46_126['front_port_A']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 253, ["192.168.253.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 60, ["192.168.60.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 10, ["192.168.10.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .add_host_vlan(host_vlan_cfg3)
            .build()
        )

        assert('success' == h5.ping(host3['ip']))
        assert('success' == h6.ping(host3['ip']))


class TagHostWithLegacySwitchInTagLeafPort_SameSubnet(SIAStaticRouting):
    """
    Test tag host with legacy switch in tag leaf port
    """

    def runTest(self):
        telnet_and_execute(cfg.legacy_1['mgmtIpAddress'], tag_cmd_list)

        host0['ip'] = '192.168.60.118'
        host6['ip'] = '192.168.60.115'
        host7['ip'] = '192.168.70.30'

        h0 = Host(host0).set_ip(vlan=60)
        h6 = Host(host6).set_ip(vlan=60)
        h7 = Host(host7).set_ip(vlan=70)

        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 60,
            'tagPorts': [cfg.sw46_188['front_port_B'], cfg.sw46_188['front_port_A']],
            'untagPorts': []
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 70,
            'tagPorts': [cfg.sw46_188['front_port_B']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 60, ["192.168.60.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 70, ["192.168.70.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .build()
        )

        assert('success' == h7.ping(host6['ip']))
        assert('success' == h6.ping(host0['ip']))


class TagHostWithLegacySwitchInTagLeafPort_DifferentSubnet(SIAStaticRouting):
    """
    Test tag host with legacy switch in tag leaf port
    """

    def runTest(self):
        telnet_and_execute(cfg.legacy_1['mgmtIpAddress'], tag_cmd_list)

        host0['ip'] = '192.168.90.118'
        host6['ip'] = '192.168.60.115'
        host7['ip'] = '192.168.70.30'

        h0 = Host(host0).set_ip(vlan=90)
        h6 = Host(host6).set_ip(vlan=60)
        h7 = Host(host7).set_ip(vlan=70)

        host_vlan_cfg1 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 60,
            'tagPorts': [cfg.sw46_188['front_port_B']],
            'untagPorts': []
        }

        host_vlan_cfg2 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 70,
            'tagPorts': [cfg.sw46_188['front_port_B']],
            'untagPorts': []
        }

        host_vlan_cfg3 = {
            'deviceId': cfg.sw46_188['id'],
            'vlanId': 90,
            'tagPorts': [cfg.sw46_188['front_port_A']],
            'untagPorts': []
        }

        sr1 = (
            StaticRouting()
            .add_switch_vlan(cfg.sw67_205['id'], 60, ["192.168.60.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 70, ["192.168.70.254/24"])
            .add_switch_vlan(cfg.sw67_205['id'], 90, ["192.168.90.254/24"])
            .add_host_vlan(host_vlan_cfg1)
            .add_host_vlan(host_vlan_cfg2)
            .add_host_vlan(host_vlan_cfg3)
            .build()
        )

        assert('success' == h7.ping(host6['ip']))
        assert('success' == h7.ping(host0['ip']))

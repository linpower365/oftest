"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test QoS Policy RestAPI.
"""


import oftest.base_tests as base_tests
import config as cfg
import requests
import time
import random
import auth
from utils import *


class QoSPolicyTest(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        # setup_configuration()
        # port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)


class SingleDeviceClassMapPostTest(QoSPolicyTest):
    """
    Test class map POST API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classA')
            .device(cfg.leaf0['id'])
            .match('dscp', 34)
            .create()
        )

        class_map = ClassMap(class_map_cfg)

        assert class_map.retrieve() == []
        class_map.create()
        assert class_map.retrieve() == [
            {'matches': [{'type': 'dscp', 'option': 34}], 'name': 'classA'}]

        # clear
        class_map.delete()


class SingleDeviceClassMapGetTest(QoSPolicyTest):
    """
    Test class map GET API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classB')
            .device(cfg.leaf0['id'])
            .match('vlan', 10)
            .create()
        )

        class_map = ClassMap(class_map_cfg)

        assert class_map.retrieve() == []
        class_map.create()
        assert class_map.retrieve() == [
            {'matches': [{'type': 'vlan', 'option': 10}], 'name': 'classB'}]

        # clear
        class_map.delete()


class SingleDeviceClassMapDeleteTest(QoSPolicyTest):
    """
    Test class map DELETE API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classB')
            .device(cfg.leaf0['id'])
            .match('cos', 5)
            .create()
        )

        class_map = ClassMap(class_map_cfg)

        assert class_map.retrieve() == []
        class_map.create()
        assert class_map.retrieve() == [
            {'matches': [{'type': 'cos', 'option': 5}], 'name': 'classB'}]
        class_map.delete()
        assert class_map.retrieve() == []


class SingleDeviceClassMapPutTest(QoSPolicyTest):
    """
    Test class map PUT API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classC')
            .device(cfg.leaf0['id'])
            .match('precedence', 1)
            .create()
        )

        class_map = ClassMap(class_map_cfg)
        class_map.create()
        assert class_map.retrieve() == [
            {'matches': [{'type': 'precedence', 'option': 1}], 'name': 'classC'}]

        new_class_map_cfg = (
            ClassMapCfg('classC')
            .device(cfg.leaf0['id'])
            .match('vlan', 2)
            .create()
        )

        class_map.update(new_class_map_cfg)
        assert class_map.retrieve() == [
            {'matches': [{'type': 'vlan', 'option': 2}], 'name': 'classC'}]

        # clear
        class_map.delete()


class MultipleDeviceClassMapPostTest(QoSPolicyTest):
    """
    Test class map POST API for multiple device
    """

    def runTest(self):
        class_map_cfg1 = (
            ClassMapCfg('classA')
            .device(cfg.leaf0['id'])
            .match('dscp', 10)
            .create()
        )
        class_map_cfg2 = (
            ClassMapCfg('classB')
            .device(cfg.leaf1['id'])
            .match('vlan', 5)
            .create()
        )

        class_map_cfg_list = [
            class_map_cfg1,
            class_map_cfg2
        ]

        class_map = ClassMap(class_map_cfg_list, multiple=True)

        for device in class_map.retrieve():
            assert device['classMap'] == []

        class_map.create()

        for device in class_map.retrieve():
            if device['deviceId'] == cfg.leaf0['id']:
                assert device['classMap'] == [
                    {'matches': [{'type': 'dscp', 'option': 10}], 'name': 'classA'}]
            elif device['deviceId'] == cfg.leaf1['id']:
                assert device['classMap'] == [
                    {'matches': [{'type': 'vlan', 'option': 5}], 'name': 'classB'}]

        # clear
        class_map.delete()


class MultipleDeviceClassMapGetTest(QoSPolicyTest):
    """
    Test class map GET API for multiple device
    """

    def runTest(self):
        class_map_cfg1 = (
            ClassMapCfg('classC')
            .device(cfg.leaf0['id'])
            .match('cos', 6)
            .create()
        )
        class_map_cfg2 = (
            ClassMapCfg('classD')
            .device(cfg.leaf1['id'])
            .match('precedence', 2)
            .create()
        )

        class_map_cfg_list = [
            class_map_cfg1,
            class_map_cfg2
        ]

        class_map = ClassMap(class_map_cfg_list, multiple=True)

        for device in class_map.retrieve():
            assert device['classMap'] == []

        class_map.create()

        for device in class_map.retrieve():
            if device['deviceId'] == cfg.leaf0['id']:
                assert device['classMap'] == [
                    {'matches': [{'type': 'cos', 'option': 6}], 'name': 'classC'}]
            elif device['deviceId'] == cfg.leaf1['id']:
                assert device['classMap'] == [
                    {'matches': [{'type': 'precedence', 'option': 2}], 'name': 'classD'}]

        # clear
        class_map.delete()


class MultipleDeviceClassMapDeleteTest(QoSPolicyTest):
    """
    Test class map DELETE API for multiple device
    """

    def runTest(self):
        class_map_cfg1 = (
            ClassMapCfg('classE')
            .device(cfg.leaf0['id'])
            .match('vlan', 10)
            .create()
        )
        class_map_cfg2 = (
            ClassMapCfg('classF')
            .device(cfg.leaf1['id'])
            .match('cos', 5)
            .create()
        )

        class_map_cfg_list = [
            class_map_cfg1,
            class_map_cfg2
        ]

        class_map = ClassMap(class_map_cfg_list, multiple=True)

        for device in class_map.retrieve():
            assert device['classMap'] == []

        class_map.create()

        for device in class_map.retrieve():
            if device['deviceId'] == cfg.leaf0['id']:
                assert device['classMap'] == [
                    {'matches': [{'type': 'vlan', 'option': 10}], 'name': 'classE'}]
            elif device['deviceId'] == cfg.leaf1['id']:
                assert device['classMap'] == [
                    {'matches': [{'type': 'cos', 'option': 5}], 'name': 'classF'}]

        class_map.delete()

        for device in class_map.retrieve():
            assert device['classMap'] == []


class SingleDevicePolicyMapPostTest(QoSPolicyTest):
    """
    Test policy map POST API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classA')
            .device(cfg.leaf0['id'])
            .match('cos', 6)
            .create()
        )

        class_map = ClassMap(class_map_cfg)
        class_map.create()

        policy_map_cfg = (
            PolicyMapCfg('policyA')
            .class_map('classA')
            .cos(5)
            .flow(cir=1100000, bc=524288, conform="transmit", violate="drop")
            .create()
        )

        policy_map = PolicyMap(policy_map_cfg, cfg.leaf0['id'])

        assert policy_map.retrieve() == []
        policy_map.create()
        assert policy_map.retrieve() == policy_map_cfg['policyMap']

        # clear
        policy_map.delete()
        class_map.delete()


class SingleDevicePolicyMapGetTest(QoSPolicyTest):
    """
    Test policy map GET API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classB')
            .device(cfg.leaf0['id'])
            .match('vlan', 20)
            .create()
        )

        class_map = ClassMap(class_map_cfg)
        class_map.create()

        policy_map_cfg = (
            PolicyMapCfg('policyB')
            .class_map('classB')
            .phb(2)
            .flow(cir=1045000, bc=524288, conform="transmit", violate="drop")
            .create()
        )
        policy_map = PolicyMap(policy_map_cfg, cfg.leaf0['id'])

        assert policy_map.retrieve() == []
        policy_map.create()
        assert policy_map.retrieve() == policy_map_cfg['policyMap']

        # clear
        policy_map.delete()
        class_map.delete()


class SingleDevicePolicyMapDeleteTest(QoSPolicyTest):
    """
    Test policy map DELETE API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classC')
            .device(cfg.leaf0['id'])
            .match('cos', 2)
            .create()
        )

        class_map = ClassMap(class_map_cfg)
        class_map.create()

        policy_map_cfg = (
            PolicyMapCfg('policyC')
            .class_map('classC')
            .cos(6)
            .flow(cir=2245000, bc=624288, conform="transmit", violate="drop")
            .create()
        )
        policy_map = PolicyMap(policy_map_cfg, cfg.leaf0['id'])

        assert policy_map.retrieve() == []
        policy_map.create()
        assert policy_map.retrieve() == policy_map_cfg['policyMap']
        policy_map.delete()
        assert policy_map.retrieve() == []


class SingleDevicePolicyMapPutTest(QoSPolicyTest):
    """
    Test policy map PUT API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classD')
            .device(cfg.leaf0['id'])
            .match('dscp', 20)
            .create()
        )

        class_map = ClassMap(class_map_cfg)
        class_map.create()

        policy_map_cfg = (
            PolicyMapCfg('policyD')
            .class_map('classD')
            .phb(3)
            .flow(cir=1245000, bc=324288, conform="transmit", violate="drop")
            .create()
        )

        policy_map = PolicyMap(policy_map_cfg, cfg.leaf0['id'])
        policy_map.create()

        assert policy_map.retrieve() == policy_map_cfg['policyMap']

        new_policy_map_cfg = (
            PolicyMapCfg('policyD')
            .class_map('classD')
            .cos(5)
            .create()
        )

        policy_map.update(new_policy_map_cfg)
        assert policy_map.retrieve() == new_policy_map_cfg['policyMap']

        # clear
        policy_map.delete()
        class_map.delete()


class MultipleDevicePolicyMapPostTest(QoSPolicyTest):
    """
    Test policy map POST API for multiple device
    """

    def runTest(self):
        class_map_cfg1 = (
            ClassMapCfg('classA')
            .device(cfg.leaf0['id'])
            .match('dscp', 32)
            .create()
        )
        class_map_cfg2 = (
            ClassMapCfg('classB')
            .device(cfg.leaf1['id'])
            .match('cos', 3)
            .create()
        )

        class_map1 = ClassMap(class_map_cfg1)
        class_map1.create()
        class_map2 = ClassMap(class_map_cfg2)
        class_map2.create()

        policy_map_cfg1 = (
            PolicyMapCfg('policyA')
            .device(cfg.leaf0['id'])
            .class_map('classA')
            .cos(7)
            .flow(cir=1245000, bc=324288, conform="transmit", violate="drop")
            .create()
        )
        policy_map_cfg2 = (
            PolicyMapCfg('policyB')
            .device(cfg.leaf1['id'])
            .class_map('classB')
            .phb(3)
            .flow(cir=1000000, bc=224288, conform="transmit", violate="drop")
            .create()
        )

        policy_map_cfg_list = [
            policy_map_cfg1,
            policy_map_cfg2
        ]

        policy_map = PolicyMap(policy_map_cfg_list, multiple=True)

        for device in policy_map.retrieve():
            assert device['policyMap'] == []

        policy_map.create()

        for device in policy_map.retrieve():
            if device['deviceId'] == cfg.leaf0['id']:
                assert device['policyMap'] == policy_map_cfg1['policyMap']
            elif device['deviceId'] == cfg.leaf1['id']:
                assert device['policyMap'] == policy_map_cfg2['policyMap']

        # clear
        policy_map.delete()
        class_map1.delete()
        class_map2.delete()


class MultipleDevicePolicyMapGetTest(QoSPolicyTest):
    """
    Test policy map GET API for multiple device
    """

    def runTest(self):
        class_map_cfg1 = (
            ClassMapCfg('classC')
            .device(cfg.leaf0['id'])
            .match('precedence', 5)
            .create()
        )
        class_map_cfg2 = (
            ClassMapCfg('classD')
            .device(cfg.leaf1['id'])
            .match('vlan', 30)
            .create()
        )

        class_map1 = ClassMap(class_map_cfg1)
        class_map1.create()
        class_map2 = ClassMap(class_map_cfg2)
        class_map2.create()

        policy_map_cfg1 = (
            PolicyMapCfg('policyC')
            .device(cfg.leaf0['id'])
            .class_map('classC')
            .phb(1)
            .flow(cir=1111000, bc=524288, conform="transmit", violate="drop")
            .create()
        )
        policy_map_cfg2 = (
            PolicyMapCfg('policyD')
            .device(cfg.leaf1['id'])
            .class_map('classD')
            .phb(3)
            .flow(cir=1660000, bc=114288, conform="transmit", violate="drop")
            .create()
        )

        policy_map_cfg_list = [
            policy_map_cfg1,
            policy_map_cfg2
        ]

        policy_map = PolicyMap(policy_map_cfg_list, multiple=True)

        for device in policy_map.retrieve():
            assert device['policyMap'] == []

        policy_map.create()

        for device in policy_map.retrieve():
            if device['deviceId'] == cfg.leaf0['id']:
                assert device['policyMap'] == policy_map_cfg1['policyMap']
            elif device['deviceId'] == cfg.leaf1['id']:
                assert device['policyMap'] == policy_map_cfg2['policyMap']

        # clear
        policy_map.delete()
        class_map1.delete()
        class_map2.delete()


class MultipleDevicePolicyMapDeleteTest(QoSPolicyTest):
    """
    Test policy map DELETE API for multiple device
    """

    def runTest(self):
        class_map_cfg1 = (
            ClassMapCfg('classE')
            .device(cfg.leaf0['id'])
            .match('vlan', 50)
            .create()
        )
        class_map_cfg2 = (
            ClassMapCfg('classF')
            .device(cfg.leaf1['id'])
            .match('dscp', 60)
            .create()
        )

        class_map1 = ClassMap(class_map_cfg1)
        class_map1.create()
        class_map2 = ClassMap(class_map_cfg2)
        class_map2.create()

        policy_map_cfg1 = (
            PolicyMapCfg('policyE')
            .device(cfg.leaf0['id'])
            .class_map('classE')
            .cos(2)
            .flow(cir=1111000, bc=524288, conform="transmit", violate="drop")
            .create()
        )
        policy_map_cfg2 = (
            PolicyMapCfg('policyF')
            .device(cfg.leaf1['id'])
            .class_map('classF')
            .cos(5)
            .flow(cir=1660000, bc=114288, conform="transmit", violate="drop")
            .create()
        )

        policy_map_cfg_list = [
            policy_map_cfg1,
            policy_map_cfg2
        ]

        policy_map = PolicyMap(policy_map_cfg_list, multiple=True)

        for device in policy_map.retrieve():
            assert device['policyMap'] == []

        policy_map.create()

        for device in policy_map.retrieve():
            if device['deviceId'] == cfg.leaf0['id']:
                assert device['policyMap'] == policy_map_cfg1['policyMap']
            elif device['deviceId'] == cfg.leaf1['id']:
                assert device['policyMap'] == policy_map_cfg2['policyMap']

        policy_map.delete()

        for device in policy_map.retrieve():
            assert device['policyMap'] == []

        # clear
        class_map1.delete()
        class_map2.delete()


class SingleDeviceServicesPostTest(QoSPolicyTest):
    """
    Test services POST API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classA')
            .device(cfg.leaf0['id'])
            .match('cos', 6)
            .create()
        )

        class_map = ClassMap(class_map_cfg)
        class_map.create()

        policy_map_cfg = (
            PolicyMapCfg('policyA')
            .class_map('classA')
            .cos(5)
            .flow(cir=1100000, bc=524288, conform="transmit", violate="drop")
            .create()
        )

        policy_map = PolicyMap(policy_map_cfg, cfg.leaf0['id'])
        policy_map.create()

        services_cfg = (
            ServicesCfg()
            .policy_map('policyA')
            .port(4)
            .create()
        )

        services = Services(services_cfg, cfg.leaf0['id'])

        assert services.retrieve() == []
        services.create()
        assert services.retrieve() == services_cfg['services']

        # clear
        services.delete()
        policy_map.delete()
        class_map.delete()


class SingleDeviceServicesGetTest(QoSPolicyTest):
    """
    Test services GET API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classB')
            .device(cfg.leaf0['id'])
            .match('vlan', 16)
            .create()
        )

        class_map = ClassMap(class_map_cfg)
        class_map.create()

        policy_map_cfg = (
            PolicyMapCfg('policyB')
            .class_map('classB')
            .phb(2)
            .flow(cir=1100000, bc=524288, conform="transmit", violate="drop")
            .create()
        )

        policy_map = PolicyMap(policy_map_cfg, cfg.leaf0['id'])
        policy_map.create()

        services_cfg = (
            ServicesCfg()
            .policy_map('policyB')
            .port(2)
            .create()
        )

        services = Services(services_cfg, cfg.leaf0['id'])

        assert services.retrieve() == []
        services.create()
        assert services.retrieve() == services_cfg['services']

        # clear
        services.delete()
        policy_map.delete()
        class_map.delete()


class SingleDeviceServicesDeleteTest(QoSPolicyTest):
    """
    Test services DELETE API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classC')
            .device(cfg.leaf0['id'])
            .match('cos', 3)
            .create()
        )

        class_map = ClassMap(class_map_cfg)
        class_map.create()

        policy_map_cfg = (
            PolicyMapCfg('policyC')
            .class_map('classC')
            .cos(2)
            .flow(cir=1122000, bc=524288, conform="transmit", violate="drop")
            .create()
        )

        policy_map = PolicyMap(policy_map_cfg, cfg.leaf0['id'])
        policy_map.create()

        services_cfg = (
            ServicesCfg()
            .policy_map('policyC')
            .port(1)
            .create()
        )

        services = Services(services_cfg, cfg.leaf0['id'])

        assert services.retrieve() == []
        services.create()
        assert services.retrieve() == services_cfg['services']

        services.delete()
        assert services.retrieve() == []

        # clear
        policy_map.delete()
        class_map.delete()


class SingleDeviceServicesPutTest(QoSPolicyTest):
    """
    Test services PUT API for specific device
    """

    def runTest(self):
        class_map_cfg = (
            ClassMapCfg('classD')
            .device(cfg.leaf0['id'])
            .match('vlan', 15)
            .create()
        )

        class_map = ClassMap(class_map_cfg)
        class_map.create()

        policy_map_cfg = (
            PolicyMapCfg('policyD')
            .class_map('classD')
            .cos(7)
            .flow(cir=1122000, bc=524288, conform="transmit", violate="drop")
            .create()
        )

        policy_map = PolicyMap(policy_map_cfg, cfg.leaf0['id'])
        policy_map.create()

        services_cfg = (
            ServicesCfg()
            .policy_map('policyD')
            .port(10)
            .create()
        )

        services = Services(services_cfg, cfg.leaf0['id'])

        services.create()
        assert services.retrieve() == services_cfg['services']

        new_services_cfg = (
            ServicesCfg()
            .policy_map('policyD')
            .port(20)
            .create()
        )

        services.update(new_services_cfg)
        assert services.retrieve() == new_services_cfg['services']

        # clear
        services.delete()
        policy_map.delete()
        class_map.delete()


class MultipleDeviceServicesPostTest(QoSPolicyTest):
    """
    Test services POST API for multiple device
    """

    def runTest(self):
        class_map_cfg1 = (
            ClassMapCfg('classA')
            .device(cfg.leaf0['id'])
            .match('dscp', 32)
            .create()
        )
        class_map_cfg2 = (
            ClassMapCfg('classB')
            .device(cfg.leaf1['id'])
            .match('cos', 3)
            .create()
        )

        class_map1 = ClassMap(class_map_cfg1)
        class_map1.create()
        class_map2 = ClassMap(class_map_cfg2)
        class_map2.create()

        policy_map_cfg1 = (
            PolicyMapCfg('policyA')
            .device(cfg.leaf0['id'])
            .class_map('classA')
            .cos(7)
            .flow(cir=1245000, bc=324288, conform="transmit", violate="drop")
            .create()
        )
        policy_map_cfg2 = (
            PolicyMapCfg('policyB')
            .device(cfg.leaf1['id'])
            .class_map('classB')
            .phb(3)
            .flow(cir=1000000, bc=224288, conform="transmit", violate="drop")
            .create()
        )

        policy_map_cfg_list = [
            policy_map_cfg1,
            policy_map_cfg2
        ]

        policy_map = PolicyMap(policy_map_cfg_list, multiple=True)
        policy_map.create()

        services_cfg1 = (
            ServicesCfg()
            .device(cfg.leaf0['id'])
            .policy_map('policyA')
            .port(10)
            .create()
        )
        services_cfg2 = (
            ServicesCfg()
            .device(cfg.leaf1['id'])
            .policy_map('policyB')
            .port(20)
            .create()
        )

        services_cfg_list = [
            services_cfg1,
            services_cfg2
        ]

        services = Services(services_cfg_list, multiple=True)

        for device in services.retrieve():
            assert device['services'] == []

        services.create()

        for device in services.retrieve():
            if device['deviceId'] == cfg.leaf0['id']:
                assert device['services'] == services_cfg1['services']
            elif device['deviceId'] == cfg.leaf1['id']:
                assert device['services'] == services_cfg2['services']

        # clear
        services.delete()
        policy_map.delete()
        class_map1.delete()
        class_map2.delete()


class MultipleDeviceServicesGetTest(QoSPolicyTest):
    """
    Test services GET API for multiple device
    """

    def runTest(self):
        class_map_cfg1 = (
            ClassMapCfg('classC')
            .device(cfg.leaf0['id'])
            .match('vlan', 25)
            .create()
        )
        class_map_cfg2 = (
            ClassMapCfg('classD')
            .device(cfg.leaf1['id'])
            .match('dscp', 10)
            .create()
        )

        class_map1 = ClassMap(class_map_cfg1)
        class_map1.create()
        class_map2 = ClassMap(class_map_cfg2)
        class_map2.create()

        policy_map_cfg1 = (
            PolicyMapCfg('policyC')
            .device(cfg.leaf0['id'])
            .class_map('classC')
            .cos(3)
            .create()
        )
        policy_map_cfg2 = (
            PolicyMapCfg('policyD')
            .device(cfg.leaf1['id'])
            .class_map('classD')
            .phb(5)
            .create()
        )

        policy_map_cfg_list = [
            policy_map_cfg1,
            policy_map_cfg2
        ]

        policy_map = PolicyMap(policy_map_cfg_list, multiple=True)
        policy_map.create()

        services_cfg1 = (
            ServicesCfg()
            .device(cfg.leaf0['id'])
            .policy_map('policyC')
            .port(15)
            .create()
        )
        services_cfg2 = (
            ServicesCfg()
            .device(cfg.leaf1['id'])
            .policy_map('policyD')
            .port(25)
            .create()
        )

        services_cfg_list = [
            services_cfg1,
            services_cfg2
        ]

        services = Services(services_cfg_list, multiple=True)

        for device in services.retrieve():
            assert device['services'] == []

        services.create()

        for device in services.retrieve():
            if device['deviceId'] == cfg.leaf0['id']:
                assert device['services'] == services_cfg1['services']
            elif device['deviceId'] == cfg.leaf1['id']:
                assert device['services'] == services_cfg2['services']

        # clear
        services.delete()
        policy_map.delete()
        class_map1.delete()
        class_map2.delete()


class MultipleDeviceServicesDeleteTest(QoSPolicyTest):
    """
    Test services DELETE API for multiple device
    """

    def runTest(self):
        class_map_cfg1 = (
            ClassMapCfg('classE')
            .device(cfg.leaf0['id'])
            .match('cos', 2)
            .create()
        )
        class_map_cfg2 = (
            ClassMapCfg('classF')
            .device(cfg.leaf1['id'])
            .match('precedence', 3)
            .create()
        )

        class_map1 = ClassMap(class_map_cfg1)
        class_map1.create()
        class_map2 = ClassMap(class_map_cfg2)
        class_map2.create()

        policy_map_cfg1 = (
            PolicyMapCfg('policyE')
            .device(cfg.leaf0['id'])
            .class_map('classE')
            .cos(6)
            .create()
        )
        policy_map_cfg2 = (
            PolicyMapCfg('policyF')
            .device(cfg.leaf1['id'])
            .class_map('classF')
            .phb(7)
            .create()
        )

        policy_map_cfg_list = [
            policy_map_cfg1,
            policy_map_cfg2
        ]

        policy_map = PolicyMap(policy_map_cfg_list, multiple=True)
        policy_map.create()

        services_cfg1 = (
            ServicesCfg()
            .device(cfg.leaf0['id'])
            .policy_map('policyE')
            .port(18)
            .create()
        )
        services_cfg2 = (
            ServicesCfg()
            .device(cfg.leaf1['id'])
            .policy_map('policyF')
            .port(28)
            .create()
        )

        services_cfg_list = [
            services_cfg1,
            services_cfg2
        ]

        services = Services(services_cfg_list, multiple=True)

        for device in services.retrieve():
            assert device['services'] == []

        services.create()

        for device in services.retrieve():
            if device['deviceId'] == cfg.leaf0['id']:
                assert device['services'] == services_cfg1['services']
            elif device['deviceId'] == cfg.leaf1['id']:
                assert device['services'] == services_cfg2['services']

        services.delete()
        for device in services.retrieve():
            assert device['services'] == []

        # clear
        policy_map.delete()
        class_map1.delete()
        class_map2.delete()

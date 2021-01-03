"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test ACL Rest API.

Test environment

    +--------+
    | spine0 |
    +--------+
   47 |  | 48
      |  +------------+
   26 |            26 |
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


class ACLTest(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)

class Acl_01_SetterAndGetter(ACLTest):
    """
    Test set and get ACL rest API
    """

    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl = ACL(acl_cfg)
        #print("debug acl_cfg1:", acl_cfg)
        #print("debug acl_cfg2:", acl_cfg['device-id'])
        #print("debug acl_cfg3:", acl_cfg['data'])
        actual_device = acl.get_device()
        #print("debug get_device status:", actual_device)
        #for a in actual_device.keys():
        #    print("debug actual_device:", a)
        if oftest.config['test_topology'] == 'scatter':
            assert(cfg.spine0['id'] in actual_device), "Spine0 device not found"
            assert(cfg.leaf0['id'] in actual_device), "leaf0 device not found"
            assert(cfg.leaf1['id'] in actual_device), "leaf1 device not found"
            
        #actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug get_deviceById status:", actual_device)
        #actual_device = acl.build()

class Acl_X01_SetterDelAclRule(ACLTest):
    """
    Test set and del ACL rule rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(3)
        actual_device = acl.get_device()
        #print("debug get_device status:", actual_device)

class Acl_02_Setter_SetScrMacRule(ACLTest):
    """
    Test set and get ACL rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "srcMac": "11:11:11:11:11:11",
                "srcMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        actual_device = acl.build()
        time.sleep(2)
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("==============================")
        #print("debug acl device status2:", actual_device)
        assert("11:11:11:11:11:11" == actual_device[0]["mac"]["srcMac"]), "acl setup src mac rule fail"

class Acl_03_Setter_SetDestMacRule(ACLTest):
    """
    Test set and get ACL rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "dstMac": "22:22:22:22:22:22",
                "dstMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        actual_device = acl.build()
        time.sleep(2)
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("==============================")
        #print("debug acl device status2:", actual_device)
        assert("22:22:22:22:22:22" == actual_device[0]["mac"]["dstMac"]), "acl setup dst mac rule fail"

class Acl_04_Setter_SetSrc_DstMacDenyRule(ACLTest):
    """
    Test set and get ACL rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "deny",
                           "mac": {
                "srcMac": "11:11:11:11:11:11",
                "srcMacMask": "FF:FF:FF:FF:FF:FF",
                "dstMac": "22:22:22:22:22:22",
                "dstMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        actual_device = acl.build()
        time.sleep(2)
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("==============================")
        #print("debug acl device status2:", actual_device)
        assert("11:11:11:11:11:11" == actual_device[0]["mac"]["srcMac"]), "acl setup src mac rule fail"
        assert("22:22:22:22:22:22" == actual_device[0]["mac"]["dstMac"]), "acl setup dst mac rule fail"

class Acl_05_Setter_SetSrc_DstMacOutRule(ACLTest):
    """
    Test set and get ACL rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [1],
                           "direction": "false",
                           "action": "permit",
                           "mac": {
                "srcMac": "11:11:11:11:11:11",
                "srcMacMask": "FF:FF:FF:FF:FF:FF",
                "dstMac": "22:22:22:22:22:22",
                "dstMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        actual_device = acl.build()
        time.sleep(2)
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("==============================")
        #print("debug acl device status2:", actual_device)
        assert("11:11:11:11:11:11" == actual_device[0]["mac"]["srcMac"] and 
            False == actual_device[0]["direction"]), "acl setup direction of src mac rule fail"
        assert("22:22:22:22:22:22" == actual_device[0]["mac"]["dstMac"] and
            False == actual_device[0]["direction"]), "acl setup direction of dst mac rule fail"

class Acl_06_Setter_DelDeviceSpecifyRule(ACLTest):
    """
    Test set and get ACL rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "srcMac": "11:11:11:11:11:11",
                "srcMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(5)
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [2],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "dstMac": "22:22:22:22:22:22",
                "dstMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(2)
        #print("debug:==============================")
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device:", actual_device)
        assert(2 == len(actual_device)), "Acl rule set len fail"

        delId_1 = actual_device[0]["policyId"]
        delId_2 = actual_device[1]["policyId"]
        #print("debug policyId 1:", delId_1)
        #print("debug policyId 2:", delId_2)

        actual_device = acl.delete_deviceSpecifyRuleId(cfg.leaf0['id'], delId_1)
        time.sleep(2)
        actual_device = acl.delete_deviceSpecifyRuleId(cfg.leaf0['id'], delId_2)
        time.sleep(2)
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug acl device status:", actual_device)
        assert(0 == len(actual_device)), "Acl rule set len fail"

class Acl_07_Setter_GetterAllRuleByDeviceId(ACLTest):
    """
    Test set and get ACL rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "srcMac": "11:11:11:11:11:11",
                "srcMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(5)
        acl_cfg['device-id'] = [cfg.leaf1['id']]
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "dstMac": "22:22:22:22:22:22",
                "dstMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(2)
        #print("debug:==============================")
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device1:", actual_device)
        assert(1 == len(actual_device)), "Acl rule set len != 1 fail on device 1"

        #print("debug:==============================")
        actual_device = acl.get_deviceById(cfg.leaf1['id'])
        #print("debug actual_device2:", actual_device)
        assert(1 == len(actual_device)), "Acl rule set len != 1 fail on device 2"

class Acl_08_Setter_DelAllRuleByDeviceId(ACLTest):
    """
    Test set and delete ACL rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "srcMac": "11:11:11:11:11:11",
                "srcMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(5)
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [2],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "dstMac": "22:22:22:22:22:22",
                "dstMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(2)
        acl_cfg['device-id'] = [cfg.leaf1['id']]
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "srcMac": "11:11:11:11:11:11",
                "srcMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(5)
        acl_cfg['device-id'] = [cfg.leaf1['id']]
        acl_cfg['data'] = {"ports": [2],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "dstMac": "22:22:22:22:22:22",
                "dstMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(2)
        #print("debug:==============================")
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device1:", actual_device)
        assert(2 == len(actual_device)), "Acl rule len != 2 fail on device 1"

        #print("debug:==============================")
        actual_device = acl.get_deviceById(cfg.leaf1['id'])
        #print("debug actual_device2:", actual_device)
        assert(2 == len(actual_device)), "Acl rule len != 2 fail on device 2"
        acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device3:", actual_device)
        assert(0 == len(actual_device)), "Acl rule len != 0 fail on device 1"
        acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.get_deviceById(cfg.leaf1['id'])
        #print("debug actual_device4:", actual_device)
        assert(0 == len(actual_device)), "Acl rule len != 0 fail on device 2"

class Acl_09_Setter_SetEther_VlanRule(ACLTest):
    """
    Test set and delete ACL rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {"etherType": "0800", "etherTypeMask": "FFFF"}
        }
        actual_device = acl.build()
        time.sleep(5)
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [2],
                           "direction": "true",
                           "action": "permit",
                           "mac": {"vid": 10, "vidMask": 4095}
        }
        actual_device = acl.build()
        time.sleep(2)
        #print("debug:==============================")
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device1:", actual_device)
        assert(2 == len(actual_device)), "Acl rule len != 2 fail on device 1"
        assert("0800" == actual_device[0]["mac"]["etherType"]), "acl setup ether type rule fail"
        assert(10 == actual_device[1]["mac"]["vid"]), "acl setup vlan id rule fail"
        acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)

        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device3:", actual_device)
        assert(0 == len(actual_device)), "Acl rule len != 0 fail on device 1"
        acl.delete_deviceById(cfg.leaf1['id'])

class Acl_10_Setter_SetIPSource_IPDestRule(ACLTest):
    """
    Test set and SetIPSource_IPDest ACL rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "ipv4": {"protocol": 17, "srcIp": "1.1.1.1", "srcIpMask": "255.255.255.255"}
        }
        actual_device = acl.build()
        time.sleep(5)
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [2],
                           "direction": "true",
                           "action": "permit",
                           "ipv4": {"protocol": 17, "dstIp": "2.2.2.2", "dstIpMask": "255.255.255.255"}
        }
        actual_device = acl.build()
        time.sleep(2)
        #print("debug:==============================")
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device1:", actual_device)
        assert(2 == len(actual_device)), "Acl rule len != 2 fail on device 1"
        testResult = False
        for testData in actual_device:
            if testData["ipv4"]["srcIp"] == "1.1.1.1": testResult = True
        assert(True == testResult), "acl setup srcIp rule fail"
        testResult = False
        for testData in actual_device:
            if testData["ipv4"]["dstIp"] == "2.2.2.2": testResult = True
        assert(True == testResult), "acl setup dstIp rule fail"

        acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)

        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device3:", actual_device)
        assert(0 == len(actual_device)), "Acl rule len != 0 fail on device 1"
        acl.delete_deviceById(cfg.leaf1['id'])

class Acl_11_Setter_SetIPSource_IPDestOutRule(ACLTest):
    """
    Test set and SetIPSource_IPDest ACL rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        acl_cfg['data'] = {"ports": [1],
                           "direction": "false",
                           "action": "permit",
                           "ipv4": {"protocol": 17, "srcIp": "1.1.1.1", "srcIpMask": "255.255.255.255"}
        }
        actual_device = acl.build()
        time.sleep(5)
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [2],
                           "direction": "false",
                           "action": "permit",
                           "ipv4": {"protocol": 17, "dstIp": "2.2.2.2", "dstIpMask": "255.255.255.255"}
        }
        actual_device = acl.build()
        time.sleep(2)
        #print("debug:==============================")
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device1:", actual_device)
        assert(2 == len(actual_device)), "Acl rule len != 2 fail on device 1"
        testResult = False
        for testData in actual_device:
            if testData["ipv4"]["srcIp"] == "1.1.1.1" and testData["direction"] == False:
                testResult = True
                #print(testData["direction"], testData["ipv4"]["srcIp"])
        assert(True == testResult), "acl setup direction of srcIp rule fail"
        testResult = False
        for testData in actual_device:
            if testData["ipv4"]["dstIp"] == "2.2.2.2" and testData["direction"] == False:
                testResult = True
                #print(testData["direction"], testData["ipv4"]["srcIp"])
        assert(True == testResult), "acl setup direction of dstIp rule fail"

        acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)

        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device3:", actual_device)
        assert(0 == len(actual_device)), "Acl rule len != 0 fail on device 1"
        acl.delete_deviceById(cfg.leaf1['id'])

class Acl_12_Setter_SetIPSource_IPDestDenyRule(ACLTest):
    """
    Test set and SetIPSource_IPDest ACL rest API
    """
    def runTest(self):
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "deny",
                           "ipv4": {"protocol": 17, "srcIp": "1.1.1.1", "srcIpMask": "255.255.255.255"}
        }
        actual_device = acl.build()
        time.sleep(5)
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [2],
                           "direction": "true",
                           "action": "deny",
                           "ipv4": {"protocol": 17, "dstIp": "2.2.2.2", "dstIpMask": "255.255.255.255"}
        }
        actual_device = acl.build()
        time.sleep(2)
        #print("debug:==============================")
        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device1:", actual_device)
        assert(2 == len(actual_device)), "Acl rule len != 2 fail on device 1"
        testResult = False
        for testData in actual_device:
            if testData["ipv4"]["srcIp"] == "1.1.1.1" and testData["action"] == "deny":
                testResult = True
                #print(testData["direction"], testData["ipv4"]["srcIp"])
        assert(True == testResult), "acl setup direction of srcIp rule fail"
        testResult = False
        for testData in actual_device:
            if testData["ipv4"]["dstIp"] == "2.2.2.2" and testData["action"] == "deny":
                testResult = True
                #print(testData["direction"], testData["ipv4"]["srcIp"])
        assert(True == testResult), "acl setup direction of dstIp rule fail"

        acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)

        actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device3:", actual_device)
        assert(0 == len(actual_device)), "Acl rule len != 0 fail on device 1"
        acl.delete_deviceById(cfg.leaf1['id'])

class Acl_Run_1_Setter_PermitDenyMacRule(ACLTest):
    """
    Test set and SetIPSource_IPDest ACL rest API
    """
    def runTest(self):
        ports = sorted(config["port_map"].keys())
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "srcMac": cfg.host0['mac'],
                "srcMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(5)
        #print("debug host0:", cfg.host0)
        #print("debug ports:", ports)
        cfg.host0['ip'] = '192.168.100.1'
        cfg.host1['ip'] = '192.168.100.2'

        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=64,
            eth_dst=cfg.host1['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host1['ip'],
            ip_src=cfg.host0['ip']
        )
        expected_pkt = pkt_from_p0_to_p1

        #print("debug: =======expect pkt_from_p0_to_p1 =======")
        for i in range(5):
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
            wait_for_seconds(1)
        verify_packet(self, str(expected_pkt), ports[1])
        #print("debug: ", str(expected_pkt), ports[1])

        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [2],
                           "direction": "true",
                           "action": "deny",
                           "mac": {
                "srcMac": cfg.host1['mac'],
                "srcMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(2)
        #print("debug:==============================")
        pkt_from_p1_to_p0 = simple_tcp_packet(
            pktlen=64,
            eth_dst=cfg.host0['mac'],
            eth_src=cfg.host1['mac'],
            ip_dst=cfg.host0['ip'],
            ip_src=cfg.host1['ip']
        )
        expected_pkt = pkt_from_p1_to_p0
        
        #print("debug: =======expect pkt_from_p1_to_p0 =======")
        for i in range(5):
            self.dataplane.send(ports[1], str(pkt_from_p1_to_p0))
            wait_for_seconds(1)
        verify_no_packet(self, str(expected_pkt), ports[0])
        #print("debug: ", str(expected_pkt), ports[0])
        #actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device1:", actual_device)

class Acl_Run_2_Setter_PermitDenyMacRuleByMuliDut(ACLTest):
    """
    Test set and SetIPSource_IPDest ACL rest API
    """
    def runTest(self):
        ports = sorted(config["port_map"].keys())
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        cfg.host0['ip'] = '192.168.100.1'
        cfg.host2['ip'] = '192.168.100.3'

        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {
                "srcMac": cfg.host0['mac'],
                "srcMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(5)
        pkt_from_p0_to_p2 = simple_tcp_packet(
            pktlen=64,
            eth_dst=cfg.host2['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host2['ip'],
            ip_src=cfg.host0['ip']
        )
        expected_pkt = pkt_from_p0_to_p2
        #print("debug: =======expect pkt_from_p0_to_p2 =======")
        for i in range(5):
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))
            wait_for_seconds(1)
        verify_packet(self, str(expected_pkt), ports[2])
        #print("debug: ", str(expected_pkt), ports[2])

        acl_cfg['device-id'] = [cfg.leaf1['id']]
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "deny",
                           "mac": {
                "srcMac": cfg.host2['mac'],
                "srcMacMask": "FF:FF:FF:FF:FF:FF"
            }
        }
        actual_device = acl.build()
        time.sleep(2)
        pkt_from_p2_to_p0 = simple_tcp_packet(
            pktlen=64,
            eth_dst=cfg.host0['mac'],
            eth_src=cfg.host2['mac'],
            ip_dst=cfg.host0['ip'],
            ip_src=cfg.host2['ip']
        )
        expected_pkt = pkt_from_p2_to_p0
        #print("debug: =======expect pkt_from_p2_to_p0 =======")
        for i in range(5):
            self.dataplane.send(ports[2], str(pkt_from_p2_to_p0))
            wait_for_seconds(1)
        verify_no_packet(self, str(expected_pkt), ports[0])

class Acl_Run_3_Setter_PermitDenyVlanRule(ACLTest):
    """
    Test set and SetIPSource_IPDest ACL rest API
    """
    def runTest(self):
        ports = sorted(config["port_map"].keys())
        vlan_cfg = {}
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        cfg.host0['ip'] = '192.168.100.1'
        cfg.host1['ip'] = '192.168.100.2'

        vlan_cfg['device-id'] = cfg.leaf0['id']
        vlan_cfg['ports'] = [
            {
                "port": 1,
                "native": 10,
                "mode": "hybrid",
                "vlans": ["10/tag"]
            }
        ]
        vlan = StaticVLAN(vlan_cfg).build()
        vlan_cfg['ports'] = [
            {
                "port": 2,
                "native": 10,
                "mode": "hybrid",
                "vlans": ["10/tag"]
            }
        ]
        vlan = StaticVLAN(vlan_cfg).build()
        time.sleep(5)

        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {"vid": 10, "vidMask": 4095}
        }
        actual_device = acl.build()
        time.sleep(5)
        pkt_from_p0_to_p1 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=10,
            eth_dst=cfg.host1['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host1['ip'],
            ip_src=cfg.host0['ip']
        )
        expected_pkt = pkt_from_p0_to_p1
        #print("debug: =======expect pkt_from_p0_to_p1 =======")
        for i in range(5):
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
            wait_for_seconds(1)
        verify_packet(self, str(expected_pkt), ports[1])
        #print("debug: ", str(expected_pkt), ports[1])

        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [2],
                           "direction": "true",
                           "action": "deny",
                           "mac": {"vid": 10, "vidMask": 4095}
        }
        actual_device = acl.build()
        time.sleep(2)
        pkt_from_p1_to_p0 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=10,
            eth_dst=cfg.host0['mac'],
            eth_src=cfg.host1['mac'],
            ip_dst=cfg.host0['ip'],
            ip_src=cfg.host1['ip']
        )
        expected_pkt = pkt_from_p1_to_p0
        #print("debug: =======expect pkt_from_p1_to_p0 =======")
        for i in range(5):
            self.dataplane.send(ports[1], str(pkt_from_p1_to_p0))
            wait_for_seconds(1)
        verify_no_packet(self, str(expected_pkt), ports[0])
        #print("debug: ", str(expected_pkt), ports[0])
        
        vlan.delete({'port': 1, 'device-id': cfg.leaf0['id']})
        actual_port = vlan.get_port(1)
        assert(None == actual_port)
        vlan.delete({'port': 2, 'device-id': cfg.leaf0['id']})
        actual_port = vlan.get_port(2)
        assert(None == actual_port)

class Acl_Run_4_Setter_PermitDenyVlanRuleByMuliDut(ACLTest):
    """
    Test set and SetIPSource_IPDest ACL rest API
    """
    def runTest(self):
        ports = sorted(config["port_map"].keys())
        vlan_cfg = {}
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        vlan = StaticVLAN(vlan_cfg)
        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        vlan.delete_DevieIdNoVerify({'device-id': cfg.leaf0['id']})
        time.sleep(2)
        vlan.delete_DevieIdNoVerify({'device-id': cfg.leaf1['id']})
        time.sleep(2)
        actual_device = acl.get_device()
        cfg.host0['ip'] = '192.168.100.1'
        cfg.host2['ip'] = '192.168.100.3'

        vlan_cfg['device-id'] = cfg.leaf0['id']
        vlan_cfg['ports'] = [
            {
                "port": 1,
                "native": 10,
                "mode": "hybrid",
                "vlans": ["10/tag"]
            }
        ]
        vlan = StaticVLAN(vlan_cfg).build()
        time.sleep(6)

        vlan_cfg['device-id'] = cfg.leaf1['id']
        vlan_cfg['ports'] = [
            {
                "port": 1,
                "native": 10,
                "mode": "hybrid",
                "vlans": ["10/tag"]
            }
        ]
        vlan = StaticVLAN(vlan_cfg).build()
        time.sleep(6)
        
        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "permit",
                           "mac": {"vid": 10, "vidMask": 4095}
        }
        actual_device = acl.build()
        time.sleep(5)
        pkt_from_p0_to_p2 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=10,
            eth_dst=cfg.host2['mac'],
            eth_src=cfg.host0['mac'],
            ip_dst=cfg.host2['ip'],
            ip_src=cfg.host0['ip']
        )
        expected_pkt = pkt_from_p0_to_p2
        #print("debug: =======expect pkt_from_p0_to_p2 =======")
        for i in range(5):
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p2))
            wait_for_seconds(1)
        verify_packet(self, str(expected_pkt), ports[2])
        #print("debug: ", str(expected_pkt), ports[2])

        acl_cfg['device-id'] = [cfg.leaf1['id']]
        acl_cfg['data'] = {"ports": [1],
                           "direction": "true",
                           "action": "deny",
                           "mac": {"vid": 10, "vidMask": 4095}
        }
        actual_device = acl.build()
        time.sleep(2)
        pkt_from_p2_to_p0 = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=10,
            eth_dst=cfg.host0['mac'],
            eth_src=cfg.host2['mac'],
            ip_dst=cfg.host0['ip'],
            ip_src=cfg.host2['ip']
        )
        expected_pkt = pkt_from_p2_to_p0
        #print("debug: =======expect pkt_from_p2_to_p0 =======")
        for i in range(5):
            self.dataplane.send(ports[2], str(pkt_from_p2_to_p0))
            wait_for_seconds(1)
        verify_no_packet(self, str(expected_pkt), ports[0])

        vlan_cfg['device-id'] = cfg.leaf0['id']
        vlan.delete({'port': 1, 'device-id': cfg.leaf0['id']})
        actual_port = vlan.get_port(1)
        assert(None == actual_port)
        vlan_cfg['device-id'] = cfg.leaf1['id']
        vlan.delete({'port': 1, 'device-id': cfg.leaf1['id']})
        actual_port = vlan.get_port(1)
        assert(None == actual_port)

class Acl_Run_5_Setter_PermitDenyEtherRuleByOut(ACLTest):
    """
    Test set and SetIPSource_IPDest ACL rest API
    """
    def runTest(self):
        ports = sorted(config["port_map"].keys())
        acl_cfg = {}
        acl_cfg['device-id'] = [cfg.leaf0['id']]

        acl = ACL(acl_cfg)
        actual_device = acl.delete_deviceById(cfg.leaf0['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.leaf1['id'])
        time.sleep(2)
        actual_device = acl.delete_deviceById(cfg.spine0['id'])
        time.sleep(2)
        actual_device = acl.get_device()
        #print("debug acl device status1:", actual_device)
        acl_cfg['data'] = {"ports": [2],
                           "direction": "false",
                           "action": "deny",
                           "mac": {"etherType" : "0806", "etherTypeMask" : "FFFF"}
        }
        actual_device = acl.build()
        time.sleep(5)
        #print("debug host0:", cfg.host0)
        #print("debug ports:", ports)
        cfg.host0['ip'] = '192.168.100.1'
        cfg.host1['ip'] = '192.168.100.2'

        pkt_from_p0_to_p1 = simple_arp_packet(
            pktlen=60, 
            eth_dst='ff:ff:ff:ff:ff:ff',
            eth_src=cfg.host0['mac'],
            vlan_vid=0,
            vlan_pcp=0,
            arp_op=1,
            ip_snd=cfg.host0['ip'],
            ip_tgt=cfg.host1['ip'],
            hw_snd=cfg.host0['mac'],
            hw_tgt='00:00:00:00:00:00'
        )
        expected_pkt = pkt_from_p0_to_p1

        #print("debug: =======expect pkt_from_p0_to_p1 =======")
        for i in range(5):
            self.dataplane.send(ports[0], str(pkt_from_p0_to_p1))
            wait_for_seconds(1)
        verify_no_packet(self, str(expected_pkt), ports[1])
        #print("debug: ", str(expected_pkt), ports[1])

        acl_cfg['device-id'] = [cfg.leaf0['id']]
        acl_cfg['data'] = {"ports": [1],
                           "direction": "false",
                           "action": "permit",
                           "mac": {"etherType" : "0806", "etherTypeMask" : "FFFF"}
        }
        actual_device = acl.build()
        time.sleep(2)
        #print("debug:==============================")
        pkt_from_p1_to_p0 = simple_arp_packet(
            pktlen=60, 
            eth_dst='ff:ff:ff:ff:ff:ff',
            eth_src=cfg.host1['mac'],
            vlan_vid=0,
            vlan_pcp=0,
            arp_op=1,
            ip_snd=cfg.host0['ip'],
            ip_tgt=cfg.host1['ip'],
            hw_snd=cfg.host1['mac'],
            hw_tgt='00:00:00:00:00:00'
        )
        expected_pkt = pkt_from_p1_to_p0
        
        #print("debug: =======expect pkt_from_p1_to_p0 =======")
        for i in range(5):
            self.dataplane.send(ports[1], str(pkt_from_p1_to_p0))
            wait_for_seconds(1)
        verify_packet(self, str(expected_pkt), ports[0])
        #print("debug: ", str(expected_pkt), ports[0])
        #actual_device = acl.get_deviceById(cfg.leaf0['id'])
        #print("debug actual_device1:", actual_device)

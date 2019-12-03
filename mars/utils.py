'''
Provided common utils for testing
'''

import time
import requests
import config as test_config
from telnetlib import Telnet

URL = test_config.API_BASE_URL
LOGIN = test_config.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}

def wait_for_system_stable():
    time.sleep(5)

def wait_for_system_process():
    time.sleep(1)

def reconnect_switch_port(ip_address, port):
    command_list = [
        ("config", "(config)#"),
        ("int eth " + port, "(config-if)#"),
        ("shutdown", "(config-if)#"),
        ("no shutdown", "(config-if)#")
    ]

    telnet_and_execute(ip_address, command_list)

def configure_spine(ip_address):
    command_list = [
        ("config", "(config)#"),
        ("vlan data", "(config-vlan)#"),
        ("vlan 100,200", "(config-vlan)#"),
        ("exit", "(config)#"),
        ("int vl 100", "(config-if)#"),
        ("ip add 192.168.100.2 255.255.255.0", "(config-if)#"),
        ("int vl 200", "(config-if)#"),
        ("ip add 192.168.200.2 255.255.255.0", "(config-if)#"),
        ("exit", "(config)#"),
        ("int eth 1/49", "(config-if)#"),
        ("switchport allowed vlan add 200 tagged", "(config-if)#"),
        ("int eth 1/50", "(config-if)#"),
        ("switchport allowed vlan add 100 tagged", "(config-if)#")
    ]

    telnet_and_execute(ip_address, command_list)

def configure_leaf(ip_address, src_if_vlan_id, access_vlan_id):
    command_list = [
        ("config", "(config)#"),
        ("vxlan source-interface vlan " + src_if_vlan_id, "(config)#"),
        ("vlan database", "(config-vlan)#"),
        ("vlan " + access_vlan_id, "(config-vlan)#"),
        ("exit", "(config)#"),
        ("int eth 1/48", "(config-if)#"),
        ("switchport allowed vlan add " + access_vlan_id + " untagged", "(config-if)#"),
    ]

    telnet_and_execute(ip_address, command_list)

def clear_spine_configuration(ip_address):
    command_list = [
        ("config", "(config)#"),
        ("vlan data", "(config-vlan)#"),
        ("no vlan 100,200", "(config-vlan)#"),
    ]

    telnet_and_execute(ip_address, command_list)

def clear_leaf_configuration(ip_address, access_vlan_id):
    command_list = [
        ("config", "(config)#"),
        ("no vxlan source-interface vlan", "(config)#"),
        ("vlan database", "(config-vlan)#"),
        ("no vlan " + access_vlan_id, "(config-vlan)#"),
        ("exit", "(config)#"),
    ]

    telnet_and_execute(ip_address, command_list)

def telnet_and_execute(host_ip, cli_command_list, debug = False):
    tn = Telnet(host_ip)

    # login
    expect(tn, "Username:")
    send(tn, "admin")
    expect(tn, "Password:")
    send(tn, "admin")
    expect(tn, "#")

    if (debug):
        print ('\r\n')
        print ('telnet to : ' + host_ip)

    for (send_word, expect_word) in cli_command_list:
        if (debug):
            print (send_word, expect_word)

        send(tn, send_word)
        expect(tn, expect_word)

def send(tn, word):
   tn.write(word.encode('ascii') + b"\r\n")

def expect(tn, word):
   tn.read_until(word.encode('utf-8'))

def setup_configuration():
    check_license()

    for device in test_config.devices:
        if config_exists(device) == False:
            config_add(device)

    clear_tenant()
    clear_uplink_segment()

    wait_for_system_stable()

    check_links()

def config_exists(device):
    response = requests.get(URL+"v1/devices/{}".format(device['id']), headers=GET_HEADER)

    if response.status_code == 404:
        return False
    elif response.status_code == 200:
        return True

def config_add(device):
    payload = {
        "id": device['id'],
        "name": device['name'],
        "type": device['type'],
        "available": "true",
        "defaultCfg": "true",
        "mgmtIpAddress": device['mgmtIpAddress'],
        "mgmtPort": 0,
        "mac": device['mac'],
        "nos": device['nos'],
        "mfr": "Nocsys",
        "port": "80",
        "protocol": "rest",
        "rack_id": "1",
        "leaf_group": {
            "name": "",
            "switch_port": ""
        }
    }

    response = requests.post(URL+'v1/devices', json=payload, headers=POST_HEADER)
    assert response.status_code == 200, 'Add device fail! ' + response.text

def clear_tenant():
    response = requests.get(URL+"v1/tenants/v1", headers=GET_HEADER)
    assert(response.status_code == 200)

    # {"tenants":[{"name":"t1","type":"Normal"}]}
    # {"tenants":[]}

    if response.json()['tenants']:
        for t in response.json()['tenants']:
            tmp_tenant = tenant(t['name'])
            tmp_tenant.destroy()

def clear_uplink_segment():
    response = requests.get(URL+"topology/v1/uplink-segments", headers=GET_HEADER)
    assert(response.status_code == 200)

    if response.json()['uplinkSegments']:
        for up_seg in response.json()['uplinkSegments']:
            tmp_uplink_segment = uplink_segment(up_seg['segment_name'])
            tmp_uplink_segment.destroy()

def check_links():
    response = requests.get(URL+"v1/links", headers=GET_HEADER)
    assert(response.status_code == 200)

    # check the connection between spine and leaf
    for spine in test_config.spines:
        for leaf in test_config.leaves:
            match = [ 
                link for link in response.json()['links'] 
                if link['src']['device'] == spine['id'] and link['dst']['device'] == leaf['id']
            ]
            assert match, 'The connection is broken between '+ spine['id'] + ' and ' + leaf['id']

def check_license():
    response = requests.get(URL+"v1/license/v1", headers=GET_HEADER)
    assert(response.status_code == 200)

    if response.json()['maxSwitches'] == 3:
        files = {'file': open('../licenseForNCTU.lic', 'rb')}
        response = requests.post(URL+'v1/license/BinaryFile', files=files, headers=POST_HEADER)
        assert response.status_code == 200, 'Add license fail! ' + response.text

class tenant():
    def __init__(self, name = None):
        self.name = name
        self.segments = []

    def segment(self, name = None, type = None, ip_address = None, vlan_id = None):
        self.segments.append({
            'name': name, 
            'type': type, 
            'ip_address': ip_address, 
            'vlan_id': vlan_id, 
            'members_list': None, 
            'access_port_list': None,
            'network_port_list': None})

        return self

    def segment_member(self, segment_name = None, members = None, device_id = None):
        for segment in self.segments:
            if segment['name'] == segment_name:
                members_info = {'ports': members, 'device_id': device_id}

                if not segment['members_list']:
                    segment['members_list'] = [members_info]
                else:
                    segment['members_list'].append(members_info)

        return self

    def access_port(self, segment_name, name, switch, port, vlan):
        for segment in self.segments:
            if segment['name'] == segment_name:
                access_port_info = {'name': name, 'switch': switch, 'port': port, 'vlan': vlan}
                if not segment['access_port_list']:
                    segment['access_port_list'] = [access_port_info]
                else:
                    segment['access_port_list'].append(access_port_info)

        return self

    def network_port(self, segment_name, name, ip_addresses, uplink_segment):
        for segment in self.segments:
            if segment['name'] == segment_name:
                network_port_info = {'name': name, 'ip_addresses': ip_addresses, 'uplink_segment': uplink_segment}
                if not segment['network_port_list']:
                    segment['network_port_list'] = [network_port_info]
                else:
                    segment['network_port_list'].append(network_port_info)

        return self

    def build(self):
        self.build_tenant()
        wait_for_system_process()
        self.build_segment()
        wait_for_system_process()

        return self

    def build_tenant(self, type = 'Normal'):
        payload = {
            'name': self.name,
            'type': type
        }
        response = requests.post(URL+"v1/tenants/v1", headers=POST_HEADER, json=payload)
        assert response.status_code == 200, 'Add a tenant fail! '+ response.text

    def build_segment(self):
        for segment in self.segments:
            payload = {
                "name": segment['name'],
                "type": segment['type'],
                "ip_address": segment['ip_address'],
                "value": segment['vlan_id']
            }
            response = requests.post(URL+'v1/tenants/v1/{}/segments'.format(self.name), json=payload, headers=POST_HEADER)
            assert response.status_code == 200, 'Add segment fail! ' + response.text

            if segment['type'] == 'vlan':
                self.build_segment_member(segment)
            elif segment['type'] == 'vxlan':
                self.build_access_port(segment)
                self.build_network_port(segment)

    def build_segment_member(self, segment):
        for member in segment['members_list']:
            payload = {
                "ports" : member['ports'],
            }
            response = requests.post(URL+'v1/tenants/v1/{}/segments/{}/device/{}/vlan'.format(self.name, segment['name'], member['device_id']), 
                json=payload, headers=POST_HEADER)
            assert response.status_code == 200, 'Add segment member fail '+ response.text

    def build_access_port(self, segment):
        for access_port in segment['access_port_list']:
            payload = {
                "access_port": [
                    {
                    "name": access_port['name'],
                    "type": "normal",
                    "switch": access_port['switch'],
                    "port": access_port['port'],
                    "vlan": access_port['vlan']
                    }
                ],
                "network_port": []
            }           

            response = requests.post(URL+'v1/tenants/v1/{}/segments/{}/vxlan'.format(self.name, segment['name']), json=payload, headers=POST_HEADER)
            assert response.status_code == 200, 'Add access port fail! '+ response.text

    def build_network_port(self, segment):
        for network_port in segment['network_port_list']:
            payload = {
                "access_port": [],
                "network_port": [
                    {
                    "name": network_port['name'],
                    "ip_addresses": network_port['ip_addresses'],
                    "uplink_segment": network_port['uplink_segment']
                    }
                ]
            }

            response = requests.post(URL+'v1/tenants/v1/{}/segments/{}/vxlan'.format(self.name, segment['name']), json=payload, headers=POST_HEADER)
            assert response.status_code == 200, 'Add network port fail! '+ response.text

    def delete_segment(self, name):
        response = requests.delete(URL+'v1/tenants/v1/{}/segments/{}'.format(self.name, name), headers=GET_HEADER)
        assert response.status_code == 200, 'Delete segment fail '+ response.text

    def destroy(self):
        response = requests.delete(URL+'v1/tenants/v1/{}'.format(self.name), headers=GET_HEADER)
        assert response.status_code == 200, 'Destroy tenant fail '+ response.text

    def debug(self):
        # print self.name
        # print self.segments
        print ''
        for segment in self.segments:
            print '===================='
            print 'segmenet:'
            print segment
            print '===================='
            if segment['members_list']:
                for member in segment['members_list']:
                    print 'member:'
                    print member
                    print '===================='
                    print ''

class uplink_segment():
    uplink_segment = {}

    # def __init__(self, name, device_id, vlan, ports, gateway, gateway_mac, ip_address):
        # self.uplink_segments.append({
        #     'name': name, 
        #     'device_id': device_id, 
        #     'vlan': vlan, 
        #     'ports': ports, 
        #     'gateway': gateway, 
        #     'gateway_mac': gateway_mac,
        #     'ip_address': ip_address
        # })

    def __init__(self, name):
        self.uplink_segment['name'] = name

    def device_id(self, device_id):
        self.uplink_segment['device_id'] = device_id
        return self
    
    def vlan(self, vlan):
        self.uplink_segment['vlan'] = vlan
        return self

    def ports(self, ports):
        self.uplink_segment['ports'] = ports
        return self
    
    def gateway(self, gateway):
        self.uplink_segment['gateway'] = gateway
        return self
    
    def gateway_mac(self, gateway_mac):
        self.uplink_segment['gateway_mac'] = gateway_mac
        return self

    def ip_address(self, ip_address):
        self.uplink_segment['ip_address'] = ip_address
        return self

    def build(self):
        self.build_uplink_segment()
        wait_for_system_process()

        return self

    def build_uplink_segment(self):
        payload = {
            "segment_name": self.uplink_segment['name'],
            "device_id": self.uplink_segment['device_id'],
            "vlan": self.uplink_segment['vlan'],
            "ports": self.uplink_segment['ports'],
            "gateway": self.uplink_segment['gateway'],
            "gateway_mac": self.uplink_segment['gateway_mac'],
            "ip_address": self.uplink_segment['ip_address']
        }

        response = requests.post(URL+'topology/v1/uplink-segments', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add uplink segment fail! '+ response.text
    
    def destroy(self):
        response = requests.delete(URL+'topology/v1/uplink-segments/{}'.format(self.uplink_segment['name']), headers=GET_HEADER)
        assert response.status_code == 200, 'Destroy uplink segment fail '+ response.text

    def debug(self):
        print uplink_segment

class port():

    def __init__(self, port_id, device_id):
        self.port_id = port_id
        self.device_id = device_id

    def link_state(self, enabled):
        payload = {
            'enabled': enabled,
        }
        response = requests.post(URL+"v1/devices/{}/portstate/{}".format(self.device_id, self.port_id), headers=POST_HEADER, json=payload)
        assert response.status_code == 200, 'Change port state fail! '+ response.text

    def link_up(self):
        self.link_state(True)

    def link_down(self):
        self.link_state(False)
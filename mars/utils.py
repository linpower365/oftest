'''
Provided common utils for testing
'''

import time
import requests
import config as test_config
from oftest.testutils import *
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

def wait_for_seconds(sec):
    time.sleep(sec)

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

def configure_arp(ip_address, target, port, vlan):
    command_list = [
        ("config", "(config)#"),
        ("mac-address-table static " + target['mac'].replace(':', '-') + " interface ethernet " + port + " vlan " + str(vlan), "(config)#"),
        ("arp " + target['ip'] + " " + target['mac'].replace(':', '-'), "(config)#"),
        ("exit", "#"),
    ]

    telnet_and_execute(ip_address, command_list)

def remove_arp(ip_address, target, vlan):
    command_list = [
        ("config", "(config)#"),
        ("no mac-address-table static " + target['mac'].replace(':', '-') + " vlan " + str(vlan), "(config)#"),
        ("no arp " + target['ip'], "(config)#"),
        ("exit", "#"),
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
    clear_logical_router()
    clear_span()
    enable_ports()

    wait_for_seconds(5)

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
        "mfr": "",
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
            tmp_tenant = Tenant(t['name'])
            tmp_tenant.destroy()

def clear_uplink_segment():
    response = requests.get(URL+"topology/v1/uplink-segments", headers=GET_HEADER)
    assert(response.status_code == 200)

    if response.json()['uplinkSegments']:
        for up_seg in response.json()['uplinkSegments']:
            tmp_uplink_segment = UplinkSegment(up_seg['segment_name'])
            tmp_uplink_segment.destroy()

def clear_logical_router():
    response = requests.get(URL+"tenantlogicalrouter/v1", headers=GET_HEADER)
    assert(response.status_code == 200)

    if response.json()['routers']:
        for lrouter in response.json()['routers']:
            tmp_lrouter = LogicalRouter(lrouter['name'], lrouter['tenant'])
            tmp_lrouter.destroy()
            clear_policy_route(lrouter['tenant'], lrouter['name'])
            clear_nexthop_group(lrouter['tenant'], lrouter['name'])
            clear_static_route(lrouter['tenant'], lrouter['name'])

def clear_policy_route(tenant, lrouter):
    response = requests.get(URL+"tenantlogicalrouter/v1/tenants/{}/{}/policy-route".format(tenant, lrouter), headers=GET_HEADER)
    assert(response.status_code == 200)

    if response.json()['policies']:
        for policy in response.json()['policies']:
            response = requests.delete(URL+'tenantlogicalrouter/v1/tenants/{}/{}/policy-route/{}'.format(tenant, lrouter, policy['name']), headers=GET_HEADER)
            assert response.status_code == 200, 'Destroy policy route fail '+ response.text

def clear_nexthop_group(tenant, lrouter):
    response = requests.get(URL+"tenantlogicalrouter/v1/tenants/{}/{}/nexthop-group".format(tenant, lrouter), headers=GET_HEADER)
    assert(response.status_code == 200)

    if response.json()['nextHops']:
        for nexthop in response.json()['nextHops']:
            response = requests.delete(URL+'tenantlogicalrouter/v1/tenants/{}/{}/nexthop-group/{}'.format(tenant, lrouter, nexthop['nexthop_group_name']), headers=GET_HEADER)
            assert response.status_code == 200, 'Destroy nexthop group fail '+ response.text

def clear_static_route(tenant, lrouter):
    response = requests.get(URL+"tenantlogicalrouter/v1/tenants/{}/{}/static-route".format(tenant, lrouter), headers=GET_HEADER)
    assert(response.status_code == 200)

    if response.json()['routes']:
        for static_route in response.json()['routes']:
            response = requests.delete(URL+'tenantlogicalrouter/v1/tenants/{}/{}/static-route/{}'.format(tenant, lrouter, static_route['name']), headers=GET_HEADER)
            assert response.status_code == 200, 'Destroy static route fail '+ response.text

def clear_span():
    response = requests.get(URL+"monitor/v1", headers=GET_HEADER)
    assert(response.status_code == 200)

    if 'sessions' in response.json():
        for session in response.json()['sessions']:
            response = requests.delete(URL+'monitor/v1/{}'.format(session['session']), headers=GET_HEADER)
            assert response.status_code == 200, 'Destroy SAPN session fail '+ response.text

def enable_ports():
    response = requests.get(URL+"v1/devices/ports", headers=GET_HEADER)
    assert(response.status_code == 200)

    for port in response.json()['ports']:
        if port['isEnabled'] == False:
            payload = {
                'enabled': True,
            }
            response = requests.post(URL+"v1/devices/{}/portstate/{}".format(port['element'], port['port']), headers=POST_HEADER, json=payload)
            assert response.status_code == 200, 'Enable port fail! '+ response.text


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
        # files = {'file': open('../licenseForNCTU.lic', 'rb')}
        # response = requests.post(URL+'v1/license/BinaryFile', files=files, headers=POST_HEADER)
        data = open('../licenseForNCTU.lic', 'rb').read()
        response = requests.post(URL+'v1/license/BinaryFile', data=data, headers=POST_HEADER)
        assert response.status_code == 200, 'Add license fail! ' + response.text

class PacketGenerator():
    def __init__(self, dataplane):
        self.device_dataplane = dataplane
        self.send_tcp_packet_dict = {}
        self.send_arp_reply_to_dict = {}

    def sender_device(self, sender_device):
        self.sender_device = sender_device

        return self

    def target_device(self, target_device):
        self.target_device = target_device

        return self

    def send_tcp_packet(self, port, port_vlan_id, will_be_trigger_device):
        self.send_tcp_packet_dict['port'] = port
        self.send_tcp_packet_dict['packet'] = simple_tcp_packet(
            pktlen=68,
            dl_vlan_enable=True,
            vlan_vid=port_vlan_id,
            eth_dst=will_be_trigger_device['mac'],
            eth_src=self.sender_device['mac'],
            ip_dst=self.target_device['ip'],
            ip_src=self.sender_device['ip']
        )

        return self

    def send_arp_reply_to(self, will_be_trigger_device, if_ip, port, port_vlan_id):
        self.send_arp_reply_to_dict['port'] = port
        self.send_arp_reply_to_dict['packet'] = simple_arp_packet(
            eth_dst=will_be_trigger_device['mac'],
            eth_src=self.target_device['mac'],
            arp_op=2,
            ip_snd=self.target_device['ip'],
            ip_tgt=if_ip,
            hw_snd=self.target_device['mac'],
            hw_tgt=will_be_trigger_device['mac'],
        )

        return self

    def run(self):
        self.device_dataplane.send(
            self.send_tcp_packet_dict['port'],
            str(self.send_tcp_packet_dict['packet'])
        )
        wait_for_system_process()
        self.device_dataplane.send(
            self.send_arp_reply_to_dict['port'],
            str(self.send_arp_reply_to_dict['packet'])
        )
        wait_for_system_process()


class Tenant():
    def __init__(self, name, type = 'Normal'):
        self.name = name
        self.segments = []
        self.type = type

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

    def build_tenant(self):
        payload = {
            'name': self.name,
            'type': self.type
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
        if segment['members_list'] is not None:
            for member in segment['members_list']:
                payload = {
                    "ports" : member['ports'],
                }
                response = requests.post(URL+'v1/tenants/v1/{}/segments/{}/device/{}/vlan'.format(self.name, segment['name'], member['device_id']),
                    json=payload, headers=POST_HEADER)
                assert response.status_code == 200, 'Add segment member fail '+ response.text

    def build_access_port(self, segment):
        if segment['access_port_list'] is not None:
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
        if segment['network_port_list'] is not None:
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

class UplinkSegment():
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
        self.uplink_segment = {}
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
        print UplinkSegment

class Port():

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


class PolicyRoute():

    def __init__(self, name):
        self._name = name
        self._ingress_segments_list = []
        self._ingress_ports_list = []
        self._action = ''
        self._sequence_no = ''
        self._protocols_list = []
        self._match_ip = ''
        self._nexthop = ''

    def ingress_segments(self, segments):
        for segment in segments:
            self._ingress_segments_list.append(segment)

        return self

    def ingress_ports(self, ports):
        for port in ports:
            self._ingress_ports_list.append(port)

        return self

    def action(self, action):
        self._action = action

        return self

    def sequence_no(self, sequence_no):
        self._sequence_no = sequence_no

        return self

    def protocols(self, protocols):
        for protocol in protocols:
            self._protocols_list.append(protocol)

        return self

    def match_ip(self, ip):
        self._match_ip = ip

        return self

    def nexthop(self, ip):
        self._nexthop = ip

        return self

    def debug(self):
        print self._name
        print self._ingress_segments_list
        print self._ingress_ports_list
        print self._action
        print self._sequence_no
        print self._protocols_list
        print self._match_ip
        print self._nexthop

class LogicalRouter():

    def __init__(self, name, tenant=None):
        self.name = name
        self.tenant = tenant
        self.interfaces_list = []
        self.tenant_routers_list = []
        self.nexthop_groups = []
        self.static_routes = []
        self.policy_routes = []

    def interfaces(self, interfaces):
        for interface in interfaces:
            self.interfaces_list.append(interface)

        return self

    def tenant_routers(self, tenant_routers):
        for tenant_router in tenant_routers:
            self.tenant_routers_list.append(tenant_router)

        return self

    def policy_route(self, policy_route):
        self.policy_routes.append(policy_route)

        return self

    def nexthop_group(self, name, ip_addresses):
        self.nexthop_groups.append({'name': name, 'ip_addresses': ip_addresses})

        return self

    def static_route(self, name, dest, prefix_len, nexthop_group):
        self.static_routes.append(
            {
                'name': name,
                'dest': dest,
                'prefix_len': prefix_len,
                'nexthop_group': nexthop_group
            }
        )

        return self

    def destroy(self):
        response = requests.delete(URL+'tenantlogicalrouter/v1/tenants/{}/{}'.format(self.tenant, self.name), headers=GET_HEADER)
        assert response.status_code == 200, 'Destroy logical router fail '+ response.text

        if self.policy_routes:
            for policy_route in self.policy_routes:
                response = requests.delete(URL+'tenantlogicalrouter/v1/tenants/{}/{}/policy-route/{}'.format(self.tenant, self.name, policy_route._name), headers=GET_HEADER)
                assert response.status_code == 200, 'Destroy policy route fail '+ response.text

        if self.nexthop_groups:
            for nexthop_group in self.nexthop_groups:
                response = requests.delete(URL+'tenantlogicalrouter/v1/tenants/{}/{}/nexthop-group/{}'.format(self.tenant, self.name, nexthop_group['name']), headers=GET_HEADER)
                assert response.status_code == 200, 'Destroy nexthop group fail '+ response.text

        if self.static_routes:
            for static_route in self.static_routes:
                response = requests.delete(URL+'tenantlogicalrouter/v1/tenants/{}/{}/static-route/{}'.format(self.tenant, self.name, static_route['name']), headers=GET_HEADER)
                assert response.status_code == 200, 'Destroy static route fail '+ response.text

    def build(self):
        self.build_lrouter()
        self.build_policy_route()
        self.build_nexthop_group()
        self.build_static_route()

        return self

    def build_lrouter(self):
        payload = {}
        payload['normal'] = {
            "name": self.name,
            "interfaces": self.interfaces_list,
        }
        payload['system'] = {
            "name": self.name,
            "tenant_routers": self.tenant_routers_list,
        }

        if self.name == 'system':
            response = requests.post(URL+'tenantlogicalrouter/v1/tenants/{}'.format(self.name), json=payload['system'], headers=POST_HEADER)
            assert response.status_code == 200, 'Add logical router fail! '+ response.text
        else:
            response = requests.post(URL+'tenantlogicalrouter/v1/tenants/{}'.format(self.tenant), json=payload['normal'], headers=POST_HEADER)
            assert response.status_code == 200, 'Add logical router fail! '+ response.text

    def build_policy_route(self):
        if self.policy_routes:
            for policy_route in self.policy_routes:
                payload = {
                    "name": policy_route._name,
                    "ingress_segments": policy_route._ingress_segments_list,
                    "ingress_ports": policy_route._ingress_ports_list,
                    "action": policy_route._action,
                    "sequence_no": policy_route._sequence_no,
                    "protocols": policy_route._protocols_list,
                    "match_ip": policy_route._match_ip,
                    "nexthop": policy_route._nexthop
                }

                response = requests.post(URL+'tenantlogicalrouter/v1/tenants/{}/{}/policy-route'.format(self.tenant, self.name), json=payload, headers=POST_HEADER)
                assert response.status_code == 200, 'Add policy route fail! '+ response.text

    def build_nexthop_group(self):
        if self.nexthop_groups:
            for nexthop_group in self.nexthop_groups:
                payload = {
                    "nexthop_group_name": nexthop_group['name'],
                    "ip_addresses": nexthop_group['ip_addresses']
                }

                response = requests.post(URL+'tenantlogicalrouter/v1/tenants/{}/{}/nexthop-group'.format(self.tenant, self.name), json=payload, headers=POST_HEADER)
                assert response.status_code == 200, 'Add nexthop group fail! '+ response.text

    def build_static_route(self):
        if self.static_routes:
            for static_route in self.static_routes:
                payload = {
                    "name": static_route['name'],
                    "dest": static_route['dest'],
                    "prefix_len": static_route['prefix_len'],
                    "nexthop_group": static_route['nexthop_group']
                }

                response = requests.post(URL+'tenantlogicalrouter/v1/tenants/{}/{}/static-route'.format(self.tenant, self.name), json=payload, headers=POST_HEADER)
                assert response.status_code == 200, 'Add static router fail! '+ response.text

    def debug(self):
        print 'router = ' + self.name
        print 'tenant = ' + self.tenant
        print 'interfacs = ' + str(self.interfaces)
        print 'nexthop_groups = ' + str(self.nexthop_groups)
        self.policy_routes[0].debug()

class SPAN():
    def __init__(self, session):
        self._session = session
        self._source = {}
        self._target = {}

    def source(self, device_id, port, direction):
        self._source['device_id'] = device_id
        self._source['port'] = port
        self._source['direction'] = direction

        return self

    def target(self, device_id, port):
        self._target['device_id'] = device_id
        self._target['port'] = port

        return self

    def get_session(self, session_id):
        response = requests.get(URL+'monitor/v1/{}'.format(session_id), headers=GET_HEADER)
        assert response.status_code == 200, 'Get SPAN session fail! '+ response.text

        return response.json()

    def build(self):
        payload = {
            "src": {
                "device_id": self._source['device_id'],
                "port": self._source['port'],
                "direction": self._source['direction']
            },
            "target": {
                "device_id": self._target['device_id'],
                "port": self._target['port']
            },
            "session": self._session
        }

        response = requests.post(URL+'monitor/v1', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add SPAN fail! '+ response.text

        return self

    def destroy(self):
        response = requests.get(URL+"monitor/v1", headers=GET_HEADER)
        assert(response.status_code == 200)

        if 'sessions' in response.json():
            for session in response.json()['sessions']:
                response = requests.delete(URL+'monitor/v1/{}'.format(session['session']), headers=GET_HEADER)
                assert response.status_code == 200, 'Destroy SAPN session fail '+ response.text

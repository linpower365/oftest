'''
Provided common utils for testing
'''

import time
import base64
import requests
import config as cfg
from oftest.testutils import *
from telnetlib import Telnet
from scapy.layers.l2 import *
from scapy.layers.inet import *
from scapy.layers.dhcp import *

URL = cfg.API_BASE_URL
LOGIN = cfg.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}
DELETE_HEADER = {'Authorization': AUTH_TOKEN, 'Accept': 'application/json'}

LINKS_INSPECT_RETRY_NUM_MAX = 300

def wait_for_system_stable():
    time.sleep(5)

def wait_for_system_process():
    time.sleep(1)

def wait_for_seconds(sec):
    time.sleep(sec)

def get_master_spine(dataplane, sender, target_ip, port, debug=False, count=5):
    arp_request = simple_arp_packet(
        eth_dst='ff:ff:ff:ff:ff:ff',
        eth_src=sender['mac'],
        arp_op=1,
        ip_snd=sender['ip'],
        ip_tgt=target_ip,
        hw_snd=sender['mac'],
        hw_tgt='00:00:00:00:00:00'
    )

    spine = None
    for i in range(count):
        dataplane.send(port, str(arp_request))
        # (_, pkt, _) = dataplane.poll(port_number=port, timeout=1)
        for (rcv_port_number, pkt, time) in dataplane.packets(port):

            if pkt is not None:
                hex_pkt = pkt.encode('hex')

                if debug:
                    print 'Received packet from port {}'.format(port)
                    print 'src mac = {}'.format(hex_pkt[0:12])
                    print 'dst mac = {}'.format(hex_pkt[12:24])
                    print 'ether type = {}'.format(hex_pkt[24:28])
                    print 'arp op = {}'.format(hex_pkt[40:44])

                if hex_pkt is not None and hex_pkt[24:28] == '0806' and hex_pkt[40:44] == '0002':
                    if hex_pkt[12:24].lower() == cfg.spine0['mac'].replace(':', '').lower():
                        spine = cfg.spine0
                    elif hex_pkt[12:24].lower() == cfg.spine1['mac'].replace(':', '').lower():
                        spine = cfg.spine1
                    else:
                        assert False, 'Getting spine MAC address fail! '

                if debug:
                    print spine

        wait_for_seconds(1)

    assert spine is not None, 'Get master spine failure!'
    return spine

def send_icmp_echo_request(dataplane, sender, target, dst_ip, port):
    icmp_echo_request = simple_icmp_packet(
        eth_dst=target['mac'],
        eth_src=sender['mac'],
        ip_src=sender['ip'],
        ip_dst=dst_ip,
    )

    for i in range(5):
        dataplane.send(port, str(icmp_echo_request))
        wait_for_seconds(1)

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

    for device in cfg.devices:
        if config_exists(device) == False:
            config_add(device)

    clear_tenant()
    clear_uplink_segment()
    clear_logical_router()
    clear_span()
    clear_dhcp_relay()
    enable_ports()

    links_inspect(cfg.spines, cfg.leaves)

def port_configuration():
    cfg.leaf0['portA']  = (
        Port(cfg.leaf0['front_port_A'])
        .tagged(False)
        .nos(cfg.leaf0['nos'])
    )
    cfg.leaf0['portB'] = (
        Port(cfg.leaf0['front_port_B'])
        .tagged(False)
        .nos(cfg.leaf0['nos'])
    )
    cfg.leaf1['portA'] = (
        Port(cfg.leaf1['front_port_A'])
        .tagged(False)
        .nos(cfg.leaf1['nos'])
    )
    cfg.leaf1['portB'] = (
        Port(cfg.leaf1['front_port_B'])
        .tagged(False)
        .nos(cfg.leaf1['nos'])
    )

def config_exists(device):
    response = requests.get(URL+"v1/devices/{}".format(device['id']), headers=GET_HEADER)

    if response.status_code == 404:
        return False
    elif response.status_code == 200:
        return True

def config_add(device):
    if device['type'] == 'leaf':
        payload = {
            "id": device['id'],
            "name": device['name'],
            "type": device['type'],
            "available": "true",
            "defaultCfg": "true",
            "mgmtIpAddress": device['mgmtIpAddress'],
            "mgmtPort": device['mgmtPort'],
            "mac": device['mac'],
            "nos": device['nos'],
            "mfr": device['mfr'],
            "port": device['port'],
            "protocol": device['protocol'],
            "rack_id": "1",
            "leaf_group": {
                "name": "",
                "switch_port": ""
            }
        }
    elif device['type'] == 'spine':
        payload = {
            "id": device['id'],
            "name": device['name'],
            "type": device['type'],
            "available": "true",
            "defaultCfg": "true",
            "mgmtIpAddress": device['mgmtIpAddress'],
            "mgmtPort": device['mgmtPort'],
            "mac": device['mac'],
            "nos": device['nos'],
            "mfr": device['mfr'],
            "port": device['port'],
            "protocol": device['protocol'],
            "rack_id": "1"
        }

    response = requests.post(URL+'v1/devices', json=payload, headers=POST_HEADER)
    assert response.status_code == 200, 'Add device fail! ' + response.text

def config_remove(device):
    response = requests.delete(URL+'v1/devices/{}'.format(device['id']), headers=DELETE_HEADER)
    assert response.status_code == 200, 'Delete device fail! ' + response.text

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
            response = requests.delete(URL+'monitor/v1/{}'.format(session['session']), headers=DELETE_HEADER)
            assert response.status_code == 200, 'Destroy SAPN session fail '+ response.text

def clear_dhcp_relay():
    response = requests.get(URL+'dhcprelay/v1/logical', headers=GET_HEADER)
    assert response.status_code == 200, 'Get DHCP relay fail! '+ response.text

    if 'dhcpRelayServers' in response.json():
        for dhcpRelayServer in response.json()['dhcpRelayServers']:
            for server in dhcpRelayServer['servers']:
                response = requests.delete(
                    URL+'dhcprelay/v1/logical/tenants/{}/segments/{}/servers/{}'.format(dhcpRelayServer['tenant'], dhcpRelayServer['segment'], server),
                    headers=GET_HEADER
                )
                assert response.status_code == 200, 'Destroy DHCP relay server fail '+ response.text

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

def links_inspect(spines, leaves, second=0, fail_stop=False, debug=False):
    start_time = time.time()

    wait_for_seconds(second)
    keep_test = True
    retry_count = 0

    while keep_test and retry_count < LINKS_INSPECT_RETRY_NUM_MAX:
        response = requests.get(URL+"v1/links", headers=GET_HEADER)
        assert(response.status_code == 200)

        # bidirection link count
        total_link_count = len(spines)*len(leaves)*2

        total_link = []

        # check the connection between spine and leaf
        for spine in spines:
            for leaf in leaves:
                match = [
                    link for link in response.json()['links']
                    if (link['src']['device'] == spine['id'] and link['dst']['device'] == leaf['id']) or
                       (link['dst']['device'] == spine['id'] and link['src']['device'] == leaf['id'])
                ]

                if fail_stop:
                    assert match, 'The connection is broken between '+ spine['id'] + ' and ' + leaf['id']
                else:
                    while match:
                        total_link.append(match.pop())

        if not fail_stop:
            if len(total_link) != total_link_count:
                wait_for_seconds(1)
                retry_count += 1
                continue

        if debug:
            print 'len(total_link) = {}'.format(len(total_link))
            print("--- %s seconds ---" % (time.time() - start_time))

        keep_test = False

    assert retry_count < LINKS_INSPECT_RETRY_NUM_MAX, 'Link inspect takes too much time'

def check_license():
    response = requests.get(URL+"v1/license/v1", headers=GET_HEADER)
    assert(response.status_code == 200)

    if response.json()['maxSwitches'] == 8:
        # files = {'file': open('../licenseForNCTU.lic', 'rb')}
        # response = requests.post(URL+'v1/license/BinaryFile', files=files, headers=POST_HEADER)
        data = open('../licenseForNCTU.lic', 'rb').read()
        response = requests.post(URL+'v1/license/BinaryFile', data=data, headers=POST_HEADER)
        assert response.status_code == 200, 'Add license fail! ' + response.text

class RemotePower():
    def __init__(self, config):
        # admin username
        username = config['username']
        password = config['password']

        pos = {'A':0, 'B':1, 'C':2, 'D':3, 'E':4, 'F':5, 'G':6, 'H':7}

        self._led = list("000000000000000000000000")
        self._led[pos[config['plug_id']]] = '1'

        # admin login
        login = base64.b64encode(bytes('{}:{}'.format(username, password)))
        auth_token = 'BASIC ' + login
        self._post_header = {'Authorization': auth_token}

        self._url = "http://" + config['ip'] + "/"

    def On(self):
        response = requests.post(self._url+"ons.cgi?led=" + "".join(self._led), headers=self._post_header)
        assert response.status_code == 200, 'Turn on remote power fail! '+ response.text

    def Off(self):
        response = requests.post(self._url+"offs.cgi?led=" + "".join(self._led), headers=self._post_header)
        assert response.status_code == 200, 'Turn off remote power fail! '+ response.text

    def OffOn(self):
        response = requests.post(self._url+"offon.cgi?led=" + "".join(self._led), headers=self._post_header)
        assert response.status_code == 200, 'Turn off and on remote power fail! '+ response.text

class SegmentMember():
    def __init__(self, segment_name, device_id):
        self._segment_name = segment_name
        self._devices_id = device_id
        self._ports = []
        self._logical_ports = []
        self._mac_based_vlan = []

    def ports(self, member_list):
        self._ports = member_list

        return self

    def logical_ports(self, member_list):
        self._logical_ports = member_list

        return self

    def mac_based_vlan(self, member_list):
        self._mac_based_vlan = member_list

        return self

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

    def segment_member(self, members):
        for segment in self.segments:
            if segment['name'] == members._segment_name:
                if not segment['members_list']:
                    segment['members_list'] = [members]
                else:
                    segment['members_list'].append(members)

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
            if segment['ip_address'] == []:
                payload = {
                    "name": segment['name'],
                    "type": segment['type'],
                    "value": segment['vlan_id']
                }
            else:
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
                    "ports" : member._ports,
                    "logical_ports" : member._logical_ports,
                    "mac_based_vlans" : member._mac_based_vlan
                }

                response = requests.post(URL+'v1/tenants/v1/{}/segments/{}/device/{}/vlan'.format(self.name, segment['name'], member._devices_id),
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

class Device():

    def __init__(self, id):
        self._id = id

    @property
    def available(self):
        response = requests.get(URL+'v1/devices/{}'.format(self._id), headers=GET_HEADER)
        assert response.status_code == 200, 'Get device fail! '+ response.text

        return response.json()['available']

class DevicePort():

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

class Port():

    def __init__(self, port_id):
        self._name = ''
        self._port_id = port_id
        self._tagged = False
        self._nos = 'aos'

    def tagged(self, value):
        self._tagged = value

        return self

    def nos(self, nos):
        self._nos = nos

        return self

    @property
    def name(self):
        if self._tagged == True:
            tagged_str = 'tag'
        else:
            tagged_str = 'untag'

        if self._nos == 'aos':
            return "{}/{}".format(self._port_id, tagged_str)
        elif self._nos == 'sonic':
            port_str = str(self._port_id - 1)
            return "{}/{}".format(port_str, tagged_str)
        else:
            return "{}/{}".format(self._port_id, tagged_str)

    @property
    def number(self):
        if self._nos == 'aos':
            return self._port_id
        elif self._nos == 'sonic':
            return self._port_id - 1
        else:
            return self._port_id

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

class DHCPRelay():
    def __init__(self, tenant, segment):
        self._tenant = tenant
        self._segment = segment
        self._servers_list = []

    def servers(self, servers):
        for server in servers:
            self._servers_list.append(server)

        return self

    def get_content(self):
        response = requests.get(URL+'dhcprelay/v1/logical', headers=GET_HEADER)
        assert response.status_code == 200, 'Get DHCP relay fail! '+ response.text

        return response.json()

    def build(self):
        payload = {
            "tenant": self._tenant,
            "segment": self._segment,
            "servers": self._servers_list
        }

        response = requests.post(URL+'dhcprelay/v1/logical', json=payload, headers=POST_HEADER)
        assert response.status_code == 200, 'Add DHCP relay fail! '+ response.text

        return self

    def destroy(self):
        response = requests.get(URL+"dhcprelay/v1/logical", headers=GET_HEADER)
        assert(response.status_code == 200)

        if 'dhcpRelayServers' in response.json():
            for dhcpRelayServer in response.json()['dhcpRelayServers']:
                for server in dhcpRelayServer['servers']:
                    response = requests.delete(
                        URL+'dhcprelay/v1/logical/tenants/{}/segments/{}/servers/{}'.format(dhcpRelayServer['tenant'], dhcpRelayServer['segment'], server),
                        headers=GET_HEADER
                    )
                    assert response.status_code == 200, 'Destroy DHCP relay server fail '+ response.text

class DHCP_PKT():
    def __init__(self):
        pass

    def generate_discover_pkt(self, client):
        dhcp_discover = (
            Ether(src=client['mac'], dst='ff:ff:ff:ff:ff:ff')/
            IP(src='0.0.0.0', dst='255.255.255.255')/
            UDP(dport=67, sport=68)/
            BOOTP(chaddr=client['mac'].replace(':','').decode('hex'), xid=1234, flags=0x8000)/
            DHCP(options=[('message-type', 'discover'), 'end'])
        )

        return dhcp_discover

    def generate_expected_discover_pkt(self, spine, dhcp_server, client, s1_vlan_ip, s2_vlan_ip):
        expected_dhcp_discover = (
            Ether(src=spine['mac'], dst=dhcp_server['mac'])/
            IP(src=s2_vlan_ip, dst=dhcp_server['ip'], id=0, flags=0x02)/
            UDP(dport=67, sport=67)/
            BOOTP(chaddr=client['mac'].replace(':','').decode('hex'), giaddr=s1_vlan_ip, xid=1234, flags=0x8000, hops=1)/
            DHCP(options=[('message-type', 'discover'), 'end'])
        )

        return expected_dhcp_discover

    def generate_offer_pkt(self, spine, dhcp_server, client, s1_vlan_ip, allocated_ip):
        dhcp_offer = (
            Ether(src=dhcp_server['mac'], dst=spine['mac'])/
            IP(src=dhcp_server['ip'], dst=s1_vlan_ip, flags=0x02)/
            UDP(dport=67, sport=67)/
            BOOTP(op=2, yiaddr=allocated_ip, chaddr=client['mac'].replace(':','').decode('hex'), giaddr=s1_vlan_ip, xid=1234, secs=128)/
            DHCP(options=[('message-type', 'offer'), ('server_id', dhcp_server['ip']), ('lease_time', 1800), ('subnet_mask', '255.255.255.0'), 'end'])
        )

        return dhcp_offer

    def generate_expected_offer_pkt(self, spine, dhcp_server, client, s1_vlan_ip, allocated_ip):
        expected_dhcp_offer = (
            Ether(src=spine['mac'], dst=client['mac'])/
            IP(src=s1_vlan_ip, dst=allocated_ip, id=0, flags=0x02)/
            UDP(dport=68, sport=67)/
            BOOTP(op=2, yiaddr=allocated_ip, chaddr=client['mac'].replace(':','').decode('hex'), giaddr=s1_vlan_ip, xid=1234, secs=128)/
            DHCP(options=[('message-type', 'offer'), ('server_id', dhcp_server['ip']), ('lease_time', 1800), ('subnet_mask', '255.255.255.0'), 'end'])
        )

        return expected_dhcp_offer

    def generate_request_pkt(self, dhcp_server, client, allocated_ip):
        dhcp_request = (
            Ether(src=client['mac'], dst='ff:ff:ff:ff:ff:ff')/
            IP(src='0.0.0.0', dst='255.255.255.255')/
            UDP(dport=67, sport=68)/
            BOOTP(chaddr=client['mac'].replace(':','').decode('hex'), xid=1234)/
            DHCP(options=[('message-type', 'request'), ('server_id', dhcp_server['ip']), ("requested_addr", allocated_ip), 'end'])
        )

        return dhcp_request

    def generate_expected_request_pkt(self, spine, dhcp_server, client, s1_vlan_ip, s2_vlan_ip, allocated_ip):
        expected_dhcp_request = (
            Ether(src=spine['mac'], dst=dhcp_server['mac'])/
            IP(src=s2_vlan_ip, dst=dhcp_server['ip'], id=0, flags=0x02)/
            UDP(dport=67, sport=67)/
            BOOTP(chaddr=client['mac'].replace(':','').decode('hex'), giaddr=s1_vlan_ip, xid=1234, hops=1)/
            DHCP(options=[('message-type', 'request'), ('server_id', dhcp_server['ip']), ("requested_addr", allocated_ip), 'end'])
        )

        return expected_dhcp_request

    def generate_ack_pkt(self, spine, dhcp_server, client, s1_vlan_ip, allocated_ip):
        dhcp_ack = (
            Ether(src=dhcp_server['mac'], dst=spine['mac'])/
            IP(src=dhcp_server['ip'], dst=s1_vlan_ip, flags=0x02)/
            UDP(dport=67, sport=67)/
            BOOTP(op=2, yiaddr=allocated_ip, chaddr=client['mac'].replace(':','').decode('hex'), giaddr=s1_vlan_ip, xid=1234, secs=128)/
            DHCP(options=[('message-type', 'ack'), ('server_id', dhcp_server['ip']), ('lease_time', 1800), ('subnet_mask', '255.255.255.0'), 'end'])
        )

        return dhcp_ack

    def generate_expected_ack_pkt(self, spine, dhcp_server, client, s1_vlan_ip, allocated_ip):
        expected_dhcp_ack = (
            Ether(src=spine['mac'], dst=client['mac'])/
            IP(src=s1_vlan_ip, dst=allocated_ip, id=0, flags=0x02)/
            UDP(dport=68, sport=67)/
            BOOTP(op=2, yiaddr=allocated_ip, chaddr=client['mac'].replace(':','').decode('hex'), giaddr=s1_vlan_ip, xid=1234, secs=128)/
            DHCP(options=[('message-type', 'ack'), ('server_id', dhcp_server['ip']), ('lease_time', 1800), ('subnet_mask', '255.255.255.0'), 'end'])
        )

        return expected_dhcp_ack

class Configuration():
    def __init__(self):
        pass

    def get_current_json(self):
        response = requests.get(URL+"v1/network/configuration", headers=GET_HEADER)
        assert(response.status_code == 200)

        return response.json()

    def get_factory_default_json(self):
        response = requests.get(URL+"v1/network/configuration/files/Factory_Default_Config.cfg", headers=GET_HEADER)
        assert(response.status_code == 200)

        return response.json()

    def save_as_boot_default_config(self, json_content):
        response = requests.post(URL+'v1/network/configuration/file-modify/startup_netcfg.cfg', json=json_content, headers=POST_HEADER)
        assert response.status_code == 204, 'save as boot default config fail! '+ response.text
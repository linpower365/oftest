"""
ref: http://docs.python-requests.org/zh_CN/latest/user/quickstart.html

Test DHCP relay RestAPI.

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
# from oftest.packet import *
from scapy.layers.l2 import *
from scapy.layers.inet import *
from scapy.layers.dhcp import *

URL = cfg.API_BASE_URL
LOGIN = cfg.LOGIN
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}
POST_HEADER = {'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'}

class DHCPRelayTest(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)

        setup_configuration()
        self.port_configuration()

    def tearDown(self):
        base_tests.SimpleDataPlane.tearDown(self)

    def port_configuration(self):
        cfg.leaf0['portA']  = (
            Port(cfg.leaf0['front_port'][0])
            .tagged(False)
            .nos(cfg.leaf0['nos'])
        )
        cfg.leaf0['portB'] = (
            Port(cfg.leaf0['front_port'][1])
            .tagged(False)
            .nos(cfg.leaf0['nos'])
        )
        cfg.leaf1['portA'] = (
            Port(cfg.leaf1['front_port'][0])
            .tagged(False)
            .nos(cfg.leaf1['nos'])
        )
        cfg.leaf1['portB'] = (
            Port(cfg.leaf1['front_port'][1])
            .tagged(False)
            .nos(cfg.leaf1['nos'])
        )

    def get_master_spine(self, sender, target_ip, port, debug=False):
        arp_request = simple_arp_packet(
            eth_dst='ff:ff:ff:ff:ff:ff',
            eth_src=sender['mac'],
            arp_op=1,
            ip_snd=sender['ip'],
            ip_tgt=target_ip,
            hw_snd=sender['mac'],
            hw_tgt='00:00:00:00:00:00',
        )

        for i in range(5):
            self.dataplane.send(port, str(arp_request))
            (_, pkt, _) = self.dataplane.poll(port_number=port, timeout=1)
            if pkt is not None:
                hex_pkt = pkt.encode('hex')
            else:
                continue

            if debug:
                print 'Received packet from port {}'.format(port)
                print 'src mac = {}'.format(hex_pkt[0:12])
                print 'dst mac = {}'.format(hex_pkt[12:24])
                print 'ether type = {}'.format(hex_pkt[24:28])
                print 'arp op = {}'.format(hex_pkt[40:44])

            spine = None
            if hex_pkt is not None and hex_pkt[24:28] == '0806' and hex_pkt[40:44] == '0002':
                if hex_pkt[12:24] == cfg.spine0['mac'].replace(':', ''):
                    spine = cfg.spine0
                elif hex_pkt[12:24] == cfg.spine1['mac'].replace(':', ''):
                    spine = cfg.spine1
                else:
                    assert False, 'Getting spine MAC address fail! '

            if debug:
                print spine

            wait_for_seconds(1)

        assert spine is not None, 'Get master spine failure!'
        return spine

    def send_icmp_echo_request(self, sender, target, dst_ip, port):
        icmp_echo_request = simple_icmp_packet(
            eth_dst=target['mac'],
            eth_src=sender['mac'],
            ip_src=sender['ip'],
            ip_dst=dst_ip,
        )

        for i in range(5):
            self.dataplane.send(port, str(icmp_echo_request))
            wait_for_seconds(1)

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

class DHCPRelaySetAndGetTest(DHCPRelayTest):
    """
    Test DHCP relay set and get api
    """

    def runTest(self):

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', ['192.168.50.1'], '50')
            .build()
        )

        dhcp_relay = (
            DHCPRelay('t1', 's1')
            .servers(['192.168.200.10'])
            .build()
        )

        actual_dhcp_relay = dhcp_relay.get_content()
        assert(dhcp_relay._tenant == actual_dhcp_relay['dhcpRelayServers'][0]['tenant'])
        assert(dhcp_relay._segment == actual_dhcp_relay['dhcpRelayServers'][0]['segment'])
        assert(dhcp_relay._servers_list == actual_dhcp_relay['dhcpRelayServers'][0]['servers'])

class DHCPRelayTransmitPacketTest(DHCPRelayTest):
    """
    Test DHCP relay transimit packet
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        case_item_list = [
            #s1_vlan_id s2_vlan_id  s1_vlan_ip       s2_vlan_ip         dhcp_server_ip      allocated_ip
            (50,        100,        '192.168.50.1', '192.168.100.1',    '192.168.100.20',   '192.168.50.51'),
            (60,        200,        '192.168.60.1', '192.168.200.1',    '192.168.200.20',   '192.168.60.51')
        ]

        for case_item in case_item_list:
            s1_vlan_id = case_item[0]
            s2_vlan_id = case_item[1]
            s1_vlan_ip = case_item[2]
            s2_vlan_ip = case_item[3]
            dhcp_server_ip = case_item[4]
            allocated_ip = case_item[5]

            t1 = (
                Tenant('t1')
                .segment('s1', 'vlan', [s1_vlan_ip], s1_vlan_id)
                .segment_member('s1', [cfg.leaf0['portA'].name], cfg.leaf0['id'])
                .segment('s2', 'vlan', [s2_vlan_ip], s2_vlan_id)
                .segment_member('s2', [cfg.leaf1['portA'].name, cfg.leaf1['portB'].name], cfg.leaf1['id'])
                .build()
            )

            lrouter = (
                LogicalRouter('r1', 't1')
                .interfaces(['s1', 's2'])
                .build()
            )

            dhcp_relay = (
                DHCPRelay('t1', 's1')
                .servers([dhcp_server_ip])
                .build()
            )

            cfg.dhcp_server['ip'] = dhcp_server_ip

            spine = get_master_spine(self.dataplane, cfg.dhcp_server, s1_vlan_ip, ports[3])
            send_icmp_echo_request(self.dataplane, cfg.dhcp_server, spine, s2_vlan_ip, ports[3])

            # verify dhcp discover
            dhcp_discover = (
                super(DHCPRelayTransmitPacketTest, self)
                .generate_discover_pkt(cfg.host0)
            )
            expected_dhcp_discover = (
                super(DHCPRelayTransmitPacketTest, self)
                .generate_expected_discover_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s2_vlan_ip)
            )

            self.dataplane.send(ports[0], str(dhcp_discover))
            verify_packet(self, str(expected_dhcp_discover), ports[3])

            # verify dhcp offer
            dhcp_offer = (
                super(DHCPRelayTransmitPacketTest, self)
                .generate_offer_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
            )
            expected_dhcp_offer = (
                super(DHCPRelayTransmitPacketTest, self)
                .generate_expected_offer_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
            )

            self.dataplane.send(ports[3], str(dhcp_offer))
            verify_packet(self, str(expected_dhcp_offer), ports[0])

            # verify dhcp request
            dhcp_request = (
                super(DHCPRelayTransmitPacketTest, self)
                .generate_request_pkt(cfg.dhcp_server, cfg.host0, allocated_ip)
            )
            expected_dhcp_request = (
                super(DHCPRelayTransmitPacketTest, self)
                .generate_expected_request_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s2_vlan_ip, allocated_ip)
            )

            self.dataplane.send(ports[0], str(dhcp_request))
            verify_packet(self, str(expected_dhcp_request), ports[3])

            # verify dhcp ack
            dhcp_ack = (
                super(DHCPRelayTransmitPacketTest, self)
                .generate_ack_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
            )
            expected_dhcp_ack = (
                super(DHCPRelayTransmitPacketTest, self)
                .generate_expected_ack_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
            )

            self.dataplane.send(ports[3], str(dhcp_ack))
            verify_packet(self, str(expected_dhcp_ack), ports[0])

            dhcp_relay.destroy()
            lrouter.destroy()
            t1.destroy()

            # clear queue packet
            self.dataplane.flush()

            wait_for_system_stable()

class DHCPRelayMultipleServerTest(DHCPRelayTest):
    """
    Test DHCP relay with multiple server
    """
    def runTest(self):
        ports = sorted(config["port_map"].keys())

        s1_vlan_id = 50
        s2_vlan_id = 100
        s1_vlan_ip = '192.168.50.1'
        s2_vlan_ip = '192.168.100.1'
        allocated_ip = '192.168.50.51'

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_vlan_ip], s1_vlan_id)
            .segment_member('s1', [cfg.leaf0['portA'].name], cfg.leaf0['id'])
            .segment('s2', 'vlan', [s2_vlan_ip], s2_vlan_id)
            .segment_member('s2', [cfg.leaf1['portA'].name, cfg.leaf1['portB'].name], cfg.leaf1['id'])
            .build()
        )

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .build()
        )

        dhcp_relay = (
            DHCPRelay('t1', 's1')
            .servers(['192.168.100.20', '192.168.100.30', '192.168.100.40'])
            .build()
        )

        cfg.dhcp_server['ip'] = '192.168.100.20'

        spine = get_master_spine(self.dataplane, cfg.dhcp_server, s1_vlan_ip, ports[3])
        send_icmp_echo_request(self.dataplane, cfg.dhcp_server, spine, s2_vlan_ip, ports[3])

        # verify dhcp discover
        dhcp_discover = (
            super(DHCPRelayMultipleServerTest, self)
            .generate_discover_pkt(cfg.host0)
        )
        expected_dhcp_discover = (
            super(DHCPRelayMultipleServerTest, self)
            .generate_expected_discover_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s2_vlan_ip)
        )

        self.dataplane.send(ports[0], str(dhcp_discover))
        verify_packet(self, str(expected_dhcp_discover), ports[3])

        # verify dhcp offer
        dhcp_offer = (
            super(DHCPRelayMultipleServerTest, self)
            .generate_offer_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        )
        expected_dhcp_offer = (
            super(DHCPRelayMultipleServerTest, self)
            .generate_expected_offer_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        )

        self.dataplane.send(ports[3], str(dhcp_offer))
        verify_packet(self, str(expected_dhcp_offer), ports[0])

        # verify dhcp request
        dhcp_request = (
            super(DHCPRelayMultipleServerTest, self)
            .generate_request_pkt(cfg.dhcp_server, cfg.host0, allocated_ip)
        )
        expected_dhcp_request = (
            super(DHCPRelayMultipleServerTest, self)
            .generate_expected_request_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s2_vlan_ip, allocated_ip)
        )

        self.dataplane.send(ports[0], str(dhcp_request))
        verify_packet(self, str(expected_dhcp_request), ports[3])

        # verify dhcp ack
        dhcp_ack = (
            super(DHCPRelayMultipleServerTest, self)
            .generate_ack_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        )
        expected_dhcp_ack = (
            super(DHCPRelayMultipleServerTest, self)
            .generate_expected_ack_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        )

        self.dataplane.send(ports[3], str(dhcp_ack))
        verify_packet(self, str(expected_dhcp_ack), ports[0])

        dhcp_relay.destroy()
        lrouter.destroy()
        t1.destroy()

class DHCPRelayCrossSystemTenantTest(DHCPRelayTest):
    """
    Test DHCP relay cross system tenant
    """
    def runTest(self):
        ports = sorted(config["port_map"].keys())

        s1_vlan_id = 50
        s2_vlan_id = 100
        s3_vlan_id = 60
        s4_vlan_id = 200
        s1_vlan_ip = '192.168.50.1'
        s2_vlan_ip = '192.168.100.1'
        s3_vlan_ip = '192.168.60.1'
        s4_vlan_ip = '192.168.200.1'
        dhcp_server_ip = '192.168.200.10'
        allocated_ip = '192.168.50.51'

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_vlan_ip], s1_vlan_id)
            .segment_member('s1', [cfg.leaf0['portA'].name], cfg.leaf0['id'])
            .segment('s2', 'vlan', [s2_vlan_ip], s2_vlan_id)
            .segment_member('s2', [cfg.leaf0['portB'].name], cfg.leaf0['id'])
            .build()
        )

        t2 = (
            Tenant('t2')
            .segment('s3', 'vlan', [s3_vlan_ip], s3_vlan_id)
            .segment_member('s3', [cfg.leaf1['portA'].name], cfg.leaf1['id'])
            .segment('s4', 'vlan', [s4_vlan_ip], s4_vlan_id)
            .segment_member('s4', [cfg.leaf1['portB'].name], cfg.leaf1['id'])
            .build()
        )

        lrouter_r1 = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .build()
        )

        lrouter_r2 = (
            LogicalRouter('r2', 't2')
            .interfaces(['s3', 's4'])
            .build()
        )

        system_tenant = (
            Tenant('system', 'System')
            .build()
        )

        lrouter_system = (
            LogicalRouter('system')
            .tenant_routers(['t1/r1', 't2/r2'])
            .build()
        )

        dhcp_relay = (
            DHCPRelay('t1', 's1')
            .servers([dhcp_server_ip])
            .build()
        )

        cfg.dhcp_server['ip'] = dhcp_server_ip

        #TODO: this case needs VRF feature
        spine = get_master_spine(self.dataplane, cfg.dhcp_server, s1_vlan_ip, ports[3])
        send_icmp_echo_request(self.dataplane, cfg.dhcp_server, spine, s2_vlan_ip, ports[3])

        # verify dhcp discover
        dhcp_discover = (
            super(DHCPRelayCrossSystemTenantTest, self)
            .generate_discover_pkt(cfg.host0)
        )
        expected_dhcp_discover = (
            super(DHCPRelayCrossSystemTenantTest, self)
            .generate_expected_discover_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s4_vlan_ip)
        )

        self.dataplane.send(ports[0], str(dhcp_discover))
        verify_packet(self, str(expected_dhcp_discover), ports[3])

        # verify dhcp offer
        dhcp_offer = (
            super(DHCPRelayCrossSystemTenantTest, self)
            .generate_offer_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        )
        expected_dhcp_offer = (
            super(DHCPRelayCrossSystemTenantTest, self)
            .generate_expected_offer_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        )

        self.dataplane.send(ports[3], str(dhcp_offer))
        verify_packet(self, str(expected_dhcp_offer), ports[0])

        # verify dhcp request
        dhcp_request = (
            super(DHCPRelayCrossSystemTenantTest, self)
            .generate_request_pkt(cfg.dhcp_server, cfg.host0, allocated_ip)
        )
        expected_dhcp_request = (
            super(DHCPRelayCrossSystemTenantTest, self)
            .generate_expected_request_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, s4_vlan_ip, allocated_ip)
        )

        self.dataplane.send(ports[0], str(dhcp_request))
        verify_packet(self, str(expected_dhcp_request), ports[3])

        # verify dhcp ack
        dhcp_ack = (
            super(DHCPRelayCrossSystemTenantTest, self)
            .generate_ack_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        )
        expected_dhcp_ack = (
            super(DHCPRelayCrossSystemTenantTest, self)
            .generate_expected_ack_pkt(spine, cfg.dhcp_server, cfg.host0, s1_vlan_ip, allocated_ip)
        )

        self.dataplane.send(ports[3], str(dhcp_ack))
        verify_packet(self, str(expected_dhcp_ack), ports[0])

        dhcp_relay.destroy()
        lrouter_r1.destroy()
        lrouter_r2.destroy()
        lrouter_system.destroy()
        system_tenant.destroy()
        t1.destroy()
        t2.destroy()


@disabled
class DHCPRelayPhysicalServerTest(DHCPRelayTest):
    """
    Test DHCP relay with physical server for manual test
    """

    def tearDown(self):
        DHCPRelayTest.tearDown(self)

    def runTest(self):
        s1_vlan_id = 50
        s2_vlan_id = 100
        s1_vlan_ip = '192.168.50.1'
        s2_vlan_ip = '192.168.100.1'
        dhcp_server_ip = '192.168.100.10'
        ports = sorted(config["port_map"].keys())

        t1 = (
            Tenant('t1')
            .segment('s1', 'vlan', [s1_vlan_ip], s1_vlan_id)
            .segment_member('s1', ['45/untag'], cfg.leaf0['id'])
            .segment('s2', 'vlan', [s2_vlan_ip], s2_vlan_id)
            .segment_member('s2', ['45/untag', '47/untag'], cfg.leaf1['id'])
            .build()
        )

        lrouter = (
            LogicalRouter('r1', 't1')
            .interfaces(['s1', 's2'])
            .build()
        )

        dhcp_relay = (
            DHCPRelay('t1', 's1')
            .servers([dhcp_server_ip])
            .build()
        )

        cfg.dhcp_server['ip'] = dhcp_server_ip
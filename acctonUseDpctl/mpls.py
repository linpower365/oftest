import logging
import oftest.base_tests as base_tests
import time
from oftest import config
from oftest.testutils import *
from util import *
from accton_util import convertIP4toStr as toIpV4Str
from accton_util import convertMACtoStr as toMacStr

class encap_mpls(base_tests.SimpleDataPlane):
    """
    [Encap one MPLS label]
      Encap a MPLS label

    Inject  eth 1/3 Tag 3, SA000000112233, DA000000113355, V4
    Output  eth 1/1 Tag 2, SA000004223355, DA000004224466, MPLS label 2305, EXP7, BoS1, TTL250, CW

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x20001 goto:60
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3 apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x2000"+str(output_port)+" goto:60")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000001")
        apply_dpctl_mod(self, config, "flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+" apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(output_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(output_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 1f fa 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 03 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b2 47 c0 a8 01 64 c0 a8 02 02 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class decap_mpls(base_tests.SimpleDataPlane):
    """
    [Decap one MPLS label]
      Decap the MPLS label

    Inject  eth 1/1 Tag 2, SA000004223355, DA000004224466, MPLS label 2305, EXP7, BoS1, TTL250, CW, InSA000000112233, InDA000000113355
    Output  eth 1/3 SA000000112233, DA000000113355

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x20001 goto:60
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3 apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(input_port)+" group=any,port=any,weight=0 output="+str(input_port))
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x2000"+str(input_port)+" goto:60")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(input_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000001")
        apply_dpctl_mod(self, config, "flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(output_port)+" apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 1f fa 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 05 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 '
                '02 01 c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 '
                '0a 0b 0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19 '
                '00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class encap_2mpls(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels]
      Encap two MPLS labels

    Inject  eth 1/3 Tag 3, SA000000112233, DA000000113355
    Output  eth 1/1 Tag 2, Outer label 0x903, TTL 250, InLabel 0x901, TTL 250, SA000004223355, DA000004224466

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x20001 goto:60
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x903,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x2000"+str(output_port)+" goto:60")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x903,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000001")
        apply_dpctl_mod(self, config, "flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class encap_3mpls(base_tests.SimpleDataPlane):
    """
    [Encap 3 MPLS labels]
      Encap 3 MPLS labels

    Inject  eth 1/3 Tag 3, SA000000112233, DA000000113355
    Output  eth 1/1 Tag 2, Outest label 0x904, TTL 250, Middle label 0x903, InLabel 0x901, SA000004223355, DA000004224466

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x20001 goto:60
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x94000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x904,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x903,group=0x94000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x2000"+str(output_port)+" goto:60")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x94000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x904,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x903,group=0x94000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000001")
        apply_dpctl_mod(self, config, "flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 4e fa 00 90 3e fa 00 90 1f fa 00 00 '
                '00 00 00 00 00 11 33 55 00 00 00 11 22 33 81 00 '
                '00 03 08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 '
                'c0 a8 01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class decap_penultimate_mpls(base_tests.SimpleDataPlane):
    """
    [Penultimate Hop Pop]
      Pop outermost tunnel label

    Inject  eth 1/1 Tag 2, Outer label 0x901, InLabel 0xF, SA000004223355, DA000004224466
    Output  eth 1/3 Tag 2, label 0xF, SA000004223355, DA000004224466

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901 apply:pop_mpls=0x8847,mpls_dec write:group=0x90000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901 apply:pop_mpls=0x8847,mpls_dec write:group=0x90000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 1e fa 00 01 0b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 01 0f f9 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class decap_2mpls(base_tests.SimpleDataPlane):
    """
    [Pop, decap, and L2 forward]
      Pop outermost tunnel label and pop outer L2 header (L2 Switch VPWS )

    Inject  eth 1/1 Tag 2, Outer label 0x903, InLabel 0x901, SA000004223355, DA000004224466; InTag 5, InSA000000112233, InDA000000113355
    Output  eth 1/3 Tag 5, SA000000112233, DA000000113355

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x00008847 goto:24
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x20001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(input_port)+" group=any,port=any,weight=0 output="+str(input_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(input_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000001")
        apply_dpctl_mod(self, config, "flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(output_port)+",vlan_vid=0x1002/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x00008847 goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x2000"+str(input_port)+" goto:60")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 05 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 '
                '02 01 c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 '
                '0a 0b 0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class decap_penultimate_swap_mpls(base_tests.SimpleDataPlane):
    """
    [Penultimate Hop Pop and swap inner MPLS label]
      Pop outermost tunnel label and swap inner MPLS label (MS-PW, LSR)

    Inject  eth 1/1 Tag 2, Outer label 0x903, InLabel 0x901, SA000004223355, DA000004224466; InTag 5, InSA000000112233, InDA000000113355
    Output  eth 1/3 Tag 2, Label 0x905, TTL 249, SA000004223355, DA000004224466

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x905,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0x95000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000001")
        apply_dpctl_mod(self, config, "flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x905,group=0x90000001")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0x95000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 51 f9 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class decap_penultimate_swap_ff_mpls(base_tests.SimpleDataPlane):
    """
    [Penultimate Hop Pop and swap inner MPLS label]
      Pop outermost tunnel label and swap inner MPLS label (MS-PW, LSR)

    Inject  eth 1/1 Tag 2, Outer label 0x903, InLabel 0x901, SA000004223355, DA000004224466; InTag 5, InSA000000112233, InDA000000113355

    -- working up --
    Output  eth 1/4 Tag 2, Label 0x905, TTL 249, SA000004223354, DA000004224464
    -- working down --
    Output  eth 1/2 Tag 2, Label 0x905, TTL 249, SA000004223352, DA000004224462

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:52,set_field=eth_dst=00:00:04:22:44:62,set_field=vlan_vid=2,group=0x20002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20004 group=any,port=any,weight=0 output=4
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x20004

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=4,weight=0 group=0x90000004 group=any,port=2,weight=0 group=0x90000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x905,group=0xA6000001

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0x95000001 goto:60
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:23
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port1 = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x2000"+str(output_port2))

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port1)+" group=any,port=any,weight=0 output="+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port1))

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port2)+",weight=0 group=0x90000004 group=any,port="+str(output_port1)+",weight=0 group=0x90000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x905,group=0xA6000001")

        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0x95000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:23")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt1 = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 90 51 f9 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19')

        output_pkt2 = simple_packet(
                '00 00 04 22 44 64 00 00 04 22 33 54 81 00 00 02 '
                '88 47 00 90 51 f9 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt2), output_port2)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port2)+",conf=0x1,mask=0x1")
        time.sleep(5)
        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port2)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port2:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1
        #check if output_port2 receives packet
        verify_packet(self, str(output_pkt1), output_port1)


class decap_penultimate_ff_swap_mpls(base_tests.SimpleDataPlane):
    """
    [Penultimate Hop Pop and swap inner MPLS label]
      Pop outermost tunnel label and swap inner MPLS label (MS-PW, LSR)

    Inject  eth 1/1 Tag 2, Outer label 0x903, InLabel 0x901, SA000004223355, DA000004224466; InTag 5, InSA000000112233, InDA000000113355

    -- working up --
    Output  eth 1/4 Tag 2, Label 0x9054, TTL 249, SA000004223354, DA000004224464
    -- working down --
    Output  eth 1/2 Tag 2, Label 0x905, TTL 249, SA000004223352, DA000004224462

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:52,set_field=eth_dst=00:00:04:22:44:62,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x95000002 group=any,port=any,weight=0 set_field=mpls_label:0x9052,group=0x90000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20004 group=any,port=any,weight=0 output=4
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x20004
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x95000004 group=any,port=any,weight=0 set_field=mpls_label:0x9054,group=0x90000004

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=4,weight=0 group=0x95000004 group=any,port=2,weight=0 group=0x95000002

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0xA6000001 goto:60
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:23
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port1 = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000004 group=any,port=any,weight=0 set_field=mpls_label:0x9054,group=0x90000004")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port1)+" group=any,port=any,weight=0 output="+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000002 group=any,port=any,weight=0 set_field=mpls_label:0x9052,group=0x90000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port2)+",weight=0 group=0x95000004 group=any,port="+str(output_port1)+",weight=0 group=0x95000002")

        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0xA6000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:23")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt1 = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 09 05 21 f9 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19')

        output_pkt2 = simple_packet(
                '00 00 04 22 44 64 00 00 04 22 33 54 81 00 00 02 '
                '88 47 09 05 41 f9 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt2), output_port2)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port2)+",conf=0x1,mask=0x1")
        time.sleep(5)
        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port2)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port2:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1
        #check if output_port2 receives packet
        verify_packet(self, str(output_pkt1), output_port1)


class decap_penultimate_ff_swap_add_mpls(base_tests.SimpleDataPlane):
    """
    [Penultimate Hop Pop and swap inner MPLS label]
      Pop outermost tunnel label and swap inner MPLS label (MS-PW, LSR)

    Inject  eth 1/1 Tag 2, Outer label 0x903, InLabel 0x901, SA000004223355, DA000004224466; InTag 5, InSA000000112233, InDA000000113355

    -- working up --
    Output  eth 1/4 Tag 2, outer Label 0x934, InLabel 0x954, DA000004224464
    -- working down --
    Output  eth 1/1 Tag 2, outer Label 0x931, InLabel 0x951, DA000004224461

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000001
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x951,group=0x93000001

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x20004 group=any,port=any,weight=0 output=4
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x20004
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x93000004 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x934,group=0x90000004
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x95000004 group=any,port=any,weight=0 set_field=mpls_label:0x954,group=0x93000004

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=4,weight=0 group=0x95000004 group=any,port=1,weight=0 group=0x95000001

    ./dpctl tcp:192.168.2.1:6633 flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24
    ./dpctl tcp:192.168.2.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0xA6000001 goto:60
    ./dpctl tcp:192.168.2.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=2,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.2.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=2,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:23
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        output_port1 = test_ports[0]
        input_port = test_ports[1]
        output_port4 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port4)+" group=any,port=any,weight=0 output="+str(output_port4))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x2000"+str(output_port4))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000004 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x934,group=0x90000004")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000004 group=any,port=any,weight=0 set_field=mpls_label:0x954,group=0x93000004")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port1)+" group=any,port=any,weight=0 output="+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x951,group=0x93000001")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port4)+",weight=0 group=0x95000004 group=any,port="+str(output_port1)+",weight=0 group=0x95000001")

        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0xA6000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:23")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt1 = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 10 f9 00 95 11 f9 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt2 = simple_packet(
                '00 00 04 22 44 64 00 00 04 22 33 54 81 00 00 02 '
                '88 47 00 93 40 f9 00 95 41 f9 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt2), output_port4)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port4)+",conf=0x1,mask=0x1")
        time.sleep(5)
        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port4)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port4:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1
        #check if output_port1 receives packet
        verify_packet(self, str(output_pkt1), output_port1)


class swap_out_mpls(base_tests.SimpleDataPlane):
    """
    [Swap outermost MPLS label]
      Swap outermost MPLS label (LSR)

    Inject  eth 1/1 Tag 2, Outer label 0x901, TTL 250, InLabel 0xF, DA000004223355, SA000004224466
    Output  eth 1/3 Tag 2, Outer label 0x9051, TTL 249, InLabel 0xF, SA000004223357, DA000004224467

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:57,set_field=eth_dst=00:00:04:22:44:67,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9051,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901 apply:mpls_dec write:group=0x95000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:57,set_field=eth_dst=00:00:04:22:44:67,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9051,group=0x90000001")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901 apply:mpls_dec write:group=0x95000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 1e fa 00 01 0b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt = simple_packet(
                '00 00 04 22 44 67 00 00 04 22 33 57 81 00 00 02 '
                '88 47 09 05 10 f9 00 01 0b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class swap_ff_out_mpls(base_tests.SimpleDataPlane):
    """
    [Swap outermost MPLS label]
      Swap outermost MPLS label (LSR)

    Inject  eth 1/2 Tag 2, Outer label 0x901, TTL 250, InLabel 0xF, DA000004223355, SA000004224466

    -- working up --
    Output  eth 1/4 Tag 2, Outer label 0x9051, TTL 249, InLabel 0xF, SA000004223354, DA000004224464
    -- working down --
    Output  eth 1/1 Tag 2, Outer label 0x9051, TTL 249, InLabel 0xF, SA000004223351, DA000004224461

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20001

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20004 group=any,port=any,weight=0 output=4
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x20004

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=4,weight=0 group=0x90000004 group=any,port=1,weight=0 group=0x90000001

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9051,group=0xA6000001
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901 apply:mpls_dec write:group=0x95000001 goto:60
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=2,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=20,cmd=add,prio=201 in_port=2,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port1 = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port1)+" group=any,port=any,weight=0 output="+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x2000"+str(output_port2))

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port1)+",weight=0 group=0x90000001 group=any,port="+str(output_port2)+",weight=0 group=0x90000004")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9051,group=0xA6000001")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901 apply:mpls_dec write:group=0x95000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 1e fa 00 01 0b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt1 = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 09 05 10 f9 00 01 0b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt1), output_port1)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port1)+",conf=0x1,mask=0x1")
        time.sleep(5)
        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port1)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port1:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1
        #check if output_port2 receives packet
        output_pkt2 = simple_packet(
                '00 00 04 22 44 64 00 00 04 22 33 54 81 00 00 02 '
                '88 47 09 05 10 f9 00 01 0b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')
        verify_packet(self, str(output_pkt2), output_port2)


class swap_encap_mpls(base_tests.SimpleDataPlane):
    """
    [Swap and encap a MPLS label]
      Swap and encap a MPLS label

    Inject  eth 1/1 Tag 2, MPLS label 0x901, TTL 250, DA000004223355, SA000004224466
    Output  eth 1/3 Tag 2, Outer label 0x9052, TTL 249, InLabel 0xF, SA000004223358, DA000004224468

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:58,set_field=eth_dst=00:00:04:22:44:68,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9052,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0x95000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:58,set_field=eth_dst=00:00:04:22:44:68,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9052,group=0x90000001")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0x95000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 1f fa 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 68 00 00 04 22 33 58 81 00 00 02 '
                '88 47 09 05 21 f9 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class swap_encap_2mpls(base_tests.SimpleDataPlane):
    """
    [Swap and encap 2 MPLS labels]
      Swap and encap 2 MPLS labels

    Inject  eth 1/1 Tag 2, MPLS label 0x901, TTL 250, DA000004223355, SA000004224466
    Output  eth 1/3 Tag 2, Outest label 0x904, TTL 249, Middle label 0x903, InLabel 0x9052, SA000004223358, DA000004224468

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:58,set_field=eth_dst=00:00:04:22:44:68,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x94000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x904,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x903,group=0x94000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9052,group=0x93000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0x95000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:58,set_field=eth_dst=00:00:04:22:44:68,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x94000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x904,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x903,group=0x94000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9052,group=0x93000001")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0x95000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 1f fa 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 68 00 00 04 22 33 58 81 00 00 02 '
                '88 47 00 90 40 f9 00 90 30 f9 09 05 21 f9 00 00 '
                '00 00 00 00 00 11 33 55 00 00 00 11 22 33 81 00 '
                '00 05 08 00 45 00 00 2e 04 d2 00 00 7f 00 b1 aa '
                'c0 a8 02 01 c0 a8 02 02 00 01 02 03 04 05 06 07 '
                '08 09 0a 0b 0c 0d 0e 0f 10 11 12 13 14 15 16 17 '
                '18 19 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class ff_swap_1mpls(base_tests.SimpleDataPlane):
    """
    [FF and swap a MPLS label]
      FF and swap a MPLS label

    Inject  eth 1/2 Tag 2, MPLS label 0x901, TTL 250, DA000004223355, SA000004224466

    --- working port4 up ---
    Output  eth 1/4 Tag 2, label 0x9054, TTL 249, SA000004223354, DA000004224464
    --- working port4 down ---
    Output  eth 1/1 Tag 2, label 0x9051, TTL 249, SA000004223351, DA000004224461

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9051,group=0x90000001

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x20004 group=any,port=any,weight=0 output=4
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x20004
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x95000004 group=any,port=any,weight=0 set_field=mpls_label:0x9054,group=0x90000004

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=4,weight=0 group=0x95000004 group=any,port=1,weight=0 group=0x95000001

    ./dpctl tcp:192.168.2.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0xA6000001 goto:60
    ./dpctl tcp:192.168.2.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=2,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.2.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=2,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        output_port1 = test_ports[0]
        input_port = test_ports[1]
        output_port4 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port1)+" group=any,port=any,weight=0 output="+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9051,group=0x90000001")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port4)+" group=any,port=any,weight=0 output="+str(output_port4))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x2000"+str(output_port4))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000004 group=any,port=any,weight=0 set_field=mpls_label:0x9054,group=0x90000004")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port4)+",weight=0 group=0x95000004 group=any,port="+str(output_port1)+",weight=0 group=0x95000001")

        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0xA6000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 1f fa 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19 00 00 00 00')

        output_pkt1 = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 09 05 11 f9 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19 00 00 00 00')

        output_pkt4 = simple_packet(
                '00 00 04 22 44 64 00 00 04 22 33 54 81 00 00 02 '
                '88 47 09 05 41 f9 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt4), output_port4)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port4)+",conf=0x1,mask=0x1")
        time.sleep(5)
        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port4)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port4:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1
        #check if output_port2 receives packet
        verify_packet(self, str(output_pkt1), output_port1)


class ff_swap_outer_mpls(base_tests.SimpleDataPlane):
    """
    [FF and swap outer MPLS label]
      FF and swap outer MPLS label

    Inject  eth 1/2 Tag 2, Outer label 0x901, TTL 250, InLabel 0xF, DA000004223355, SA000004224466

    --- working port4 up ---
    Output  eth 1/4 Tag 2, label 0x9054, TTL 249, InLabel 0xF, SA000004223354, DA000004224464
    --- working port4 down ---
    Output  eth 1/1 Tag 2, label 0x9051, TTL 249, InLabel 0xF, SA000004223351, DA000004224461

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9051,group=0x90000001

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x20004 group=any,port=any,weight=0 output=4
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x20004
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x95000004 group=any,port=any,weight=0 set_field=mpls_label:0x9054,group=0x90000004

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=4,weight=0 group=0x95000004 group=any,port=1,weight=0 group=0x95000001

    ./dpctl tcp:192.168.2.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=0 apply:mpls_dec write:group=0xA6000001 goto:60
    ./dpctl tcp:192.168.2.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=2,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.2.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=2,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        output_port1 = test_ports[0]
        input_port = test_ports[1]
        output_port4 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port1)+" group=any,port=any,weight=0 output="+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x9051,group=0x90000001")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port4)+" group=any,port=any,weight=0 output="+str(output_port4))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x2000"+str(output_port4))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000004 group=any,port=any,weight=0 set_field=mpls_label:0x9054,group=0x90000004")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port4)+",weight=0 group=0x95000004 group=any,port="+str(output_port1)+",weight=0 group=0x95000001")

        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=0 apply:mpls_dec write:group=0xA6000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 1e fa 00 01 0b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt1 = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 09 05 10 f9 00 01 0b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt4 = simple_packet(
                '00 00 04 22 44 64 00 00 04 22 33 54 81 00 00 02 '
                '88 47 09 05 40 f9 00 01 0b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt4), output_port4)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port4)+",conf=0x1,mask=0x1")
        time.sleep(5)
        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port4)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port4:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1
        #check if output_port2 receives packet
        verify_packet(self, str(output_pkt1), output_port1)


class ff_swap_add_mpls(base_tests.SimpleDataPlane):
    """
    [FF and add a MPLS label]
      FF and add a MPLS label

    Inject  eth 1/2 Tag 2, MPLS label 0x901, TTL 250, DA000004223355, SA000004224466

    -- working up --
    Output  eth 1/4 Tag 2, outer Label 0x934, InLabel 0x954, DA000004224464
    -- working down --
    Output  eth 1/1 Tag 2, outer Label 0x931, InLabel 0x951, DA000004224461

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000001
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x951,group=0x93000001

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x20004 group=any,port=any,weight=0 output=4
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x20004
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x93000004 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x934,group=0x90000004
    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ind,group=0x95000004 group=any,port=any,weight=0 set_field=mpls_label:0x954,group=0x93000004

    ./dpctl tcp:192.168.2.1:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=4,weight=0 group=0x95000004 group=any,port=1,weight=0 group=0x95000001

    ./dpctl tcp:192.168.2.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0xA6000001 goto:60
    ./dpctl tcp:192.168.2.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=2,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.2.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=2,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        output_port1 = test_ports[0]
        input_port = test_ports[1]
        output_port4 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port1)+" group=any,port=any,weight=0 output="+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port1))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000001 group=any,port=any,weight=0 set_field=mpls_label:0x951,group=0x93000001")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port4)+" group=any,port=any,weight=0 output="+str(output_port4))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000004 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:54,set_field=eth_dst=00:00:04:22:44:64,set_field=vlan_vid=2,group=0x2000"+str(output_port4))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000004 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x934,group=0x90000004")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x95000004 group=any,port=any,weight=0 set_field=mpls_label:0x954,group=0x93000004")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port4)+",weight=0 group=0x95000004 group=any,port="+str(output_port1)+",weight=0 group=0x95000001")

        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:mpls_dec write:group=0xA6000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 1f fa 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19 00 00 00 00')

        output_pkt1 = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 10 f9 00 95 11 f9 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19 00 00 '
                '00 00')

        output_pkt4 = simple_packet(
                '00 00 04 22 44 64 00 00 04 22 33 54 81 00 00 02 '
                '88 47 00 93 40 f9 00 95 41 f9 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19 00 00 '
                '00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt4), output_port4)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port4)+",conf=0x1,mask=0x1")
        time.sleep(5)
        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port4)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port4:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1
        #check if output_port2 receives packet
        verify_packet(self, str(output_pkt1), output_port1)


class decap_1mpls_of3(base_tests.SimpleDataPlane):
    """
    [Decap outermost MPLS label of 3 MPLS labels]
      Decap outermost one MPLS of 3 MPLS labels

    Inject  eth 1/1 Tag 2, Outest label 0x904, TTL 250, Middle label 0x903/250, InLabel 0x901/250, SA000004224466, DA000004223355
    Output  eth 1/3 Tag 2, Outer label 0x903/249, InLabel 0x901/250, SA000004223355, DA000004224466

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x904 apply:pop_mpls=0x8847,mpls_dec write:group=0x90000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x904 apply:pop_mpls=0x8847,mpls_dec write:group=0x90000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 4e fa 00 90 3e fa 00 90 1f fa 00 00 '
                '00 00 00 00 00 11 33 55 00 00 00 11 22 33 00 00 '
                '00 03 08 00 45 00 00 2e 04 d2 00 00 7f 00 b1 aa '
                'c0 a8 02 01 c0 a8 02 02 00 01 02 03 04 05 06 07 '
                '08 09 0a 0b 0c 0d 0e 0f 10 11 12 13 14 15 16 17 '
                '18 19')

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 3e f9 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 00 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class decap_2mpls_of3(base_tests.SimpleDataPlane):
    """
    [Decap outermost 2 MPLS labels of 3 MPLS labels]
      Decap outermost two MPLS of 3 MPLS labels

    Inject  eth 1/1 Tag 2, Outest label 0x904, TTL 250, Middle label 0x903/250, InLabel 0x901/250, SA000004224466, DA000004223355
    Output  eth 1/3 Tag 2, MPLS Label 0x901/249, SA000004223355, DA000004224466

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x904 apply:pop_mpls=0x8847,mpls_dec goto:24
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec write:group=0x90000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x904 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec write:group=0x90000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 4e fa 00 90 3e fa 00 90 1f fa 00 00 '
                '00 00 00 00 00 11 33 55 00 00 00 11 22 33 00 00 '
                '00 03 08 00 45 00 00 2e 04 d2 00 00 7f 00 b1 aa '
                'c0 a8 02 01 c0 a8 02 02 00 01 02 03 04 05 06 07 '
                '08 09 0a 0b 0c 0d 0e 0f 10 11 12 13 14 15 16 17 '
                '18 19')

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 1f f9 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 00 00 00 03 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class encap_2mpls_ff(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels with FF]
      Encap two MPLS labels with fast failover group

    Env eth 1/1 link up; eth 1/5 link down
    Inject  eth 1/3 Tag 3, SA000000112233, DA000000113355
    Output  eth 1/1 Tag 2, Outest label 0x931, TTL 250, InLabel 0x901, SA000004223351, DA000004224461

    Env eth 1/1 link down; eth 1/5 link up
    Inject  eth 1/3 Tag 3, SA000000112233, DA000000113355
    Output  eth 1/5 Tag 2, Outest label 0x935, TTL 250, InLabel 0x901, SA000004223355, DA000004224465

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20005 group=any,port=any,weight=0 output=5
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000005 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x20005
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000005 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000005
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=1,weight=0 group=0x93000001 group=any,port=5,weight=0 group=0x93000005
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x20001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]
        
        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000005 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000005 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000005")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port)+",weight=0 group=0x93000001 group=any,port="+str(output_port2)+",weight=0 group=0x93000005")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001")
        apply_dpctl_mod(self, config, "flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x2000"+str(output_port)+" goto:60")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt2 = simple_packet(
                '00 00 04 22 44 65 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 93 5e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x1,mask=0x1")
        time.sleep(5)
        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1
        #check if output_port2 receives packet
        verify_packet(self, str(output_pkt2), output_port2)


class decap_mpls_acl(base_tests.SimpleDataPlane):
    """
    [Decap a MPLS label with ACL]
      Decap a MPLS label with ACL

    Inject  eth 1/1 Tag 2, SA000004223355, DA000004224466, MPLS label 2305, EXP7, BoS1, TTL250, CW, InSA000000112233, InDA000000113355
    Output  eth 1/5 SA000000112233, DA000000113355

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x20001 goto:60
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3 apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20005 group=any,port=any,weight=0 output=5
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=60,cmd=add,prio=601 tunn_id=0x10001,ofdpa_mpls_l2_port=131328 write:group=0x20005
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(input_port)+" group=any,port=any,weight=0 output="+str(input_port))
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x2000"+str(input_port)+" goto:60")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(input_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000001")
        apply_dpctl_mod(self, config, "flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+" apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "flow-mod table=60,cmd=add,prio=601 tunn_id=0x10001,ofdpa_mpls_l2_port=131328 write:group=0x2000"+str(output_port))

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 1f fa 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 05 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b1 aa c0 a8 02 01 c0 a8 02 02 '
                '00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f '
                '10 11 12 13 14 15 16 17 18 19 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 05 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 '
                '02 01 c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 '
                '0a 0b 0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19 '
                '00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class encap_mpls_l3(base_tests.SimpleDataPlane):
    """
    [Encap a MPLS label with L3]
      Encap a MPLS label with L3 routing

    Inject  eth 1/3 Tag 2, SA000000112233, DA000000113355, SIP 192.168.1.10, DIP 192.168.2.2
    Output  eth 1/1 SA000004223355, DA000004224466, Tag2, MPLS label 0x901; IP the same as original

    ./dpctl tcp:192.168.1.1:6633 flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=3,vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.2.2/255.255.255.0 write:group=0x92000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0x90000001")
        apply_dpctl_mod(self, config, "flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.3.2/255.255.255.0 write:group=0x92000001 goto:60")

        input_pkt = simple_tcp_packet(pktlen=96,
                                       eth_dst='00:00:00:11:33:55',
                                       eth_src='00:00:00:11:22:33',
                                       ip_src='192.168.5.10',
                                       ip_dst='192.168.3.2',
                                       ip_ttl=64,
                                       vlan_vid=2,
                                       dl_vlan_enable=True)
        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 1f fa 45 00 00 4e 00 01 00 00 3f 06 '
                'f2 4c c0 a8 05 0a c0 a8 03 02 04 d2 00 50 00 00 '
                '00 00 00 00 00 00 50 02 20 00 f0 2c 00 00 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class decap_mpls_l3(base_tests.SimpleDataPlane):
    """
    [Decap a MPLS label with L3]
      Decap a MPLS label with L3 routing

    Inject  eth 1/3 Tag 12, SA000000112233, DA000000000111, MPLS 0x1234, SIP 192.168.3.1, DIP 192.168.2.1
    Output  eth 1/1 Tag 10, SA000006223355, DA000006224466, SIP 192.168.3.1, DIP 192.168.2.1

    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x100c/0x1fff apply:set_field=ofdpa_vrf:1 goto:20
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0xa0001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20000001 group=any,port=any,weight=0 set_field=eth_src=00:00:06:22:33:55,set_field=eth_dst=00:00:06:22:44:66,set_field=vlan_vid=10,group=0xa0001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x1234,mpls_bos=1,ofdpa_mpls_data_first_nibble=4 apply:mpls_dec,pop_mpls=0x0800,set_field=ofdpa_vrf:1 goto:30
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.3.2/255.255.255.0,ofdpa_vrf=1 write:group=0x20000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 vlan_vid=12/0xfff,eth_dst=00:00:00:00:01:11,eth_type=0x8847 goto:24
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x100c/0x1fff apply:set_field=ofdpa_vrf:1 goto:20")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0xa000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x20000001 group=any,port=any,weight=0 set_field=eth_src=00:00:06:22:33:55,set_field=eth_dst=00:00:06:22:44:66,set_field=vlan_vid=10,group=0xa000"+str(output_port))
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x1234,mpls_bos=1,ofdpa_mpls_data_first_nibble=4 apply:mpls_dec,pop_mpls=0x0800,set_field=ofdpa_vrf:1 goto:30")
        apply_dpctl_mod(self, config, "flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.3.2/255.255.255.0,ofdpa_vrf=1 write:group=0x20000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 vlan_vid=12/0xfff,eth_dst=00:00:00:00:01:11,eth_type=0x8847 goto:24")

        input_pkt = simple_packet(
                '00 00 00 00 01 11 00 00 00 11 22 33 81 00 00 0c '
                '88 47 01 23 41 3f 45 00 00 26 00 00 00 00 3f 00 '
                'f5 84 c0 a8 02 01 c0 a8 03 02 00 01 02 03 04 05 '
                '06 07 08 09 0a 0b 0c 0d 0e 0f 10 11 12 13 14 15 '
                '16 17 18 19')

        output_pkt = simple_packet(
                '00 00 06 22 44 66 00 00 06 22 33 55 81 00 00 0a '
                '08 00 45 00 00 26 00 00 00 00 3e 00 f6 84 c0 a8 '
                '02 01 c0 a8 03 02 00 01 02 03 04 05 06 07 08 09 '
                '0a 0b 0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class encap_2mpls_l3(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels with L3]
      Encap two MPLS labels with L3 routing

    Inject  eth 1/3 Tag 2, SA000000112233, DA000000113355, SIP 192.168.1.10, DIP 192.168.2.2
    Output  eth 1/1 SA000004223355, DA000004224466, Tag2, Outer Label 0x903, EXP 7, TTL 250, Inner Label 0x901, EXP 7, TTL 250; IP the same as original

    ./dpctl tcp:192.168.1.1:6633 flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=3,vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0x93000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.2.2/255.255.255.0 write:group=0x92000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0x93000001")
        apply_dpctl_mod(self, config, "flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.3.2/255.255.255.0 write:group=0x92000001 goto:60")

        input_pkt = simple_tcp_packet(pktlen=96,
                                       eth_dst='00:00:00:11:33:55',
                                       eth_src='00:00:00:11:22:33',
                                       ip_src='192.168.5.10',
                                       ip_dst='192.168.3.2',
                                       ip_ttl=64,
                                       vlan_vid=2,
                                       dl_vlan_enable=True)

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1f fa 45 00 00 4e 00 01 '
                '00 00 3f 06 f2 4c c0 a8 05 0a c0 a8 03 02 04 d2 '
                '00 50 00 00 00 00 00 00 00 00 50 02 20 00 f0 2c '
                '00 00 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class decap_2mpls_l3(base_tests.SimpleDataPlane):
    """
    [Decap two MPLS labels with L3]
      Decap two MPLS labels with L3 routing

    Inject  eth 1/1 SA000004223355, DA000004224466, Tag2, Outer Label 0x903, EXP 7, TTL 250, Inner Label 0x901, SIP 192.168.3.2, DIP 192.168.2.10
    Output  eth 1/3 SA000006223355, DA000006224466, Tag2, SIP 192.168.3.2, DIP 192.168.2.10

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20000003 group=any,port=any,weight=0 set_field=eth_src=00:00:06:22:33:55,set_field=eth_dst=00:00:06:22:44:66,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff apply:set_field=ofdpa_vrf:1 goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1,ofdpa_mpls_data_first_nibble=4 apply:mpls_dec,pop_mpls=0x0800,set_field=ofdpa_vrf:1 goto:30
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.2.2/255.255.255.0,ofdpa_vrf=1 write:group=0x20000003 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x20000003 group=any,port=any,weight=0 set_field=eth_src=00:00:06:22:33:55,set_field=eth_dst=00:00:06:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff apply:set_field=ofdpa_vrf:1 goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:23")
        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1,ofdpa_mpls_data_first_nibble=4 apply:mpls_dec,pop_mpls=0x0800,set_field=ofdpa_vrf:1 goto:30")
        apply_dpctl_mod(self, config, "flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.3.2/255.255.255.0,ofdpa_vrf=1 write:group=0x20000003 goto:60")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1f fa 45 00 00 4e 00 01 '
                '00 00 3f 06 f2 4c c0 a8 05 0a c0 a8 03 02 04 d2 '
                '00 50 00 00 00 00 00 00 00 00 50 02 20 00 f0 2c '
                '00 00 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44')
        output_pkt = simple_packet(
                '00 00 06 22 44 66 00 00 06 22 33 55 81 00 00 02 '
                '08 00 45 00 00 4e 00 01 00 00 f9 06 38 4c c0 a8 '
                '05 0a c0 a8 03 02 04 d2 00 50 00 00 00 00 00 00 '
                '00 00 50 02 20 00 f0 2c 00 00 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class encap_3mpls_l3(base_tests.SimpleDataPlane):
    """
    [Encap 3 MPLS labels with L3]
      Encap 3 MPLS labels with L3 routing

    Inject  eth 1/3 Tag 2, SA000000112233, DA000000113355, SIP 192.168.1.10, DIP 192.168.2.2
    Output  eth 1/1 SA000004223355, DA000004224466, Tag2, OuterLabel 0x904 EXP 7, TTL 250, M 0x903, Inner0x901, EXP 7, TTL 250; IP the same as original

    ./dpctl tcp:192.168.1.1:6633 flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=3,vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x94000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x904,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x94000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0x93000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.2.2/255.255.255.0 write:group=0x92000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x94000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x904,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x94000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0x93000001")
        apply_dpctl_mod(self, config, "flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.3.2/255.255.255.0 write:group=0x92000001 goto:60")

        input_pkt = simple_tcp_packet(pktlen=96,
                                       eth_dst='00:00:00:11:33:55',
                                       eth_src='00:00:00:11:22:33',
                                       ip_src='192.168.5.10',
                                       ip_dst='192.168.3.2',
                                       ip_ttl=64,
                                       vlan_vid=2,
                                       dl_vlan_enable=True)

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 4e fa 00 90 3e fa 00 90 1f fa 45 00 '
                '00 4e 00 01 00 00 3f 06 f2 4c c0 a8 05 0a c0 a8 '
                '03 02 04 d2 00 50 00 00 00 00 00 00 00 00 50 02 '
                '20 00 f0 2c 00 00 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)



class encap_2mpls_l3v6(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels with L3]
      Encap two MPLS labels with L3 routing

    Inject  eth 1/3 Tag 2, SA000000112233, DA000000113355, SIP 2014::1, DIP 2014::03
    Output  eth 1/1 SA000004223355, DA000004224466, Tag2, Outer Label 0x903, EXP 7, TTL 250, Inner Label 0x901, EXP 7, TTL 250; IP the same as original

    ./dpctl tcp:192.168.1.1:6633 flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=3,vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x86dd goto:30
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0x93000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=30,cmd=add,prio=301 eth_type=0x86dd,ipv6_dst=2014::3/64 write:group=0x92000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x86dd goto:30")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0x93000001")
        apply_dpctl_mod(self, config, "flow-mod table=30,cmd=add,prio=301 eth_type=0x86dd,ipv6_dst=2014::3/64 write:group=0x92000001 goto:60")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 02 '
                '86 dd 60 00 00 00 00 08 11 7f 20 14 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 02 20 14 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 01 00 0d 00 07 00 08 '
                'bf 9f 00 00 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1f fa 60 00 00 00 00 08 '
                '11 7e 20 14 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 02 20 14 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 01 00 0d 00 07 00 08 bf 9f 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class decap_2mpls_l3v6(base_tests.SimpleDataPlane):
    """
    [Decap two MPLS labels with L3]
      Decap two MPLS labels with L3 routing

    Inject  eth 1/1 SA000000000033, DA000000113355, Tag2, Outer Label 0x903, EXP 7, TTL 250, Inner Label 0x901, SIP 2014::1, DIP 2014::03
    Output  eth 1/3 SA000006223355, DA000006224466, Tag2, SIP 2014::1, DIP 2014::03

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20000003 group=any,port=any,weight=0 set_field=eth_src=00:00:06:22:33:55,set_field=eth_dst=00:00:06:22:44:66,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff apply:set_field=ofdpa_vrf:1 goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:24
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1,ofdpa_mpls_data_first_nibble=4 apply:mpls_dec,pop_mpls=0x0800,set_field=ofdpa_vrf:1 goto:30
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=30,cmd=add,prio=301 eth_type=0x86dd,ipv6_dst=2014::3/64,ofdpa_vrf=1 write:group=0x20000003 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x20000003 group=any,port=any,weight=0 set_field=eth_src=00:00:06:22:33:55,set_field=eth_dst=00:00:06:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff apply:set_field=ofdpa_vrf:1 goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x8847 goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1,ofdpa_mpls_data_first_nibble=4 apply:mpls_dec,pop_mpls=0x0800,set_field=ofdpa_vrf:1 goto:30")
        apply_dpctl_mod(self, config, "flow-mod table=30,cmd=add,prio=301 eth_type=0x86dd,ipv6_dst=2014::3/64,ofdpa_vrf=1 write:group=0x20000003 goto:60")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 00 00 33 81 00 00 02 '
                '88 47 00 90 30 40 00 90 11 40 60 00 00 00 00 2c '
                '3a 40 20 14 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 01 20 14 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 03 80 00 a6 ca 00 01 00 01 31 32 33 34 35 36 '
                '37 38 39 30 61 62 63 64 65 66 67 68 69 6a 6b 6c '
                '6d 6e 6f 70 71 72 73 74 75 76 77 78 79 7a ')
        output_pkt = simple_packet(
                '00 00 06 22 44 66 00 00 06 22 33 55 81 00 00 02 '
                '86 dd 60 00 00 00 00 2c 3a 3f 20 14 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 01 20 14 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 03 80 00 a6 ca 00 01 '
                '00 01 31 32 33 34 35 36 37 38 39 30 61 62 63 64 '
                '65 66 67 68 69 6a 6b 6c 6d 6e 6f 70 71 72 73 74 '
                '75 76 77 78 79 7a')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class encap_2mpls_l3_mp2mp(base_tests.SimpleDataPlane):
    """
    add MPLS 2 labels:
    Table 0 -> table 10 -> table 20 -> table 30 -> MPLS L3 VPN group -> MPLS FF group -> MPLS tunnel label 1 group -> MPLS intf group -> L2 intf group
    NOT add MPLS 2 labels:
    Table 0 -> table 10 -> table 60 -> L2 intf group

    ./dpctl tcp:192.168.1.1:6633 flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:57,set_field=eth_dst=00:00:04:22:44:67,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 set_field=mpls_label:0x907,push_mpls=0x8847,group=0x90000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=2,weight=0 group=0x93000001 group=any,port=3,weight=0 group=0x93000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0xA6000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.2.2/255.255.255.0 write:group=0x92000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=60,cmd=add,prio=601 eth_dst=00:00:00:11:33:56 write:group=0x20001
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:57,set_field=eth_dst=00:00:04:22:44:67,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 set_field=mpls_label:0x907,push_mpls=0x8847,group=0x90000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port)+",weight=0 group=0x93000001 group=any,port="+str(output_port2)+",weight=0 group=0x93000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0xA6000001")
        apply_dpctl_mod(self, config, "flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.3.2/255.255.255.0 write:group=0x92000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=60,cmd=add,prio=601 eth_dst=00:00:00:11:33:56 write:group=0x2000"+str(output_port))

        input_pkt = simple_tcp_packet(pktlen=96,
                                       eth_dst='00:00:00:11:33:56',
                                       eth_src='00:00:00:11:22:33',
                                       ip_src='192.168.5.10',
                                       ip_dst='192.168.3.2',
                                       ip_ttl=64,
                                       vlan_vid=2,
                                       dl_vlan_enable=True)

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(input_pkt), output_port)

        input_pkt = simple_tcp_packet(pktlen=96,
                                       eth_dst='00:00:00:11:33:55',
                                       eth_src='00:00:00:11:22:33',
                                       ip_src='192.168.5.10',
                                       ip_dst='192.168.3.2',
                                       ip_ttl=64,
                                       vlan_vid=2,
                                       dl_vlan_enable=True)

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1f fa 45 00 00 4e 00 01 '
                '00 00 3f 06 f2 4c c0 a8 05 0a c0 a8 03 02 04 d2 '
                '00 50 00 00 00 00 00 00 00 00 50 02 20 00 f0 2c '
                '00 00 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x1,mask=0x1")
        time.sleep(5)
        #send the same packet when working port down
        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1
        #check if output_port2 receives packet
        output_pkt2 = simple_packet(
                '00 00 04 22 44 67 00 00 04 22 33 57 81 00 00 02 '
                '88 47 00 90 7e fa 00 90 1f fa 45 00 00 4e 00 01 '
                '00 00 3f 06 f2 4c c0 a8 05 0a c0 a8 03 02 04 d2 '
                '00 50 00 00 00 00 00 00 00 00 50 02 20 00 f0 2c '
                '00 00 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44')
        verify_packet(self, str(output_pkt2), output_port2)


class encap_2mpls_l3_mp2mp_vrf(base_tests.SimpleDataPlane):
    """
    add MPLS 2 labels:
    Table 0 -> table 10 -> table 20 -> table 30 -> MPLS L3 VPN group -> MPLS FF group -> MPLS tunnel label 1 group -> MPLS intf group -> L2 intf group
    NOT add MPLS 2 labels:
    Table 0 -> table 10 -> table 60 -> L2 intf group

    ./dpctl tcp:192.168.1.1:6633 flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff apply:set_field=ofdpa_vrf:1 goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:57,set_field=eth_dst=00:00:04:22:44:67,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 set_field=mpls_label:0x907,push_mpls=0x8847,group=0x90000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=2,weight=0 group=0x93000001 group=any,port=3,weight=0 group=0x93000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0xA6000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.2.2/255.255.255.0,ofdpa_vrf=1 write:group=0x92000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=60,cmd=add,prio=601 eth_dst=00:00:00:11:33:56 write:group=0x20001
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff apply:set_field=ofdpa_vrf:1 goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:57,set_field=eth_dst=00:00:04:22:44:67,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 set_field=mpls_label:0x907,push_mpls=0x8847,group=0x90000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port)+",weight=0 group=0x93000001 group=any,port="+str(output_port2)+",weight=0 group=0x93000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0xA6000001")
        apply_dpctl_mod(self, config, "flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.3.2/255.255.255.0,ofdpa_vrf=1 write:group=0x92000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=60,cmd=add,prio=601 eth_dst=00:00:00:11:33:56 write:group=0x2000"+str(output_port))

        input_pkt = simple_tcp_packet(pktlen=96,
                                       eth_dst='00:00:00:11:33:56',
                                       eth_src='00:00:00:11:22:33',
                                       ip_src='192.168.5.10',
                                       ip_dst='192.168.3.2',
                                       ip_ttl=64,
                                       vlan_vid=2,
                                       dl_vlan_enable=True)

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(input_pkt), output_port)

        input_pkt = simple_tcp_packet(pktlen=96,
                                       eth_dst='00:00:00:11:33:55',
                                       eth_src='00:00:00:11:22:33',
                                       ip_src='192.168.5.10',
                                       ip_dst='192.168.3.2',
                                       ip_ttl=64,
                                       vlan_vid=2,
                                       dl_vlan_enable=True)

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1f fa 45 00 00 4e 00 01 '
                '00 00 3f 06 f2 4c c0 a8 05 0a c0 a8 03 02 04 d2 '
                '00 50 00 00 00 00 00 00 00 00 50 02 20 00 f0 2c '
                '00 00 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x1,mask=0x1")
        time.sleep(5)
        #send the same packet when working port down
        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1
        #check if output_port2 receives packet
        output_pkt2 = simple_packet(
                '00 00 04 22 44 67 00 00 04 22 33 57 81 00 00 02 '
                '88 47 00 90 7e fa 00 90 1f fa 45 00 00 4e 00 01 '
                '00 00 3f 06 f2 4c c0 a8 05 0a c0 a8 03 02 04 d2 '
                '00 50 00 00 00 00 00 00 00 00 50 02 20 00 f0 2c '
                '00 00 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44')
        verify_packet(self, str(output_pkt2), output_port2)


class encap_2mpls_l3_mp2mp_vrf_diff(base_tests.SimpleDataPlane):
    """
    add MPLS 2 labels:
    Table 0 -> table 10 -> table 20 -> table 30 -> MPLS L3 VPN group -> MPLS FF group -> MPLS tunnel label 1 group -> MPLS intf group -> L2 intf group
    NOT add MPLS 2 labels:
    Table 0 -> table 10 -> table 60 -> L2 intf group

    ./dpctl tcp:192.168.1.1:6633 flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff apply:set_field=ofdpa_vrf:1 goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:57,set_field=eth_dst=00:00:04:22:44:67,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 set_field=mpls_label:0x907,push_mpls=0x8847,group=0x90000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=2,weight=0 group=0x93000001 group=any,port=3,weight=0 group=0x93000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0xA6000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.2.2/255.255.255.0,ofdpa_vrf=2 write:group=0x92000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=60,cmd=add,prio=601 eth_dst=00:00:00:11:33:56 write:group=0x20001
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "flow-mod table=0,cmd=add,prio=1 in_port=0/0xffff0000 goto:10")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff apply:set_field=ofdpa_vrf:1 goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:00:11:33:55,eth_type=0x0800 goto:30")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:57,set_field=eth_dst=00:00:04:22:44:67,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 set_field=mpls_label:0x907,push_mpls=0x8847,group=0x90000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port)+",weight=0 group=0x93000001 group=any,port="+str(output_port2)+",weight=0 group=0x93000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x92000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ttl_out,group=0xA6000001")
        apply_dpctl_mod(self, config, "flow-mod table=30,cmd=add,prio=301 eth_type=0x0800,ip_dst=192.168.3.2/255.255.255.0,ofdpa_vrf=2 write:group=0x92000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=60,cmd=add,prio=601 eth_dst=00:00:00:11:33:56 write:group=0x2000"+str(output_port))

        input_pkt = simple_tcp_packet(pktlen=96,
                                       eth_dst='00:00:00:11:33:56',
                                       eth_src='00:00:00:11:22:33',
                                       ip_src='192.168.5.10',
                                       ip_dst='192.168.3.2',
                                       ip_ttl=64,
                                       vlan_vid=2,
                                       dl_vlan_enable=True)

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(input_pkt), output_port)

        input_pkt = simple_tcp_packet(pktlen=96,
                                       eth_dst='00:00:00:11:33:55',
                                       eth_src='00:00:00:11:22:33',
                                       ip_src='192.168.5.10',
                                       ip_dst='192.168.3.2',
                                       ip_ttl=64,
                                       vlan_vid=2,
                                       dl_vlan_enable=True)

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1f fa 45 00 00 4e 00 01 '
                '00 00 3f 06 f2 4c c0 a8 05 0a c0 a8 03 02 04 d2 '
                '00 50 00 00 00 00 00 00 00 00 50 02 20 00 f0 2c '
                '00 00 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 44 '
                '44 44 44 44 44 44 44 44')

        self.dataplane.send(input_port, str(input_pkt))
        verify_no_packet(self, str(output_pkt), output_port)


class encap_2mpls_wind(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels]
      Encap two MPLS labels

    Inject  eth 1/3 Tag 3, SA000000112233, DA000000113355
    Output  eth 1/1 Tag 2, Outer label 0x903, TTL 250, InLabel 0x901, TTL 250, SA000004223355, DA000004224466

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000001
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=2,weight=0 group=0x93000001 group=any,port=3,weight=0 group=0x93000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x2000"+str(output_port)+" goto:60")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x903,group=0x90000001")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:57,set_field=eth_dst=00:00:04:22:44:67,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 set_field=mpls_label:0x907,push_mpls=0x8847,group=0x90000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port)+",weight=0 group=0x93000001 group=any,port="+str(output_port2)+",weight=0 group=0x93000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001")

        apply_dpctl_mod(self, config, "flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 66 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x1,mask=0x1")
        time.sleep(5)
        #send the same packet when working port down
        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1
        #check if output_port2 receives packet
        output_pkt2 = simple_packet(
                '00 00 04 22 44 67 00 00 04 22 33 57 81 00 00 02 '
                '88 47 00 90 7e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')
        verify_packet(self, str(output_pkt2), output_port2)


class decap_2mpls_wind(base_tests.SimpleDataPlane):
    """
    [Pop, decap, and L2 forward]
      Pop outermost tunnel label and pop outer L2 header (L2 Switch VPWS )

    Inject  eth 1/1 Tag 2, Outer label 0x903, InLabel 0x901, SA000004223355, DA000004224466; InTag 5, InSA000000112233, InDA000000113355
    Output  eth 1/3 Tag 5, SA000000112233, DA000000113355

    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x20001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x20001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001
    ./dpctl tcp:192.168.1.1:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000001
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=20,cmd=add,prio=201 in_port=1,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x00008847 goto:24
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24
    ./dpctl tcp:192.168.1.1:6633 flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x20001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(input_port)+" group=any,port=any,weight=0 output="+str(input_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:66,set_field=vlan_vid=2,group=0x2000"+str(input_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 set_field=mpls_label:0x903,push_mpls=0x8847,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000001")
        apply_dpctl_mod(self, config, "flow-mod table=13,cmd=add,prio=113 tunn_id=0x10001,ofdpa_mpls_l2_port=100 write:group=0x91000001 goto:60")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(output_port)+",vlan_vid=0x1002/0x1fff apply:set_field=ofdpa_mpls_l2_port:100,set_field=tunn_id:0x10001 goto:13")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(input_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x00008847 goto:23")
        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x903 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=24,cmd=add,prio=204 eth_type=0x8847,mpls_label=0x901,mpls_bos=1 apply:pop_mpls=0x8847,mpls_dec,ofdpa_pop_l2hdr,ofdpa_pop_cw,set_field=ofdpa_mpls_l2_port:0x20100,set_field=tunn_id:0x10001 write:group=0x2000"+str(input_port)+" goto:60")

        input_pkt = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 66 81 00 00 02 '
                '88 47 00 90 3e fa 00 90 1b ff 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 05 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 02 01 '
                'c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 0a 0b '
                '0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        output_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 05 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b1 aa c0 a8 '
                '02 01 c0 a8 02 02 00 01 02 03 04 05 06 07 08 09 '
                '0a 0b 0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)




##################################################
# MPLS VPLS
##################################################

class encap_2mpls_vpls_p2p_ff(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels: customer to FF provider]

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000003 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000003 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000003

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=2,weight=0 group=0x93000002 group=any,port=3,weight=0 group=0x93000003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60

    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000003 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000003 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000003")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port)+",weight=0 group=0x93000002 group=any,port="+str(output_port2)+",weight=0 group=0x93000003")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt2 = simple_packet(
                '00 00 04 22 44 65 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 93 5e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x1,mask=0x1")
        time.sleep(5)

        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1

        #check if output_port2 receives packet
        verify_packet(self, str(output_pkt2), output_port2)


class decap_2mpls_vpls_p2p(base_tests.SimpleDataPlane):
    """
    [Decap two MPLS labels: provider to customer]

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000003 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000003 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000003

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=2,weight=0 group=0x93000002 group=any,port=3,weight=0 group=0x93000003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=2,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=3,vlan_vid=0x1002/0x1fff goto:20

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=20,cmd=add,prio=201 in_port=2,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:51,eth_type=0x8847 goto:23
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=20,cmd=add,prio=201 in_port=3,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:23

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x931 apply:pop_mpls=0x8847,mpls_dec goto:24
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x935 apply:pop_mpls=0x8847,mpls_dec goto:24

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x30001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9D000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001,group=0x30001
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:22:33 write:group=0x9D000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000003 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000003 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000003")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port)+",weight=0 group=0x93000002 group=any,port="+str(output_port2)+",weight=0 group=0x93000003")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(output_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(output_port2)+",vlan_vid=0x1002/0x1fff goto:20")

        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(output_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:51,eth_type=0x8847 goto:23")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(output_port2)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:23")

        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x931 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x935 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x3000"+str(input_port)+" group=any,port=any,weight=0 output="+str(input_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9D000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001,group=0x3000"+str(input_port))
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:22:33 write:group=0x9D000001 goto:60")

        input_pkt = simple_packet(
                '00 00 00 11 22 33 00 00 00 11 33 55 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 33 51 00 00 04 22 44 61 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 22 33 00 00 00 11 33 55 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt2 = simple_packet(
                '00 00 04 22 33 55 00 00 04 22 44 65 81 00 00 02 '
                '88 47 00 93 5e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 22 33 00 00 00 11 33 55 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(output_port, str(output_pkt))
        verify_packet(self, str(input_pkt), input_port)
        print 'send 1st done'
        self.dataplane.send(output_port2, str(output_pkt2))
        verify_packet(self, str(input_pkt), input_port)


class encap_2mpls_vpls_p2p_normal(base_tests.SimpleDataPlane):
    """
    [customer to customer]
    NOT care output vlan with input

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9D000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10002,set_field=tunn_id:0x20001,group=0x20002

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9D000001 goto:60

    #duplicate customer setting
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=2,vlan_vid=0x1002/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10002,set_field=tunn_id:0x20001 goto:50
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=del,prio=101 in_port=2,vlan_vid=0x1002/0x1fff

    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9D000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10002,set_field=tunn_id:0x20001,group=0x2000"+str(output_port))

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9D000001 goto:60")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(input_pkt), output_port)


class encap_2mpls_vpls_p2m_same(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels: customer to multiple provider with same output]

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000001
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000001

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000002 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000002 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30002,set_field=tunn_id:0x20001,group=0x91000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=all,group=0x9f000001 group=any,port=any,weight=0 group=0x9C000001 group=any,port=any,weight=0 group=0x9C000002

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=01:00:5e:11:33:55 write:group=0x9f000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000001 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000001 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000001")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000002 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000002 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30002,set_field=tunn_id:0x20001,group=0x91000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=all,group=0x9f000001 group=any,port=any,weight=0 group=0x9C000001 group=any,port=any,weight=0 group=0x9C000002")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=01:00:5e:11:33:55 write:group=0x9f000001 goto:60")

        input_pkt = simple_packet(
                '01 00 5e 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 01 00 '
                '5e 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)
        verify_packet(self, str(output_pkt), output_port2)


class encap_2mpls_vpls_p2m_diff(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels: customer to multiple provider with different mpls]

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000002 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000003 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000003 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000003 group=any,port=any,weight=0 set_field=mpls_label:0x903,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000003

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000002 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30002,set_field=tunn_id:0x20001,group=0x91000003

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=all,group=0x9f000001 group=any,port=any,weight=0 group=0x9C000001 group=any,port=any,weight=0 group=0x9C000002

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=01:00:5e:11:33:55 write:group=0x9f000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000002 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000003 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000003 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000003")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000003 group=any,port=any,weight=0 set_field=mpls_label:0x903,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000003")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000002 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30002,set_field=tunn_id:0x20001,group=0x91000003")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=all,group=0x9f000001 group=any,port=any,weight=0 group=0x9C000001 group=any,port=any,weight=0 group=0x9C000002")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=01:00:5e:11:33:55 write:group=0x9f000001 goto:60")

        input_pkt = simple_packet(
                '01 00 5e 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 01 00 '
                '5e 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt2 = simple_packet(
                '00 00 04 22 44 65 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 93 5e fa 00 90 3f fa 00 00 00 00 01 00 '
                '5e 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)
        verify_packet(self, str(output_pkt2), output_port2)


class encap_2mpls_vpls_p2m_cp(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels: customer to provider and customer]

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000002 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9D000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10002,set_field=tunn_id:0x20001,group=0x20003

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=all,group=0x9f000001 group=any,port=any,weight=0 group=0x9C000001 group=any,port=any,weight=0 group=0x9D000001

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=01:00:5e:11:33:55 write:group=0x9f000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000002 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9D000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10002,set_field=tunn_id:0x20001,group=0x2000"+str(output_port2))

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=all,group=0x9f000001 group=any,port=any,weight=0 group=0x9C000001 group=any,port=any,weight=0 group=0x9D000001")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=01:00:5e:11:33:55 write:group=0x9f000001 goto:60")

        input_pkt = simple_packet(
                '01 00 5e 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 01 00 '
                '5e 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)
        verify_packet(self, str(input_pkt), output_port2)


class encap_2mpls_vpls_p2m_dlf(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels: customer to provider and customer]

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000002 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9D000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10002,set_field=tunn_id:0x20001,group=0x20003

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=all,group=0x9E020001 group=any,port=any,weight=0 group=0x9C000001 group=any,port=any,weight=0 group=0x9D000001

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001 write:group=0x9E020001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000002 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9D000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10002,set_field=tunn_id:0x20001,group=0x2000"+str(output_port2))

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=all,group=0x9E020001 group=any,port=any,weight=0 group=0x9C000001 group=any,port=any,weight=0 group=0x9D000001")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001 write:group=0x9E020001 goto:60")

        input_pkt = simple_packet(
                '01 00 5e 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 01 00 '
                '5e 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)
        verify_packet(self, str(input_pkt), output_port2)

        input_pkt = simple_packet(
                '00 00 00 11 22 33 00 00 00 11 33 55 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 22 33 00 00 00 11 33 55 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)
        verify_packet(self, str(input_pkt), output_port2)


class encap_decap_2mpls_vpls_p2m_dlf(base_tests.SimpleDataPlane):
    """
    input_port: customer port1
    output_port: provider port
    output_port2: customer port2

    encap:
        customer port1 -> provider port [encap 2 mpls]
                       -> customer port2 [normal forward]
    decap:
        provider port -> customer port1
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000002 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x93000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9D000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10002,set_field=tunn_id:0x20001,group=0x2000"+str(output_port2))

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x3000"+str(input_port)+" group=any,port=any,weight=0 output="+str(input_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9D000002 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001,group=0x3000"+str(input_port))

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=all,group=0x9E020001 group=any,port=any,weight=0 group=0x9C000001 group=any,port=any,weight=0 group=0x9D000001 group=any,port=any,weight=0 group=0x9D000002")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001 write:group=0x9E020001 goto:60")

        input_pkt = simple_packet(
                '01 00 5e 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 01 00 '
                '5e 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)
        verify_packet(self, str(input_pkt), output_port2)

        #decap
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(output_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(output_port2)+",vlan_vid=0x1002/0x1fff goto:20")

        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(output_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:51,eth_type=0x8847 goto:23")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(output_port2)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:55,eth_type=0x8847 goto:23")

        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x931 apply:pop_mpls=0x8847,mpls_dec goto:24")
        apply_dpctl_mod(self, config, "flow-mod table=23,cmd=add,prio=203 eth_type=0x8847,mpls_label=0x935 apply:pop_mpls=0x8847,mpls_dec goto:24")
        #apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x3000"+str(input_port)+" group=any,port=any,weight=0 output="+str(input_port))
        #apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9D000002 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001,group=0x3000"+str(input_port))
        #apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:22:33 write:group=0x9D000001 goto:60")

        input_pkt = simple_packet(
                '00 00 04 22 33 51 00 00 04 22 44 61 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 22 33 00 00 00 11 33 55 81 00 00 03 08 00 '
                '45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 00 11 22 33 00 00 00 11 33 55 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(output_port, str(input_pkt))
        verify_packet(self, str(output_pkt), input_port)


class encap_2mpls_vpls_p2p_ff_pop_outer_vlan(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels: customer to FF provider]

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000003 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000003 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000003

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=2,weight=0 group=0x93000002 group=any,port=3,weight=0 group=0x93000003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1006/0x1fff apply:pop_vlan,set_field=ofdpa_ovid:6 goto:11
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=11,cmd=add,prio=111 in_port=1,vlan_vid=0x1003/0x1fff,ofdpa_ovid=0x1006 apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000003 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000003 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000003")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port)+",weight=0 group=0x93000002 group=any,port="+str(output_port2)+",weight=0 group=0x93000003")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1006/0x1fff apply:pop_vlan,set_field=ofdpa_ovid:6 goto:11")
        apply_dpctl_mod(self, config, "flow-mod table=11,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff,ofdpa_ovid=0x1006 apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 06 '
                '81 00 00 03 08 00 45 00 00 2a 04 d2 00 00 7f 00 '
                'b2 4b c0 a8 01 64 c0 a8 02 02 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2a 04 d2 00 00 7f 00 b2 4b c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt2 = simple_packet(
                '00 00 04 22 44 65 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 93 5e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 03 08 00 '
                '45 00 00 2a 04 d2 00 00 7f 00 b2 4b c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x1,mask=0x1")
        time.sleep(5)

        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1

        #check if output_port2 receives packet
        verify_packet(self, str(output_pkt2), output_port2)


class encap_2mpls_vpls_p2p_ff_pop_outer_vlan_change_inner(base_tests.SimpleDataPlane):
    """
    [Encap two MPLS labels: customer to FF provider]

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20003 group=any,port=any,weight=0 output=3
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000003 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x20003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x93000003 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000003

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ff,group=0xA6000001 group=any,port=2,weight=0 group=0x93000002 group=any,port=3,weight=0 group=0x93000003
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1006/0x1fff apply:pop_vlan,set_field=ofdpa_ovid:6 goto:11
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=11,cmd=add,prio=111 in_port=1,vlan_vid=0x1003/0x1fff,ofdpa_ovid=0x1006 apply:pop_vlan,push_vlan=0x8100,set_field=vlan_vid=4,set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000002 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x931,group=0x90000002")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port2)+" group=any,port=any,weight=0 output="+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000003 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:55,set_field=eth_dst=00:00:04:22:44:65,set_field=vlan_vid=2,group=0x2000"+str(output_port2))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x93000003 group=any,port=any,weight=0 push_mpls=0x8847,set_field=mpls_label:0x935,group=0x90000003")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ff,group=0xA6000001 group=any,port="+str(output_port)+",weight=0 group=0x93000002 group=any,port="+str(output_port2)+",weight=0 group=0x93000003")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0xA6000001")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1006/0x1fff apply:pop_vlan,set_field=ofdpa_ovid:6 goto:11")
        apply_dpctl_mod(self, config, "flow-mod table=11,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff,ofdpa_ovid=0x1006 apply:pop_vlan,push_vlan=0x8100,set_field=vlan_vid=4,set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 06 '
                '81 00 00 03 08 00 45 00 00 2a 04 d2 00 00 7f 00 '
                'b2 4b c0 a8 01 64 c0 a8 02 02 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 93 1e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 04 08 00 '
                '45 00 00 2a 04 d2 00 00 7f 00 b2 4b c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt2 = simple_packet(
                '00 00 04 22 44 65 00 00 04 22 33 55 81 00 00 02 '
                '88 47 00 93 5e fa 00 90 1f fa 00 00 00 00 00 00 '
                '00 11 33 55 00 00 00 11 22 33 81 00 00 04 08 00 '
                '45 00 00 2a 04 d2 00 00 7f 00 b2 4b c0 a8 01 64 '
                'c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)

        #if output_port link down
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x1,mask=0x1")
        time.sleep(5)

        self.dataplane.send(input_port, str(input_pkt))

        #recover output_port link status, before assert check
        apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
        time.sleep(1)
        #make sure port link up
        port_up = 0
        while port_up == 0:
            time.sleep(1)
            #apply_dpctl_mod(self, config, "port-mod port="+str(output_port)+",conf=0x0,mask=0x1")
            json_result = apply_dpctl_get_cmd(self, config, "port-desc")
            result=json_result["RECEIVED"][1]
            for p_desc in result["port"]:
                if p_desc["no"] == output_port:
                    if p_desc["config"] != 0x01 : #up
                        port_up = 1

        #check if output_port2 receives packet
        verify_packet(self, str(output_pkt2), output_port2)










##################################################
# MPLS VPLS out of range extra test
##################################################
class ext_encap_1mpls_vpls(base_tests.SimpleDataPlane):
    """
    [Encap 1 MPLS label: customer to provider]

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60")

        input_pkt = simple_packet(
                '00 00 00 11 33 55 00 00 00 11 22 33 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 04 22 44 61 00 00 04 22 33 51 81 00 00 02 '
                '88 47 00 90 1f fa 00 00 00 00 00 00 00 11 33 55 '
                '00 00 00 11 22 33 81 00 00 03 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b2 47 c0 a8 01 64 c0 a8 02 02 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(input_port, str(input_pkt))
        verify_packet(self, str(output_pkt), output_port)


class ext_decap_1mpls_vpls(base_tests.SimpleDataPlane):
    """
    [Decap 1 MPLS label: provider to customer]

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x20002 group=any,port=any,weight=0 output=2
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x20002
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000002

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=1,vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60

    ./dpctl tcp:0.0.0.0:6633 flow-mod table=10,cmd=add,prio=101 in_port=2,vlan_vid=0x1002/0x1fff goto:20
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=20,cmd=add,prio=201 in_port=2,vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:51,eth_type=0x8847 goto:23

    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x30001 group=any,port=any,weight=0 output=1
    ./dpctl tcp:0.0.0.0:6633 group-mod cmd=add,type=ind,group=0x9D000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001,group=0x30001
    ./dpctl tcp:0.0.0.0:6633 flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:22:33 write:group=0x9D000001 goto:60
    """
    def runTest(self):
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        test_ports = sorted(config["port_map"].keys())

        input_port = test_ports[0]
        output_port = test_ports[1]
        output_port2 = test_ports[2]

        apply_dpctl_mod(self, config, "meter-mod cmd=del,meter=0xffffffff")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x2000"+str(output_port)+" group=any,port=any,weight=0 output="+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x90000002 group=any,port=any,weight=0 set_field=eth_src=00:00:04:22:33:51,set_field=eth_dst=00:00:04:22:44:61,set_field=vlan_vid=2,group=0x2000"+str(output_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x91000001 group=any,port=any,weight=0 set_field=mpls_label:0x901,set_field=mpls_tc:7,set_field=ofdpa_mpls_ttl:250,ofdpa_push_l2hdr,push_vlan=0x8100,push_mpls=0x8847,ofdpa_push_cw,group=0x90000002")
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9C000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x30001,set_field=tunn_id:0x20001,group=0x91000001")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(input_port)+",vlan_vid=0x1003/0x1fff apply:set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001 goto:50")
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:33:55 write:group=0x9C000001 goto:60")

        apply_dpctl_mod(self, config, "flow-mod table=10,cmd=add,prio=101 in_port="+str(output_port)+",vlan_vid=0x1002/0x1fff goto:20")
        apply_dpctl_mod(self, config, "flow-mod table=20,cmd=add,prio=201 in_port="+str(output_port)+",vlan_vid=2/0xfff,eth_dst=00:00:04:22:33:51,eth_type=0x8847 goto:23")

        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x3000"+str(input_port)+" group=any,port=any,weight=0 output="+str(input_port))
        apply_dpctl_mod(self, config, "group-mod cmd=add,type=ind,group=0x9D000001 group=any,port=any,weight=0 set_field=ofdpa_mpls_l2_port:0x10001,set_field=tunn_id:0x20001,group=0x3000"+str(input_port))
        apply_dpctl_mod(self, config, "flow-mod table=50,cmd=add,prio=501 tunn_id=0x20001,eth_dst=00:00:00:11:22:33 write:group=0x9D000001 goto:60")

        input_pkt = simple_packet(
                '00 00 04 22 33 51 00 00 04 22 44 61 81 00 00 02 '
                '88 47 00 90 1f fa 00 00 00 00 00 00 00 11 22 33 '
                '00 00 00 11 33 55 81 00 00 03 08 00 45 00 00 2e '
                '04 d2 00 00 7f 00 b2 47 c0 a8 01 64 c0 a8 02 02 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00')

        output_pkt = simple_packet(
                '00 00 00 11 22 33 00 00 00 11 33 55 81 00 00 03 '
                '08 00 45 00 00 2e 04 d2 00 00 7f 00 b2 47 c0 a8 '
                '01 64 c0 a8 02 02 00 00 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        self.dataplane.send(output_port, str(input_pkt))
        verify_packet(self, str(output_pkt), input_port)

#!/bin/bash
# this shell script is useful to change different test cases quickly

HOST_IP=124.219.108.5

# network interfaces
IF_NAME_1=ens16f0
IF_NAME_2=ens16f1
IF_NAME_3=ens17f0
IF_NAME_4=ens17f1

# test case category
TEST_SINGLE_CASE=test_tenants.Getter
TEST_EXCEPTION="test_exception_switch_reboot \
                test_exception_link_down_up \
                test_exception_disconnect_device \
                test_exception_restart_mars"

TEST_ALL_WITHOUT_EXCEPTION="test_account \
                            test_alert \
                            test_dhcp_relay \
                            test_healthy_check \
                            test_intents \
                            test_ntp_server \
                            test_qos \
                            test_storm_control \
                            test_span \
                            test_tenant_logical_router \
                            test_tenants"

TEST_ALL="test_account \
          test_alert \
          test_dhcp_relay \
          test_healthy_check \
          test_intents \
          test_ntp_server \
          test_qos \
          test_storm_control \
          test_span \
          test_tenant_logical_router \
          test_tenants \
          test_exception_switch_reboot \
          test_exception_link_down_up \
          test_exception_disconnect_device \
          test_exception_restart_mars"

# main
python oft --host=${HOST_IP} \
           -i 1@${IF_NAME_1} \
           -i 2@${IF_NAME_2} \
           -i 3@${IF_NAME_3} \
           -i 4@${IF_NAME_4} \
           --of-version=1.3 \
           --mars=MARS \
           --test-dir=mars \
           --disable-ipv6 \
           --debug=debug \
           ${TEST_ALL_WITHOUT_EXCEPTION}
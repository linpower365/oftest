"""
Config file for some constant value
"""

import base64
from oftest import config
import ConfigParser
import socket

API_BASE_URL = "http://" + config['controller_host'] + ":8181/mars/"

# admin username
ADMIN_USERNAME = 'karaf'
ADMIN_PASSWORD = 'karaf'

# admin login
LOGIN = base64.b64encode(bytes('{}:{}'.format(ADMIN_USERNAME, ADMIN_PASSWORD)))

# Read ini file
INI_FILE = "auto-test.ini"

if socket.gethostname() == 'AutoTestMars':
    INI_FILE = "auto-test.ini"
elif socket.gethostname() == 'Mars-charles':
    INI_FILE = "mars-charles.ini"

print 'Test Host: ' + socket.gethostname()
print 'Test INI : ' + INI_FILE

conf = ConfigParser.ConfigParser()
conf.read('./mars/ini/' + INI_FILE)

# devices under test
spine0 = {
    'id': conf.get('spine0', 'id'),
    'name': conf.get('spine0', 'name'),
    'type': conf.get('spine0', 'type'),
    'mgmtIpAddress': conf.get('spine0', 'mgmtIpAddress'),
    'mac': conf.get('spine0', 'mac'),
    'nos': conf.get('spine0', 'nos'),
}

spine1 = {
    'id': conf.get('spine1', 'id'),
    'name': conf.get('spine1', 'name'),
    'type': conf.get('spine1', 'type'),
    'mgmtIpAddress': conf.get('spine1', 'mgmtIpAddress'),
    'mac': conf.get('spine1', 'mac'),
    'nos': conf.get('spine1', 'nos'),
}

leaf0 = {
    'id': conf.get('leaf0', 'id'),
    'name': conf.get('leaf0', 'name'),
    'type': conf.get('leaf0', 'type'),
    'mgmtIpAddress': conf.get('leaf0', 'mgmtIpAddress'),
    'mac': conf.get('leaf0', 'mac'),
    'nos': conf.get('leaf0', 'nos'),
}

leaf1 = {
    'id': conf.get('leaf1', 'id'),
    'name': conf.get('leaf1', 'name'),
    'type': conf.get('leaf1', 'type'),
    'mgmtIpAddress': conf.get('leaf1', 'mgmtIpAddress'),
    'mac': conf.get('leaf1', 'mac'),
    'nos': conf.get('leaf1', 'nos'),
}

host0 = {
    'id': 'host0',
    'mac': '00:00:01:00:00:01',
    'ip': ''
}

host1 = {
    'id': 'host1',
    'mac': '00:00:01:00:00:02',
    'ip': ''
}

host2 = {
    'id': 'host2',
    'mac': '00:00:01:00:00:03',
    'ip': ''
}

host3 = {
    'id': 'host3',
    'mac': '00:00:01:00:00:04',
    'ip': ''
}

external_router0 = {
    'id': 'external_router0',
    'mac': '00:00:02:00:00:01',
    'ip': ''
}

external_router1 = {
    'id': 'external_router1',
    'mac': '00:00:02:00:00:02',
    'ip': ''
}

devices = [spine0, spine1, leaf0, leaf1]
spines = [spine0, spine1]
leaves = [leaf0, leaf1]
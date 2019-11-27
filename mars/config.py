"""
Config file for some constant value
"""

import base64
from oftest import config


API_BASE_URL = "http://" + config['controller_host'] + ":8181/mars/"

# admin username
ADMIN_USERNAME = 'karaf'
ADMIN_PASSWORD = 'karaf'

# admin login
LOGIN = base64.b64encode(bytes('{}:{}'.format(ADMIN_USERNAME, ADMIN_PASSWORD)))

# devices under test
spine0 = {
    'id': 'rest:192.168.40.147:80',
    'name': 'spine0',
    'type': 'spine',
    'mgmtIpAddress': '192.168.40.147',
    'mac': '8c:ea:1b:8d:0e:88',
}

spine1 = {
    'id': 'rest:192.168.40.148:80',
    'name': 'spine1',  
    'type': 'spine',
    'mgmtIpAddress': '192.168.40.148',
    'mac': '8c:ea:1b:8d:0e:d2',
}

leaf0 = {
    'id': 'rest:192.168.40.149:80',
    'name': 'leaf0',
    'type': 'leaf',
    'mgmtIpAddress': '192.168.40.149',
    'mac': '8c:ea:1b:8d:0e:3e',
}

leaf1 = {
    'id': 'rest:192.168.40.150:80',
    'name': 'leaf1',
    'type': 'leaf',
    'mgmtIpAddress': '192.168.40.150',
    'mac': '8c:ea:1b:9b:a4:30',
}

host0 = {
    'id': 'host0',
    'mac': '00:00:01:00:00:01'
}

host1 = {
    'id': 'host1',
    'mac': '00:00:01:00:00:02'
}

host2 = {
    'id': 'host2',
    'mac': '00:00:01:00:00:03'
}

devices = [spine0, spine1, leaf0, leaf1]
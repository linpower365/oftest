#!/usr/bin/python
#
# Parsing oftest xml file and generated report
#

import xunitparser
import requests
import base64
from datetime import datetime
from os import listdir
from os.path import isfile, join, exists
from distutils.dir_util import copy_tree, remove_tree

config = {}
config ['controller_host'] = '127.0.0.1'

# datetime object containing current date and time
now = datetime.now()

src_xml_dir = './xunit/'
dst_xml_dir = './xunit-{}/'.format(now.strftime("%Y-%m-%d"))
URL = "http://" + config['controller_host'] + ":8181/mars/"

# copy source files into new folder
if exists(dst_xml_dir):
    remove_tree(dst_xml_dir)
copy_tree(src_xml_dir, dst_xml_dir)

# admin username
ADMIN_USERNAME = 'karaf'
ADMIN_PASSWORD = 'karaf'

# admin login
LOGIN = base64.b64encode(bytes('{}:{}'.format(ADMIN_USERNAME, ADMIN_PASSWORD)))
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}

# log file name
log_file_name = now.strftime("%Y%m%d-%H%M%S")

# mars version
version = requests.get(URL+"utility/v1/version", headers=GET_HEADER)

# devices info
devices_info = requests.get(URL+"v1/devices", headers=GET_HEADER)

fp = open('test-report-{}.log'.format(log_file_name), "a")

# YY/mm/dd H:M:S
dt_string = now.strftime("%Y/%m/%d %H:%M:%S")

print >>fp, 'Report generated at {}'.format(dt_string)
print >>fp, ''
print >>fp, '<<< Mars Informantion >>>'
print >>fp, 'Git Commit           : {}'.format(version.json()['commit'])
print >>fp, 'Version              : {}'.format(version.json()['version'])
print >>fp, 'Build server         : {}'.format(version.json()['build_server'])
print >>fp, 'Build time           : {}'.format(version.json()['build_date'])
print >>fp, 'Logstash version     : {}'.format(version.json()['logstash'])
print >>fp, 'Elasticsearch version: {}'.format(version.json()['elasticsearch'])
print >>fp, 'Nginx version        : {}'.format(version.json()['nginx'])
print >>fp, ''

print >>fp, '<<< Devices Informantion >>>'
for i in range(4):
    print >>fp, 'ID: {}'.format(devices_info.json()['devices'][i]['id']),
    print >>fp, '  Serial: {}'.format(devices_info.json()['devices'][i]['serial']),
    print >>fp, '  NOS: {}'.format(devices_info.json()['devices'][i]['nos']),
    print >>fp, '  Software: {}'.format(devices_info.json()['devices'][i]['sw'])
print >>fp, ''

xml_files = [f for f in listdir(dst_xml_dir) if isfile(join(dst_xml_dir, f))]
xml_files.sort()

# print xml_files
print >>fp, '<<< Test Result >>>'

result = {'pass': 0, 'error': 0, 'failure': 0, 'check': 0}

for xml_file in xml_files:
    ts, tr = xunitparser.parse(open(dst_xml_dir + xml_file))

    if len(tr.errors) == 0 and len(tr.failures) == 0:
        test_result = 'PASS'
        result['pass'] = result['pass'] + 1
    elif len(tr.errors) != 0:
        test_result = 'ERROR'
        result['error'] = result['error'] + 1
    elif len(tr.failures) != 0:
        test_result = 'FAILURE'
        result['failure'] = result['failure'] + 1
    else:
        test_result = 'CHECK'
        result['pass'] = result['check'] + 1

    for tc in ts:
        print >>fp, '{:90} result: {:10} time: {}'.format(tc.classname, test_result, tc.time)

total = result['pass'] + result['error'] + result['failure'] + result['check']

print >>fp, ''
print >>fp, 'Status: Pass: {} Failure: {} Error: {} Check: {}'.format(result['pass'], result['failure'], result['error'] ,result['check'])
print >>fp, ''
print >>fp, 'Total: {}'.format(total)

fp.close()

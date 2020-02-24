#!/usr/bin/python
#
# Parsing oftest xml file and generated report
#

import xunitparser
import requests
import base64
from datetime import datetime
from os import listdir
from os.path import isfile, join

config = {}
config ['controller_host'] = '127.0.0.1'

xml_file_path = './xunit/'
URL = "http://" + config['controller_host'] + ":8181/mars/"

# admin username
ADMIN_USERNAME = 'karaf'
ADMIN_PASSWORD = 'karaf'

# admin login
LOGIN = base64.b64encode(bytes('{}:{}'.format(ADMIN_USERNAME, ADMIN_PASSWORD)))
AUTH_TOKEN = 'BASIC ' + LOGIN
GET_HEADER = {'Authorization': AUTH_TOKEN}

# datetime object containing current date and time
now = datetime.now()

# log file name
log_file_name = now.strftime("%Y%m%d-%H%M%S")

# mars version
response = requests.get(URL+"utility/v1/version", headers=GET_HEADER)

fp = open('test-report-{}.log'.format(log_file_name), "a")

# YY/mm/dd H:M:S
dt_string = now.strftime("%Y/%m/%d %H:%M:%S")

print >>fp, 'Report generated at {}'.format(dt_string)
print >>fp, ''
print >>fp, '<<< Mars Informantion >>>'
print >>fp, 'Git Commit           : {}'.format(response.json()['commit'])
print >>fp, 'Version              : {}'.format(response.json()['version'])
print >>fp, 'Build server         : {}'.format(response.json()['build_server'])
print >>fp, 'Build time           : {}'.format(response.json()['build_date'])
print >>fp, 'Logstash version     : {}'.format(response.json()['logstash'])
print >>fp, 'Elasticsearch version: {}'.format(response.json()['elasticsearch'])
print >>fp, 'Nginx version        : {}'.format(response.json()['nginx'])
print >>fp, ''

xml_files = [f for f in listdir(xml_file_path) if isfile(join(xml_file_path, f))]
xml_files.sort()

# print xml_files
print >>fp, '<<< Test Result >>>'

result = {'pass': 0, 'error': 0, 'failure': 0, 'check': 0}

for xml_file in xml_files:
    ts, tr = xunitparser.parse(open(xml_file_path + xml_file))

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

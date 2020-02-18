#!/usr/bin/python
#
# Parsing oftest xml file and generated report
#

import xunitparser
from datetime import datetime
from os import listdir
from os.path import isfile, join

xml_file_path = './xunit/'

# datetime object containing current date and time
now = datetime.now()

# log file name
log_file_name = now.strftime("%Y%m%d-%H%M%S")

fp = open('test-report-{}.log'.format(log_file_name), "a")

# YY/mm/dd H:M:S
dt_string = now.strftime("%Y/%m/%d %H:%M:%S")

print >>fp, 'Report generated at {}'.format(dt_string)
print >>fp, ''

xml_files = [f for f in listdir(xml_file_path) if isfile(join(xml_file_path, f))]
xml_files.sort()

# print xml_files

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
        print >>fp, 'Class {:60} time: {:20} result: {}'.format(tc.classname, tc.time, test_result) 

total = result['pass'] + result['error'] + result['failure'] + result['check']

print >>fp, ''
print >>fp, 'Status: Pass: {} Failure: {} Error: {} Check: {}'.format(result['pass'], result['failure'], result['error'] ,result['check'])
print >>fp, ''
print >>fp, 'Total: {}'.format(total)

fp.close()
#!/usr/bin/env python3

import argparse
import os
import requests
import json
import sys

# argparser
parser = argparse.ArgumentParser(description='phpipam Ansible Dynamic Inventory')
parser.add_argument('--list', action="store_true", default=False, dest="list", help='print dynamic inventory')
parser.add_argument('--host', dest="host")
parser.add_argument('--url', default=os.getenv('PHPIPAM_URL'), type=str, help='phpipam target host')
parser.add_argument('--username', default=os.getenv('PHPIPAM_USERNAME'), type=str, dest='username', help='phpipam username')
parser.add_argument('--password', default=os.getenv('PHPIPAM_PASSWORD'), type=str, dest='password', help='phpipam password')
parser.add_argument('--api-appid', default=os.getenv('PHPIPAM_API_APPID', "ansible"), type=str, dest='appid', help='phpipam api App id')
parser.add_argument('--sectionid', default="3", type=str, dest='sectionid', help='phpipam subnet section id')
parser.add_argument('--skip-tls-verify', default='true', action='store_true', dest='tlsVerify', help='Skip TLS certificate verification')
args = parser.parse_args()

if args.sectionid is None and 'PHPIPAM_SECTION_ID' in os.environ:
    args.sectionid = os.getenv('PHPIPAM_SECTION_APPID')
else:
  # sectionid = 1
  sectionid = args.sectionid
if args.tlsVerify is None and 'PHPIPAM_TLS_VERIFY' in os.environ:
    args.tlsVerify = os.getenv('PHPIPAM_TLS_VERIFY')
else:
  tlsVerify = args.tlsVerify

# defina variables
url = args.url
appid = args.appid
username = args.username
password = args.password

api_url = "%s/api/%s" % (url, appid)
inventory={'all': {'children': {}, "hosts": {}, 'vars': { 'netids': {} } }}
groupids=[]

# get ticket
print(api_url)
response1 = requests.post(api_url + '/user/', data={}, auth=(username, password))
if not response1.ok:
    raise AssertionError('Authentification Failed : \n {}'.format(response1.reason))
ticket = {'phpipam-token': response1.json()['data']['token']}

# get groups
response2 = requests.get(api_url + '/sections/' + str(sectionid) + '/subnets/', verify=tlsVerify, headers=ticket )
if not response2.ok:
    raise AssertionError('Group list Failed : \n {}'.format(response2.reason))
gjson = response2.json()['data']
for item in range(len(gjson)):
  if str(gjson[item]['description']) != "None":
        newkey1 = gjson[item]['id']
        newkey2 = gjson[item]['description']
        inventory['all']['children'][newkey2] = {}
        inventory['all']['children'][newkey2]['vars'] = {}
        inventory['all']['children'][newkey2]['vars']['id'] = newkey1
        inventory['all']['vars']['netids'][newkey1] = gjson[item]['description']
        groupids.append(gjson[item]['id'])

# get hosts
for tid in groupids:
  response3 = requests.get(api_url + '/subnets/' + tid +'/addresses/', verify=tlsVerify, headers=ticket )
  if not response3.ok:
    raise AssertionError('Host list Failed : \n {}'.format(response3.reason))
  hjson = response3.json()['data']
  for item in range(len(hjson)):
    if str(hjson[item]['hostname']) != "None":
      if not str(hjson[item]['hostname']).startswith('*'):
        netw=inventory['all']['vars']['netids'][tid]
        hname=hjson[item]['hostname']
        # debug
        """print(netw + " - " + hname)"""
        inventory['all']['children'][netw][hname] = None
        inventory['all']['hosts'][hname] = None


# Called with `--list`.
if args.list:
  jsonStr = json.dumps(inventory, indent=2)
  print(jsonStr)
# Called with `--host [hostname]`.
elif args.host:
    print()
else:
  jsonStr = json.dumps(inventory, indent=2)
  print(jsonStr)
  """
  parser.print_help()
  sys.exit(1)"""

# https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html
# https://linuxhint.com/ansible_inventory_json_format/
# https://phpipam.net/api/api_documentation/
# _meta ???

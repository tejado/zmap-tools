#!/usr/bin/env python3
import sys
import ujson as json
import json as json_orig
import traceback
import re
import argparse
import os.path
import operator
import requests
from threading import Thread
from queue import Queue

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

parser = argparse.ArgumentParser()
parser.add_argument('-f', "--file", help='Input JSON file', required=True)
parser.add_argument('-i', "--index-of", help='Show all with Index Of /', action="store_true")
parser.add_argument('-e', "--index-of-extended", help='Extract and show directory listing', action="store_true")
parser.add_argument('-r', "--recursive", help='Recursive directory listing', action="store_true")
parser.add_argument("-c", "--cn", help='Output TLS Cert Common Names', action="store_true")
parser.add_argument('-s', "--summary", help='Output summary', action="store_true")
parser.add_argument("--no-header", help='Suppress header', action="store_true")

args = parser.parse_args()

if not args.no_header:
  print("==============================================")
  print("| zdata v0.33c3 - A zmap JSON Output Utility |")
  print("==============================================")

file = args.file
if not os.path.isfile(file):
  exit('Error: Input file not found')

regex_indexof_links_all = re.compile(r'<a href="[^\?]', re.MULTILINE)
regex_indexof_links_path = re.compile(r'<a href="([^\?]+?)"', re.MULTILINE)

line_count = 0
line_count_with_data = 0
status_codes = {}
tls_count = 0
listing_indexof = {}
listing_cn = {}
listing_directory = {}


concurrent = 200
q = Queue(concurrent * 2)

def doWork():
    while True:
        data = q.get()

        host = data[0]
        url = data[1]
        content = data[2]

        requests_session = requests.Session()
        requests_session.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

        listing_directory[host] = indexof_extended(url, content, requests_session)
        q.task_done()

for i in range(concurrent):
    t = Thread(target=doWork)
    t.daemon = True
    t.start()

def indexof_extended(url, content, sess, level=0):
  global requests_session
  level += 1
  if level > 5:
    return 'RECURSION_LIMIT'
  folder = {}
  folder_links = regex_indexof_links_path.findall(content)
  try:
    folder_links.remove('../')
  except:
    pass

  try:
    folder_links.remove('/')
  except:
    pass

  for link in folder_links:
    if link.endswith('/'):
      if args.recursive:
        subfolder_url = "{}{}".format(url, link)
        try:
          r = sess.get(subfolder_url, verify=False, timeout=2)
        except:
          folder[link] = 'DIRECTORY_SUBFOLDER_LOAD_ERROR'
          continue
        subfolder_content = r.text
        if 'Index of' in subfolder_content:
          folder[link] = indexof_extended(subfolder_url, subfolder_content, sess, level)
        else:
          folder[link] = 'DIRECTORY_WITHOUT_INDEX'
      else:
        folder[link] = 'DIRECTORY'
    else:
      folder[link] = 'FILE'

  return folder

def process_entry(line):
    global q, line_count, line_count_with_data, status_codes, tls_count, listing_indexof, listing_cn
    line_count += 1
    try:
      result = json.loads(line)
    except:
      traceback.print_exc()
    if 'data' in result:
      line_count_with_data += 1

      status_code = 0
      try:
        status_code = result['data']['http']['response']['status_code']
      except KeyError as e:
        pass

      if status_code not in status_codes:
        status_codes[status_code] = 1
      else:
        status_codes[status_code] += 1

      cn = "n/a"
      tls = False
      url = "/"
      try:
        #host = result['data']['http']['response']['request']['host']
        host = result['data']['http']['response']['request']['url']['host']
        schema = result['data']['http']['response']['request']['url']['scheme']
        url = "{}://{}/".format(schema, host)
        if 'tls_handshake' in result['data']['http']['response']['request']:
          tls_count += 1
          tls = True
          try:
            cn = result['data']['http']['response']['request']['tls_handshake']['server_certificates']['certificate']['parsed']['subject']['common_name'][0].encode('latin-1')
          except:
            cn = result['data']['http']['response']['request']['tls_handshake']['server_certificates']['certificate']['parsed']['subject']['common_name'][0]
      except KeyError as e:
        pass

      if tls and args.cn:
        listing_cn[host] = cn

      try:
        content = result['data']['http']['response']['body']
        if 'Index of /' in content:
          match = regex_indexof_links_all.findall(content)
          #print( "{} has index ({})".format(host, len(match)) )
          listing_indexof[host] = len(match)

          if args.index_of_extended:
            #print('===================================================================')
            #print(url)
            #struct = indexof_extended(url, content)
            #print( json_orig.dumps(struct, indent=4, sort_keys=True) )
            q.put([host, url, content])
      except KeyError as e:
        pass
      except:
        traceback.print_exc()



with open(file) as f:
  for line in f:
    process_entry(line)


if args.cn:
  for host in listing_cn:
    print("{} -> {}".format(host, listing_cn[host]))

def print_folder_structure(structure, level=0):
  level += 1
  indent = ' ' * 4 * (level)
  for key in structure:
    value = structure[key]
    if isinstance(value, dict):
      print(indent + key)
      print_folder_structure(value, level)
    else:
      print(indent + key)


if args.index_of:
  sort = sorted(listing_indexof.items(), key=operator.itemgetter(1),reverse=True)
  for entry in sort:
    print("{} has index ({})".format(entry[0], entry[1]))
    if args.index_of_extended and entry[0] in listing_directory:
      #print( json_orig.dumps(listing_directory[entry[0]], indent=4, sort_keys=True) )
      print_folder_structure(listing_directory[entry[0]])



if args.summary:
  print("=====================================")
  print("Line Count: %s" % line_count)
  print("Line Count with data: %s" % line_count_with_data)
  print("TLS count: %s" % tls_count)
  print("=====================================")
  for status_code in status_codes:
    print("Status Code {: >3}: {: >8} responses".format(status_code, status_codes[status_code]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Prince Mendiratta
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import os.path
import sys
import requests
import time
import json
from os import path, sep
from datetime import datetime
from bs4 import BeautifulSoup
from requests.exceptions import Timeout
from lxml import html
from lxml.etree import tostring
import hashlib
import hmac
import base64
import json
from requests.adapters import HTTPAdapter, Retry
# from .bot.plugins.broadcast import sendtelegram


def request_time():
    print("[*] Checking NU Website for notices now....")
    try:
        s = requests.Session()
        headers = {
        "User-Agent": 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        "Content-Type": 'text/html; charset=UTF-8'
        }
        retries = Retry(total=500,
                        backoff_factor=0.1,)
        s.mount('https://', HTTPAdapter(max_retries=retries))
        r = s.get(('https://www.nu.ac.bd/'), headers=headers, timeout=25)
    except Timeout:
        print("[{}]: The request timed out.".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        return [403]


    write = open("cache.txt", "w") 
    write.write(str(r.text))
    write.close()
    read = open("cache.txt", "r") 
    tree = html.fromstring(read.read())
    try:
        top_notice = tree.xpath(
            '//*[@id="section1"]/div/div/div[1]/table/tbody/tr[1]/td[1]/a')[0].text_content()
    except Exception as e:
        print('TOP NOTICE TITLE ERROR ' + str(e))
    
    try:
        top_link = tree.xpath(
            '//*[@id="section1"]/div/div/div[1]/table/tbody/tr[1]/td[1]/a')[0]
        top_link = top_link.attrib.get('href', None)
        if top_link is not None:
            top_link = ('https://www.nu.ac.bd/uploads' + top_link.split('uploads', 1)[1])
    except IndexError:
        top_link = ''

    tabs = ['//*[@id="section1"]/div/div/div[1]', '//*[@id="section-3"]/div/div/div/div[1]', '//*[@id="section-4"]/div/div/div[1]', '//*[@id="section-6"]/div/div/div[1]']
    #tabs = [3, 4]
    tab_titles = ['Latest Notice', 'Examination', 'Admissions',
                  'News/Press Release']
    y = 0
    records = {}
    titles = []
    for tab_iterator in tabs:
        tab = tab_titles[y]
        full_list = tree.xpath('{}/table/tbody'.format(tab_iterator))[0]
        max_range = 1
        for ele in full_list:
            if ele.tag == 'tr' and ele.get('class', None) is None:
                max_range += 1
        max_range = min(max_range, 20)
        for notice_iterator in range(1, max_range):
            try:
                title = notice_title(tab_iterator, notice_iterator, tree)
                
                rest = notice_link(tab_iterator, notice_iterator, tree)
                notice = {
                    "title": title,
                    "link": rest[0],
                    "children": {
                        "titles": rest[2],
                        "links": rest[1]
                    },
                    "tab": tab
                }
                #print(notice)
                if title != "":
                    titles.append(notice)
            except Exception as e:
                print("No title - " + str(e))
                pass
        records[tab] = titles
        titles = []
        y += 1
        max_range = 2

    previous_records = records
    if not path.exists("bot/hf/recorded_status.json"):
        data = json.dumps(previous_records)
        with open("bot/hf/recorded_status.json", "w+") as f:
            f.write(data)
            print("[*] Recorded Current Status.\n[*] Latest dates: {}".format(data))
            return_values = [404, top_notice, top_link, ' ', ' ']
            return return_values
    else:
        with open("bot/hf/recorded_status.json", "r") as f:
            data = f.read()
        previous_records = json.loads(data)
        modified_keys = dict_compare(records, previous_records)
        if modified_keys != []:
            # print(modified_keys)
            # return_values = [200, top_notice,
            #                  top_link, modified_keys["title"], modified_keys["link"], modified_keys["tab"]]
            return_values = [200, top_notice,
                             top_link, modified_keys]
            print(return_values)
            return return_values
        else:
            return_values = [404, top_notice, top_link, ' ', ' ']
            return return_values
        
        
def notice_title(tab_iterator, notice_iterator, tree):
    try:
        top_notice = tree.xpath(
            '{}/table/tbody/tr[{}]/td[1]/a'.format(tab_iterator, notice_iterator))[0].text_content().strip().replace("\u201c", "").replace("\u201d", "")
        return top_notice
    except Exception as e:
        print('TITLE ERROR ' + str(e))
        # sendtelegram(2, AUTH_CHANNEL, '_', 'Got an error finding the notice title.')

    

def notice_link(tab_iterator, notice_iterator, tree):
    print("tab_iterator", tab_iterator)
    print("notice_iterator", notice_iterator)
    try:
        links= []
        children = []
        notice_self_link = tree.xpath(
            '{}/table/tbody/tr[{}]/td[1]/a'.format(tab_iterator, notice_iterator))[0]
        notice_self_link = notice_self_link.attrib.get('href', None)
        print('Self Link: ', notice_self_link)
        if notice_self_link is not None and notice_self_link.startswith('uploads'):
            notice_self_link = ('https://www.nu.ac.bd/uploads' + notice_self_link.split('uploads', 1)[1])

        separators = tree.xpath('{}/table/tbody/tr[{}]/td[1]'.format(tab_iterator, notice_iterator))[0]
        if "#160".encode() in tostring(separators):
            print(tostring(separators))
            print(len(separators))
            # contains child links
            if "maroon".encode() in tostring(separators):
                # red link, contains all in h6
                for x in range(2,len(separators)):
                    print(x)
                    print(tostring(separators[x]))
                    print(separators[x].attrib.get('href', None))
                    print(separators[x].text_content())
                    if '<!--'.encode() in tostring(separators[x]):
                        pass
                    link = separators[x].attrib.get('href', None)
                    child = separators[x].text_content().replace('\xa0', '').replace('||', '')
                    if link is not None:
                        if link.startswith('uploafs') and link != '':
                            links.append('https://www.nu.ac.bd/uploads' + link.split('uploads', 1)[1])
                        else:
                            links.append(link)
                    if child != '' and 'Date' not in child:
                        children.append(child)
            else:
                ele = tree.xpath('{}/table/tbody/tr[{}]/td'.format(tab_iterator, notice_iterator))[0]
                for x in range(1,len(ele)):
                    # print(tostring(ele[x]))
                    # print(ele[x].text_content())
                    if '<!--'.encode() in tostring(ele[x]):
                        continue
                    link = ele[x].attrib.get('href', None)
                    child = ele[x].text_content().replace('\xa0', '').replace('||', '')
                    if link is not None:
                        if link.startswith('uploads') and link != '':
                            links.append('https://www.nu.ac.bd/uploads' + link.split('uploads', 1)[1])
                        else:
                            links.append(link)
                    if child != '' and 'Date' not in child:
                        children.append(child)
        return [notice_self_link, links, children]
    except Exception as e:
        print(str(tab_iterator), str(notice_iterator))
        print('LINK ERROR ' + str(e))
        # sendtelegram(2, AUTH_CHANNEL, '_', 'Got an error finding the notice link, {} {}.'.format(str(tab_iterator), str(notice_iterator)))

    
    
def dict_compare(d1, d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    shared_keys = d1_keys.intersection(d2_keys)
    out = []
    for o in shared_keys:
        for i in d1[o]:
            if i not in d2[o]:
                out.append(i)

    return out


def sign_request(body):

    key = bytes(SHA_SECRET, 'UTF-8')
    body = bytes(str(body), 'UTF-8')

    digester = hmac.new(key, body, hashlib.sha1)
    signature1 = digester.hexdigest()
    return str(signature1)


def send_webhook_alert(xhash, body):
    Headers = {"X-Hub-Signature": xhash, "Content-Type": "application/json"}
    r = requests.post(url=WEBHOOK_ADDRESS, data=body, headers=Headers)
    print(r)
    print("Webhook configured.\nBody - ." +
                 body + "\nURL - " + WEBHOOK_ADDRESS)


    
request_time()
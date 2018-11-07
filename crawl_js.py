# -*- coding: UTF-8 -*-
import os
import re
import requests
import tldextract
from pyquery import PyQuery as pq
import validators

import logging
import logging.config

logging.config.fileConfig('logging.conf')
root_logger = logging.getLogger('root')
root_logger.info('start crawl url...')

HTML_FILE_DIR = os.getcwd() + "\\crawl_html\\"
JS_FILE_DIR = os.getcwd() + "\\crawl_js\\"

IS_CRAWL_HTML = True
IS_CRAWL_JS = True

TIMEOUT = 2

MAX_HTML_COUNT = 0
MAX_JS_COUNT = 0
global_html_count = 0
global_js_count = 0

global_js_index = 0
global_html_index = 0

global_html_list = []
global_js_list = []
global_site_status = dict()

def write_file(url, file_type):
    tld = tldextract.extract(url)
    main_domain = tld.registered_domain

    if global_site_status.get(main_domain) == False:
        return None

    else:
        global global_html_index
        global global_js_index
        global global_html_count
        global global_js_count

        try:
            response = requests.get(url, timeout = TIMEOUT)
            doc = pq(response.text)
            doc = doc.text()

            if not doc or file_type == 'html':
                return None

            if file_type == "js":
                with open(JS_FILE_DIR + str(global_js_index) + ".js", "w", encoding = 'UTF-8') as f:
                    f.write(doc)
                    global_js_index += 1
                    global_js_count += 1

        except requests.exceptions.ConnectTimeout:
        # 如果存在并且不为False(即为True时)，重新设置为False
            root_logger.info('###domain is:' + str(main_domain))

            if global_site_status.get(main_domain, -1) == -1:
                global_site_status[main_domain] = False

        except Exception as e:
            print("[-] Crawl exception 2")
            print(e)


def crawl(url, deep):
    global global_html_count

    try:
        tld = tldextract.extract(url)
        main_domain = tld.registered_domain

        if global_site_status.get(main_domain) == False:
            return None

        response = requests.get(url = url, timeout = TIMEOUT)
        doc = pq(response.text)

        if global_js_count < MAX_JS_COUNT:

            script_label = doc('script').items()

            for doc_inner in script_label:
                js_href = doc_inner('script').attr('src')

                if js_href and js_href.endswith('.js'):
                    js_href = js_href.strip('/')

                    if js_href.find('?') != -1:
                        js_href = js_href.split("?")[0]

                    if not re.search(r'https?://', js_href):
                        tld_sub = tldextract.extract(js_href)
                        main_domain_sub = tld_sub.registered_domain

                        if validators.domain(main_domain_sub):

                            if js_href.find('www.') != -1: #包含了www.
                                js_href = 'http://' + js_href

                            else:
                                js_href = 'http://www.' + js_href

                        else:
                            js_href = url + js_href

                            # else:
                            #
                            # js_href = url + js_href

                    print('way2', js_href)

                    if not js_href in global_js_list:
                        print("[+] Js: " + js_href)
                        global_js_list.append(js_href)
                        print(type(js_href))
                        write_file(js_href, "js")

        anchors = doc('a').items()
        for tag in anchors:
            html_href = tag.attr("href")

            if html_href:
                html_href = html_href.split("?")[0].split("#")[0].split("javascript:")[0].split(" ")[0]

                if html_href and len(html_href) > 0:
                    html_href = html_href.strip('/')

                if not re.search(r'https?://', html_href):
                    tld_sub = tldextract.extract(html_href)
                    main_domain_sub = tld_sub.registered_domain

                    if validators.domain(main_domain_sub):

                        if html_href.find('www.') != -1:  # 包含了www.
                            html_href = 'http://' + html_href

                        else:
                            html_href = 'http://www.' + html_href

                    else:
                        html_href = url + html_href

                    print('way~~~ is', html_href)

                if not html_href in global_html_list:
                    print("[+] Html: " + html_href)
                    global_html_list.append(html_href)

                    if global_html_count < MAX_HTML_COUNT:
                        #avoid too many same websites
                        global_html_count += 1

                    if not html_href.endswith('.exe'):
                        if deep > 0 and (global_html_count < MAX_HTML_COUNT   or global_js_count < MAX_JS_COUNT):
                            crawl(html_href, deep - 1)

    except requests.exceptions.ConnectTimeout:
        # 如果存在并且不为False(即为True时)，重新设置为False
        root_logger.info('###domain is:', main_domain)

        if global_site_status.get(main_domain, -1) == -1:
            global_site_status[main_domain] = False


    except Exception as e:
        print("[-] Crawl exception 1")
        print(e)


def schedule():
    print("[+] Start")

    global MAX_HTML_COUNT
    global MAX_JS_COUNT
    global global_html_count
    global global_js_count

    crawl_list = open("crawlList.txt")
    while True:
        line = crawl_list.readline()
        if not line:
            break

        tokens = line.split(",")
        if tokens[0][0] == '#':
            continue

        url = tokens[0].strip()
        rec_deep = 2
        MAX_HTML_COUNT = 100
        MAX_JS_COUNT = 100

        print("[+] Url: " + url + ", recursive deep: " + str(rec_deep) \
        + ", html count: " + str(MAX_HTML_COUNT) + ", js count: " + str(MAX_JS_COUNT))

        global_html_count = 0
        global_js_count = 0

        global_html_list.append(url)
        print(123)
        crawl(url, rec_deep)

    print("[+] Finish")

schedule()

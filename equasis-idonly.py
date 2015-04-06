__author__ = 'Excelle'


import re, os
import urllib2
import time
import string
import sqlite3
from multiprocessing import Pool, Queue, Process
from threading import Thread, current_thread
from HTMLParser import HTMLParser

'''
    1.Login and capture SESSIONID
    2.Send POST search request with the given Session-ID
    3.Analyze the HTML page.
    4.Parse SHIPID and PageID
'''

debug_mode = True
_LOGFILE = './crawler_equasis.log'

_user_name = ''
_user_list = Queue()
expire_count = 0
_user_pwd = '1234567'
base_url = 'http://www.equasis.org'
# POST,
_login_url = 'http://www.equasis.org/EquasisWeb/authen/HomePage?fs=HomePage'
# _login_post = 'j_email=' + _user_name + '&submit=Ok&j_password=' + _user_pwd
cookie_header = ''
# POST
_ship_query_url = 'http://www.equasis.org/EquasisWeb/restricted/ShipInfo?fs=ShipList'
_ship_query_post = 'P_IMO='
# POST
_ship_search_url = 'http://www.equasis.org/EquasisWeb/restricted/ShipList?fs=ShipSearch'
# init sqlite
init_table_sql = 'create table ships (`imo_number` INT(8) NOT NULL primary key, `name` varchar(32),' \
                 '`mmsi` int(10), `call_sign` varchar(8) ,`tonnage` int(8) ,' \
                 '`type` varchar(64),`build_year` varchar(11),`flag` varchar(20),`status` varchar(40),' \
                 '`last_update_time` varchar(11),`overview` text,`management_detail` text,`classification_status` text,' \
                 '`classification_survey` text,`pi_info` text,`geo_info` text)'

# Request queues
ship_id_list = Queue()
ship_id_count = 0
ship_infos = Queue()

# Regex objects
_RE_SHIPID = re.compile(r'P_IMO.value=\'(\d+)\'')

# Err msg
no_page = 'No result has been found with your criteria.'
no_ship = 'No ship has been found with your criteria'
too_many = 'Too many results. Please narrow your search down'
login_expire = 'You have not registered'

cursor = None
conn = None

# Record page crawling info
current_ton_range = 99
current_page = 1


class MyIDParser(HTMLParser):

    def handle_starttag(self, tag, attrs):
        global ship_id_count, ship_id_list
        if tag == 'a':
            attr = dict()
            attr['onclick'] = ''
            for key, value in attrs:
                attr[key] = value
            if attr['onclick']:
                r = _RE_SHIPID.search(attr['onclick'])
                if r:
                    ship_id_list.put(r.group(1))
                    log_id(r.group(1))
                    ship_id_count += 1


def clear_list(lst):
    while lst.__len__():
        lst.pop(0)


def log(info):
    if debug_mode:
        print(time.strftime('%Y-%m-%d %H:%M:%S') + ' :' + info)
    with open(_LOGFILE, 'a') as f:
        f.writelines(time.strftime('%Y-%m-%d %H:%M:%S') + ' :' + info + '\r\n')


def log_id(info):
    with open('idlist.txt', 'a') as f:
        f.writelines(info + '\r\n')


def httprequest(method, url, data=''):
    # Create a HTTP request object
    reqobj = urllib2.Request(url)
    reqobj.add_header('Host', 'www.equasis.org')
    reqobj.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)'
                                    ' AppleWebKit/600.3.18 (KHTML, like Gecko) Version/7.1.3 Safari/537.85.12')
    reqobj.add_header('Accept', 'ftext/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    reqobj.add_header('Accept-Language', 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3')
    reqobj.add_header('Referer', base_url)
    if cookie_header:
        reqobj.add_header('Cookie', cookie_header)
    if method == 'POST':
        reqobj.add_header('Content-Type', 'application/x-www-form-urlencoded')
        reqobj.add_header('Content-Length', str(len(data)))
        reqobj.add_data(data)
    u = urllib2.urlopen(reqobj)
    return u


# Login
def login():
    global cookie_header, _user_name, _user_list, expire_count
    u = httprequest('POST', _login_url, 'j_email=' + _user_name + '&submit=Ok&j_password=' + _user_pwd)
    if not _user_name or expire_count == 3:
        _user_name = _user_list.get()
        expire_count = 0  # Reset expiration count

    if u.getcode() == 200:
        c = u.info().getheader('Set-Cookie')
        if c:
            cookie_header = re.split(';', c)[0]
        log('Logged in as %s' % _user_name)
        log('Session ID: %s' % cookie_header)
    else:
        log('HTTP error %d' % u.getcode())


def user_supervisor():
    log('User Supervisor: Process %s has launched' % os.getpid())
    global _user_list
    while True:
        if _user_list.empty():
            with open('user.list', 'r') as fp:
                for line in fp.readlines():
                    _user_list.put(line.strip())


def check_login(content):
    return not re.search(login_expire, content)


def crawl_id():
    global current_page, current_ton_range, ship_id_count
    log('ID Crawler: Starting process: %s' % os.getpid())
    start_ton = current_ton_range

    for val in range(start_ton, 403345, 5):
        while True:
            _ship_search_post = 'P_PAGE=' + str(current_page) + '&P_IMO=&P_CALLSIGN=&P_NAME=&P_MMSI=&P_GT_GT=' + str(val+1) \
                                + '&P_GT_LT=' + str(val+5) + '&P_DW_GT=&P_DW_LT=&P_CatTypeShip_rb=HC&P_CatTypeShip_p2=' \
                                                             '&P_CatTypeShip_p3=%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0&' \
                                                             'P_YB_GT=&P_YB_LT=&P_FLAG_rb=HC&P_FLAG_p2=&' \
                                                             'P_FLAG_p3=%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0&P_STATUS=' \
                                                             '&P_CLASS_rb=HC&P_CLASS_p2=&' \
                                                             'P_CLASS_p3=%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0&' \
                                                             'P_CLASS_ST_rb=HC&P_CLASS_ST_p2=&' \
                                                             'P_CLASS_ST_p3=%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0%A0&' \
                                                             'Submit=SEARCH'
            resp = httprequest('POST', _ship_search_url, _ship_search_post)
            log('Getting IDs from page %d with range %d-%d' % (current_page, val+1, val+5))
            current_page += 1
            current_ton_range = val
            if resp.getcode() == 200:
                log('200 OK Get. Starting reading.')
                text = resp.read()
                if not check_login(text):
                    global expire_count
                    log('Expired. Relogin')
                    expire_count += 1
                    login()
                    current_page -= 1
                    continue

                if re.search(no_page, text):
                    current_page = 1
                    break
                if re.search(too_many, text):
                    log('Too many results at page %d with range %d-%d' % (current_page, val+1, val+5))
                    current_page = 1
                    break

                par = MyIDParser()
                par.feed(text)
                time.sleep(1)


if __name__ == '__main__':
    try:
        print('Starting to crawl....')
        # Preparations
        # initSQLDb()
        # p = Pool(processes=3)
        log('Starting to load user list file..')
        proc_user = Process(target=user_supervisor, args=())
        proc_user.start()
        time.sleep(3)
        log('Logging in...')
        login()
        # Load last status
        if os.path.exists('./id.last') and os.path.exists('./page.last'):
            with open('id.last', 'r') as f:
                log('Load last ID list..')
                l = f.readlines()
                for i in l:
                    ship_id_list.put(i.strip())
            with open('page.last', 'r') as f:
                log('Load last page..')
                l = f.readlines()
                current_page, current_ton_range = int(l[0].strip()), int(l[1].strip())
        # Load crawling processes
        proc_id = Process(target=crawl_id, args=())
        proc_id.start()

        print('Doing all processes...')

        proc_user.join()
        proc_id.join()
        log('All process done.')

    except KeyboardInterrupt, ex:
        log('EXCEPTION: %s' % ex.message)
    finally:
        # Save state
        if not ship_id_list.empty():
            print('Saving status...')
            with open('id.last', 'w') as f:
                while not ship_id_list.empty():
                    f.writeline(ship_id_list.get() + '\n')
            with open('page.last', 'w') as f2:
                f2.writeline(str(current_page) + '\n')
                f2.writeline(str(current_ton_range))
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
login_expire = 'You have not registered'

cursor = None
conn = None

# Record page crawling info
current_ton_range = 99
current_page = 1


class Ship():
    imo_number = 0
    name = ''
    mmsi = 0
    call_sign = ''
    tonnage = 0
    type = ''
    build_year = 0
    flag = ''
    status = ''
    last_update = ''
    overview_list = list()
    management_detail_list = list()
    classification_status = list()
    classification_survey = list()
    pi_info = list()
    geo_info = list()

    def add_overview(self, content, value):
        self.overview_list.append(dict(overview=content, value=value))

    def add_management(self, imo, role, company, address, date):
        self.management_detail_list.append(dict(imo_num=imo, role=role, company=company, address=address, date_of_effect=date))

    def add_class_stat(self, society, date, status, reason):
        self.classification_status.append(dict(class_society=society, date_change_stat=date, status=status, reason=reason))

    def add_class_survey(self, society, date, date_next, detail):
        self.classification_survey.append(dict(class_society=society, date_last=date, date_next=date_next, detail=detail))

    def add_pi(self, insurer, date):
        self.pi_info.append(dict(insurer=insurer, date_inception=date))

    def add_geo(self, date, area, source):
        self.geo_info.append(dict(date_record=date, seen_area=area, source=source))

    def list_to_str(self, l):
        tmp = list()
        for i in range(0, l.__len__()):
            tmp.append(str(l.pop(0)))
        s = string.join(tmp, '\n')
        return s.replace("'", '|').replace('"', '|')

    def dispose(self):
        clear_list(self.overview_list)
        clear_list(self.management_detail_list)
        clear_list(self.classification_status)
        clear_list(self.classification_survey)
        clear_list(self.pi_info)
        clear_list(self.geo_info)

    def Commit(self):
        global cursor, conn
        sql = 'insert into ships (`imo_number`, `name`, `mmsi`, `call_sign`, `tonnage`, `type`,' \
              ' `build_year`, `flag`, `status`, `last_update_time`, `overview`, `management_detail`,' \
              ' `classification_status`, `classification_survey`,`pi_info`, `geo_info`) VALUES (%s,' \
              ' "%s", %s, "%s", %s, "%s", %s, "%s", "%s", "%s", "%s", "%s", "%s", ' \
              '      "%s", "%s", "%s")' % (self.imo_number, self.name, self.mmsi, self.call_sign,
                                           self.tonnage, self.type, self.build_year, self.flag,
                                           self.status, self.last_update, self.list_to_str(self.overview_list),
                                           self.list_to_str(self.management_detail_list),
                                           self.list_to_str(self.classification_status),
                                           self.list_to_str(self.classification_survey),
                                           self.list_to_str(self.pi_info), self.list_to_str(self.geo_info))
        try:
            cursor.execute(sql)
            conn.commit()
            log('#%s Ship successfully written into DB - %d.' % (self.imo_number, cursor.rowcount))
        except sqlite3.OperationalError, ex:
            log('DB EXCEPTION: %s' % ex.message)


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


class MyInfoParser(HTMLParser):
    basic_info_flag = False
    basic_info_flag_2 = False
    ext_info_title_begin = False
    ext_info_title_end = False
    ext_info_start = False
    current_ext_tag = ''
    _list_basic_info = []
    _list_overview = []
    _list_manage_detail = []
    _list_class_stat = []
    _list_class_survey = []
    _list_pi = []
    _list_geo = []

    def __init__(self):
        self._list_basic_info = []
        self._lit_overview = []
        self._lit_manage_detail = []
        self._lit_class_stat = []
        self._lit_class_survey = []
        self._lit_pi = []
        self._list_geo = []
        self.reset()

    def handle_starttag(self, tag, attrs):
        attr = dict()
        attr['class'] = ''
        attr['src'] = ''
        for key, value in attrs:
            attr[key] = value
        if tag == 'td' and attr['class'] == 'bleugras':
            self.basic_info_flag = True
            self.basic_info_flag_2 = False
            return
        if tag == 'td' and self.basic_info_flag:
            self.basic_info_flag = False
            self.basic_info_flag_2 = True
        if tag == 'img' and attr['src'] == '../Static/img/puce_triangle_tit.gif':
            self.ext_info_title_begin = True
            self.ext_info_title_end = False
            return
        if tag == 'tr' and (attr['class'] == 'lignej' or attr['class'] == 'ligneb'):
            self.ext_info_start = True
            return

    def handle_endtag(self, tag):
        if self.ext_info_start and tag == 'tr':
            self.ext_info_start = False
        pass

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_data(self, data):
        if self.basic_info_flag and not self.basic_info_flag_2:
            self._list_basic_info.append(data)
        if self.basic_info_flag_2 and not self.basic_info_flag:
            self._list_basic_info.append(data)
            self.basic_info_flag_2 = False
        if self.ext_info_title_begin and not self.ext_info_title_end:
            self.current_ext_tag = data
            self.ext_info_title_end = True
            self.ext_info_title_begin = False
        if self.ext_info_start:
            if re.search('OVERVIEW', self.current_ext_tag):
                self._list_overview.append(data)
            elif re.search('Management', self.current_ext_tag):
                self._list_manage_detail.append(data)
            elif re.search('Classification status', self.current_ext_tag):
                self._list_class_stat.append(data)
            elif re.search('Classification survey', self.current_ext_tag):
                self._list_class_survey.append(data)
            elif re.search('P/I', self.current_ext_tag):
                self._list_pi.append(data)
            elif re.search('Geographical', self.current_ext_tag):
                self._list_geo.append(data)
            # print('%s : %s' % (self.current_ext_tag, data))

    def handle_entityref(self, name):
        if self.ext_info_start:
            print('%s : <&%s>' % (self.current_ext_tag, name))

    def get_basic_info(self):
        res = []
        for i in range(0, self._list_basic_info.__len__()):
            res.append(self._list_basic_info.pop(0))
        return res

    def get_manage_detail(self):
        res = []
        for i in range(0, self._list_manage_detail.__len__()):
            res.append(self._list_manage_detail.pop(0))
        return res

    def get_class_status(self):
        res = []
        for i in range(0, self._list_class_stat.__len__()):
            res.append(self._list_class_stat.pop(0))
        return res

    def get_class_survey(self):
        res = []
        for i in range(0, self._list_class_survey.__len__()):
            res.append(self._list_class_survey.pop(0))
        return res

    def get_pi_info(self):
        res = []
        for i in range(0, self._list_pi.__len__()):
            res.append(self._list_pi.pop(0))
        return res

    def get_geographical_info(self):
        res = []
        for i in range(0, self._list_geo.__len__()):
            res.append(self._list_geo.pop(0))
        return res

    def get_overview(self):
        res = []
        for i in range(0, self._list_overview.__len__()):
            res.append(self._list_overview.pop(0))
        return res

    def dispose(self):
        self._list_basic_info = None
        self._list_manage_detail = None
        self._list_class_stat = None
        self._list_class_survey = None
        self._list_overview = None
        self._list_pi = None
        self._list_geo = None


def initSQLDb():
    global cursor, conn
    conn = sqlite3.connect('equasis.db')
    cursor = conn.cursor()
    try:
        cursor.execute(init_table_sql)
    except sqlite3.OperationalError:
        pass
    conn.commit()


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
    while True:
        global _user_list
        if _user_list.empty():
            with open('user.list', 'r') as fp:
                for line in fp.readlines():
                    _user_list.put(line.strip())


def check_login(content):
    return not re.search(login_expire, content)


def crawl_ship():
    global ship_id_count
    log('Starting process: %s' % os.getpid())
    last_id = ''
    while not ship_id_list.empty():
        if not last_id:
            _id = ship_id_list.get()
            ship_id_count -= 1
        else:
            _id = last_id
        try:
            query_ship(_id)
            last_id = ''
        except urllib2.HTTPError, e:
            log('HTTP EXCEPTION: %s When querying #%s' % (e.message, _id))
            last_id = _id

    log('Process %s done.' % os.getpid())


def query_ship(id):
    global ship_id_count
    log('Start querying ship ID #%s' % id)
    resp = httprequest('POST', _ship_query_url, _ship_query_post + id)
    if resp.getcode() == 200:
        log('200 OK get. Start parse data at #%s' % id)
        parser = MyInfoParser()
        parser.reset()
        content = resp.read()
        # Check login status.
        if not check_login(content):
            global expire_count
            log('Expired. Relogin')
            login()
            expire_count += 1
            log('Put back ship ID #%s to queue...')
            ship_id_list.put(id)
            ship_id_count += 1
            return
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&', '/')
        parser.feed(content)
        basic = parser.get_basic_info()
        ship = Ship()
        ship.imo_number = id
        # Basic info
        for i in range(0, basic.__len__()-1, 2):
            if re.match('IMO', basic[i]):
                pass
                # ship.imo_number = basic[i+1]
            elif re.search('Name of ship', basic[i]):
                ship.name = basic[i+1]
            elif re.search('MMSI', basic[i]):
                ship.mmsi = basic[i+1]
            elif re.search('Call Sign', basic[i]):
                ship.call_sign = basic[i+1]
            elif re.search('Gross tonnage', basic[i]):
                ship.tonnage = int(basic[i+1])
            elif re.search('Type', basic[i]):
                ship.type = basic[i+1]
            elif re.search('Year of build', basic[i]):
                ship.build_year = int(basic[i+1])
            elif re.search('Flag', basic[i]):
                ship.flag = basic[i+1]
            elif re.search('Status', basic[i]):
                ship.status = basic[i+1]
            elif re.search('Last update', basic[i]):
                ship.last_update = basic[i+1]
            else:
                pass
        clear_list(basic)
        # Overview
        ovw = parser.get_overview()
        if ovw:
            for i in range(0, ovw.__len__()-1, 2):
                ship.add_overview(ovw[i], ovw[i+1])
        clear_list(ovw)
        # Management Detail
        md = parser.get_manage_detail()
        if md:
            for i in range(0, md.__len__()-1, 5):
                ship.add_management(md[i], md[i+1], md[i+2], md[i+3], md[i+4])
        clear_list(md)
        # Classification status
        css = parser.get_class_status()
        if css:
            for i in range(0, css.__len__()-1, 4):
                ship.add_class_stat(css[i], css[i+1], css[i+2], css[i+3])
        clear_list(css)
        # Classification Survey
        csv = parser.get_class_survey()
        if csv:
            for i in range(0, csv.__len__()-1, 3):
                ship.add_class_survey(csv[i], csv[i+1], csv[i+2], '')
        clear_list(csv)
        # PI information
        pi = parser.get_pi_info()
        if pi:
            for i in range(0, pi.__len__()-1, 2):
                ship.add_pi(pi[i], pi[i+1])
        clear_list(pi)
        # Geographical information
        ge = parser.get_geographical_info()
        if ge:
            for i in range(0, ge.__len__()-1, 3):
                ship.add_geo(ge[i], ge[i+1], ge[i+2])
        clear_list(ge)
        log('Parsing #%s complete. Starting to write to DB.' % ship.imo_number)
        if not ship.imo_number or not ship.name:
            log('Empty data line encountered. Put back ID #%s' % id)
            ship_id_list.put(id)
        else:
            ship.Commit()

        ship.dispose()
        parser.close()
        content = ''
        resp.close()
        pass

    else:
        log('Error HTTP status: %d' % resp.getcode())


def crawl_id():
    global current_page, current_ton_range, ship_id_count
    log('Starting process: %s' % os.getpid())
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
                par = MyIDParser()
                par.feed(text)
                if ship_id_count > 20:
                    time.sleep(ship_id_count / 10)

if __name__ == '__main__':
    try:
        print('Starting to crawl....')
        # Preparations
        initSQLDb()
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
        time.sleep(5)
        proc_ship = Process(target=crawl_ship, args=())
        proc_ship.start()

        print('Doing all processes...')

        proc_user.join()
        proc_id.join()
        proc_ship.join()
        log('All process done.')

    except KeyboardInterrupt, ex:
        log('EXCEPTION: %s' % ex.message)
    finally:
        cursor.close()
        conn.close()
        # Save state
        if not ship_id_list.empty():
            print('Saving status...')
            with open('id.last', 'w') as f:
                while not ship_id_list.empty():
                    f.writeline(ship_id_list.get() + '\n')
            with open('page.last', 'w') as f2:
                f2.writeline(str(current_page) + '\n')
                f2.writeline(str(current_ton_range))
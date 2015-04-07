__author__ = 'Excelle'


import re, os
import urllib2
import time
from logger import log, log_id
from HTMLParser import HTMLParser
from model import initSQLDb, Ship, close_db
from parsers import MyInfoParser
from multiprocessing import Queue, Process
from multiprocessing.queues import SimpleQueue

'''
    1.Login and capture SESSIONID
    2.Send POST search request with the given Session-ID
    3.Analyze the HTML page.
    4.Parse SHIPID and PageID
'''

_user_name = 'ab@fstech.host56.com'
_user_list = Queue()
# Ship info list pending to be written to DB
ship_info_list = Queue()
expire_count = 0
_user_pwd = '1234567'
base_url = 'http://www.equasis.org'
# POST,
_login_url = 'http://www.equasis.org/EquasisWeb/authen/HomePage?fs=HomePage'
# _login_post = 'j_email=' + _user_name + '&submit=Ok&j_password=' + _user_pwd
cookie_header = ''
# POST
_ship_query_url = 'http://www.equasis.org/EquasisWeb/restricted/ShipInfo?fs=ShipList'
_ship_imo_conv_url = 'http://www.equasis.org/EquasisWeb/restricted/ShipCertification?fs=ShipInfo'
_ship_psc_url = 'http://www.equasis.org/EquasisWeb/restricted/ShipInspection?fs=ShipCertification'
_ship_inspect_url = 'http://www.equasis.org/EquasisWeb/restricted/DetailsPSC?fs=ShipInspection'
_ship_history_url = 'http://www.equasis.org/EquasisWeb/restricted/ShipHistory?fs=ShipCertification'
_company_url = 'http://www.equasis.org/EquasisWeb/restricted/CompanyInfo?fs=ShipInfo'
_fleet_url = 'http://www.equasis.org/EquasisWeb/restricted/FleetInfo?fs=CompanyInfo'
_ship_query_post = 'P_IMO='
# POST
_ship_search_url = 'http://www.equasis.org/EquasisWeb/restricted/ShipList?fs=ShipSearch'

# Request queues
ship_id_list = Queue()
ship_id_count = 0

# Err msg
no_page = 'No result has been found with your criteria.'
no_ship = 'No ship has been found with your criteria'
too_many = 'Too many results. Please narrow your search down'
login_expire = 'You have not registered'
_RE_SHIPID = re.compile(r'P_IMO.value=\'(\d+)\'')


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
    u = urllib2.urlopen(reqobj, timeout=10)
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
        time.sleep(1)


def check_login(content):
    return not re.search(login_expire, content)


def crawl_ship():
    global ship_id_count, ship_info_list
    log('Ship info crawler: Starting process: %s' % os.getpid())
    is_ok = True
    while not ship_id_list.empty():
        _id = ship_id_list.get()
        if is_ok:
            ship_id_count -= 1
        try:
            result = query_ship(_id)
            if result:
                # ------debug---------
                print result.overview_list
                print result.classification_status
                print result.imo_number
                # -------------------
                ship_info_list.put(result)
            is_ok = True
        except Exception, e:
            log('HTTP EXCEPTION: %s When querying #%s - Put back to queue.' % (e.message, _id))
            ship_id_list.put(_id)
            is_ok = False

    log('Process %s done.' % os.getpid())


def query_ship(_id):
    global ship_id_count
    log('Start querying ship ID #%s' % _id)
    resp = httprequest('POST', _ship_query_url, _ship_query_post + _id)
    if resp.getcode() == 200:
        log('200 OK get. Start parse data at #%s' % _id)
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
            ship_id_list.put(_id)
            ship_id_count += 1
            return
        ship = Ship()
        # Get page 1: Basic info
        content = content.replace('&nbsp;', 'N/A').replace('</BR><BR>', '\r\n')
        content = content.replace('&', '/').replace('<TD></TD>', '<TD>N/A</TD>')
        parser.feed(content)
        # Get company ids
        companies = parser.get_company_ids()
        companies = list(set(companies))
        time.sleep(1)
        # Get page 2: IMO convention
        resp = httprequest('POST', _ship_imo_conv_url, _ship_query_post + _id)
        log('IMO Convention Info at #' + _id)
        content = resp.read()
        content = content.replace('&nbsp;', 'N/A').replace('</BR><BR>', '\r\n')
        content = content.replace('&', '/').replace('<TD></TD>', '<TD>N/A</TD>')
        parser.feed(content)
        time.sleep(1)
        # Get page 3: PSC list
        resp = httprequest('POST', _ship_psc_url, _ship_query_post + _id)
        log('PSC Info at #' + _id)
        content = resp.read()
        content = content.replace('&nbsp;', 'N/A').replace('</BR><BR>', '\r\n')
        content = content.replace('&', '/').replace('<TD></TD>', '<td>N/A</td>')
        parser.feed(content)
        time.sleep(1)
        # Get page 4: History
        resp = httprequest('POST', _ship_history_url, _ship_query_post + _id)
        log('History info at #' + _id)
        content = resp.read()
        content = content.replace('&nbsp;', 'N/A').replace('</BR><BR>', '\r\n')
        content = content.replace('&', '/').replace('<TD></TD>', '<td>N/A</td>')
        parser.feed(content)
        time.sleep(1)
        # Get page 5: Inspect detail
        insp_ids = parser.get_insp_id()
        for i_id in insp_ids:
            resp = httprequest('POST', _ship_inspect_url, 'P_IMO=' + _id + '&P_INSP=' + i_id)
            log('Inspection detail at #' + _id + ',' + i_id)
            content = resp.read()
            content = content.replace('&nbsp;', 'N/A').replace('</BR><BR>', '\r\n')
            content = content.replace('&', '/').replace('<TD></TD>', '<td>N/A</td>')
            parser.feed(content)
            time.sleep(1)
        # Now to retrieve company infos

        # ----
        basic = parser.get_basic_info()
        ship.imo_number = _id
        for c_id in companies:
            resp = httprequest('POST', _company_url, 'P_IMO=' + _id + '&P_COMP=' + c_id)
            content = resp.read()
            log('Company info #' + c_id)
            content = content.replace('&nbsp;', 'N/A').replace('</BR><BR>', '\r\n')
            content = content.replace('&', '/').replace('<TD></TD>', '<td>N/A</td>')
            p_company = MyInfoParser()
            p_company.feed(content)
            # Company basic info
            c_basicinfo = p_company.get_basic_info()
            c_imo = ''
            c_name = ''
            c_addr = ''
            c_last_up = ''
            for i in range(0, c_basicinfo.__len__()-1, 2):
                if re.search('IMO number', basic[i]):
                    c_imo = c_basicinfo[i+1]
                elif re.search('Name', basic[i]):
                    c_name = c_basicinfo[i+1]
                elif re.search('Address', basic[i]):
                    c_addr = c_basicinfo[i+1]
                elif re.search('Last update', basic[i]):
                    c_last_up = c_basicinfo[i+1]
            if c_imo:
                ship.add_company_info(c_imo, c_name, c_addr, c_last_up)
            clear_list(c_basicinfo)
            # Company Overview
            o = p_company.get_company_overview()
            if o:
                for i in range(0, o.__len__()-1, 2):
                    ship.add_company_overview(c_id, o[i], o[i+1])
            clear_list(o)
            # Doc of Compliance
            doc = p_company.get_doc_compliance()
            if doc:
                for i in range(0, doc.__len__()-1, 6):
                    ship.add_doc_compliance(c_imo, doc[i], doc[i+1], doc[i+2],
                                            doc[i+3], doc[i+4], doc[i+5])
            clear_list(doc)
            # Syn of Insp
            so = p_company.get_synthesis_insp()
            if so:
                for i in range(0, so.__len__()-1, 6):
                    ship.add_synthesis_inspection(c_imo, so[i], so[i+1], so[i+2],
                                                  so[i+3], so[i+4], so[i+5])
            clear_list(so)
            # Class key
            time.sleep(1)
            resp = httprequest('POST', _fleet_url, 'P_PAGE=1&P_COMP=' + c_id)
            log('Class key info at company #' + c_id)
            content = resp.read()
            content = content.replace('&nbsp;', 'N/A').replace('</BR><BR>', '\r\n')
            content = content.replace('&', '/').replace('<TD></TD>', '<td>N/A</td>')
            p_company.feed(content)
            ck = p_company.get_class_key()
            if ck:
                for i in range(0, ck.__len__()-1, 2):
                    ship.add_class_key(c_id, ck[i], ck[i+1])
            clear_list(ck)
            # Fleet

            fleet_page = 1
            parse_f = MyInfoParser()
            while True:
                resp = httprequest('POST', _fleet_url, 'P_COMP=' + c_id + '&P_PAGE=' + str(fleet_page))
                content = resp.read()
                log('Fleet #%s Page %d' % (c_id, fleet_page))
                if not re.search('Class key', content):
                    break
                content = content.replace('&nbsp;', 'N/A').replace('</BR>', '\r\n').replace('<BR>', '')
                content = content.replace('&', '/').replace('<TD></TD>', '<td>N/A</td>')
                parse_f.feed(content)
                fleet_page += 1
                time.sleep(1)
            fl = parse_f.get_fleet()
            if fl:
                for i in range(0, fl.__len__()-1, 9):
                    ship.add_fleet(c_id, fl[i], fl[i+1], fl[i+2], fl[i+3], fl[i+4], fl[i+5],
                                   fl[i+6], fl[i+7], fl[i+8])
            clear_list(fl)
            parse_f.dispose()
            parse_f.close()
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
            elif re.search('DWT', basic[i]):
                ship.dwt = basic[i+1]
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
        overview = parser.get_overview()
        if overview:
            for i in range(0, overview.__len__()-1, 2):
                ship.add_overview(overview[i], overview[i+1])
        clear_list(overview)
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
        # Safety Management Certificate
        smc = parser.get_smc()
        if smc:
            for i in range(0, smc.__len__()-1, 7):
                ship.add_smc(smc[i], smc[i+1], smc[i+2], smc[i+3], smc[i+4], smc[i+5], smc[i+6])
        clear_list(smc)
        # IMO Conventions
        imoc = parser.get_imo_convention()
        if imoc:
            for i in range(0, imoc.__len__()-1, 2):
                ship.add_imo_convention(imoc[i], imoc[i+1])
        clear_list(imoc)
        # PSC List
        pscl = parser.get_psc_list()
        if pscl:
            for i in range(0, pscl.__len__()-1, 8):
                ship.add_psc_list(pscl[i], pscl[i+1], pscl[i+2], pscl[i+3], pscl[i+4],
                                  pscl[i+5], pscl[i+6], pscl[i+7])
        clear_list(pscl)
        # History name
        hn = parser.get_history_name()
        if hn:
            for i in range(0, hn.__len__()-1, 3):
                ship.add_history_name(hn[i], hn[i+1], hn[i+2])
        clear_list(hn)
        # History flag
        hf = parser.get_history_flag()
        if hf:
            for i in range(0, hf.__len__()-1, 3):
                ship.add_history_flag(hf[i], hf[i+1], hf[i+1])
        clear_list(hf)
        # History class
        hc = parser.get_history_class()
        if hc:
            for i in range(0, hc.__len__()-1, 3):
                ship.add_history_class(hc[i], hc[i+1], hc[i+2])
        clear_list(hc)
        # History Company
        hcp = parser.get_history_company()
        if hcp:
            for i in range(0, hcp.__len__()-1, 4):
                ship.add_history_company(hcp[i], hcp[i+1], hcp[i+2], hcp[i+3])
        clear_list(hcp)
        # Deficiencies
        df = parser.get_deficiencies()
        if df:
            for i in range(0, df.__len__()-1, 3):
                ship.add_deficiency(df[i], df[i+1], df[i+2])
        clear_list(df)
        log('Parsing #%s complete. Starting to write to DB.' % ship.imo_number)
        if not ship.imo_number or not ship.name:
            log('Empty data line encountered. Put back ID #%s' % id)
            ship_id_list.put(id)
            return None
        else:
            return ship
    else:
        log('Error HTTP status: %d' % resp.getcode())
        return None


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
                time.sleep(20)


def db_supervisor():
    global ship_info_list
    while not ship_id_list.empty():
        time.sleep(30)
        while ship_info_list.empty():
            s = ship_info_list.get()
            # ------debug---------
            print s.overview_list
            print s.classification_status
            print s.imo_number
            # -------------------
            s.Commit()

if __name__ == '__main__':
    try:
        print('Starting to crawl....')
        # Preparations
        initSQLDb()
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
        # proc_ship2 = Process(target=crawl_ship, args=())
        # proc_ship3 = Process(target=crawl_ship, args=())
        # proc_ship4 = Process(target=crawl_ship, args=())
        # proc_ship5 = Process(target=crawl_ship, args=())
        # proc_ship6 = Process(target=crawl_ship, args=())
        proc_db = Process(target=db_supervisor, args=())
        proc_ship.start()
        proc_db.start()
        # time.sleep(0.5)
        # proc_ship2.start()
        # time.sleep(1)
        # proc_ship3.start()
        # time.sleep(1.5)
        # proc_ship4.start()
        # time.sleep(2)
        # proc_ship5.start()
        # time.sleep(3)
        # proc_ship6.start()

        print('Following ship list queue and commit them to DB.')

        print('Doing all processes...')

        proc_user.join()
        proc_id.join()
        proc_db.join()
        proc_ship.join()
        # proc_ship2.join()
        # proc_ship3.join()
        # proc_ship4.join()
        # proc_ship5.join()
        # proc_ship6.join()
        log('All process done.')
    except KeyboardInterrupt, ex:
        log('EXCEPTION: %s' % ex.message)
    finally:
        close_db()
        # Save state
        if not ship_id_list.empty():
            print('Saving status...')
            with open('id.last', 'w') as f:
                while not ship_id_list.empty():
                    f.write(ship_id_list.get() + '\n')
            with open('page.last', 'w') as f2:
                f2.write(str(current_page) + '\n')
                f2.write(str(current_ton_range))

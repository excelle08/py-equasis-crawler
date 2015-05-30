import sqlite3
from equasis import login, user_supervisor, check_login, httprequest
from logger import log
import re
import time
from multiprocessing import Process, Queue
import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "equasis-res.db")

cursor = None
conn = None
list_imo = Queue()
_RE_TYPE_TAG = re.compile(r'Type of ship \:\<\/TD\>\<TD\>([A-Za-z0-9 ]*)\<\/TD\>\<TD\>')


def init_sqlite_db():
    global cursor, conn, db_path
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()


def copy_company_address():
    sql_retrieve = 'SELECT imo_company, address FROM management_detail'
    if not cursor or not conn:
        return
    lst = cursor.execute(sql_retrieve).fetchall()
    for row in lst:
        print row[0] + ', ' + row[1]
        sql_update = 'UPDATE company_info SET address="%s" WHERE imo_company=%s' % (row[1], row[0])
        cursor.execute(sql_update)
    conn.commit()


def get_page_by_id(imo):
    ship_query_url = 'http://www.equasis.org/EquasisWeb/restricted/ShipInfo?fs=ShipList'
    ship_query_post = 'P_IMO='
    resp = httprequest('POST', ship_query_url, data=ship_query_post+imo)
    text = resp.read()
    return text


def type_parser(text):
    res = _RE_TYPE_TAG.search(text)
    if res:
        return res.group(1)
    else:
        return None


def crawler():
    # global cursor, conn
    while not list_imo.empty():
        try:
            imo = list_imo.get()
            _raw_text = get_page_by_id(imo)
            if not check_login(_raw_text):
                log('Expired - relogin.')
                login()
                list_imo.put(imo)
                continue
            _type = type_parser(_raw_text)
            sql_cmd = gen_sql(_type, imo)
            log(sql_cmd)
            # cursor.execute(sql_cmd)
            log_sql(sql_cmd)
            log('IMO_Number=' + imo + ', type=' + _type)
            # conn.commit()
        except Exception, e:
            log('EXCEPTION at ' + imo + ': ' + e.message)
            list_imo.put(imo)


def gen_sql(_type, imo):
    return 'UPDATE `ships` SET type="%s" WHERE imo_number=%s' % (_type, imo)


def log_sql(cmd):
    with open(str(os.getpid()) + '.sql', 'a') as f:
        f.write(cmd + ';\n')


if __name__ == '__main__':
    try:
        print os.getcwd()
        with open('to_be_repair.list', 'r') as f:
            l = f.readlines()
            print 'Lines are read.'
            for i in l:
                list_imo.put(i.strip())
        log('Load complete')
        # init_sqlite_db()
        # log('SQLite init complete')
        proc_user = Process(target=user_supervisor, args=())
        proc_user.start()
        time.sleep(1)
        login()
        log('Login.')
        proc_type = Process(target=crawler, args=())
        proc_type.start()
        proc_type.join()
        proc_user.join()
    except Exception, e:
        log(e.message)
    finally:
        with open('to_be_repair.list', 'w') as f:
            while not list_imo.empty():
                f.write(list_imo.get() + '\r\n')

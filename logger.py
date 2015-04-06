__author__ = 'Excelle'

import time
import re

debug_mode = True
_LOGFILE = './crawler_equasis.log'


def log(info):
    if debug_mode:
        print(time.strftime('%Y-%m-%d %H:%M:%S') + ' :' + info)
    with open(_LOGFILE, 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' :' + info + '\r\n')


def log_id(info):
    with open('idlist.txt', 'a') as f:
        f.write(info + '\r\n')
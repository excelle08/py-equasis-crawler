__author__ = 'Excelle'

from multiprocessing import Queue
from equasis import query_ship, login
from model import Ship

q = Queue()
login()
login()
s = query_ship('7397177')
q.put(s)
r = q.get()
print r.overview_list

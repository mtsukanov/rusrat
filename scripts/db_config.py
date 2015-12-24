#!/var/beacon/clr/bin/python 


import MySQLdb
from time import gmtime, strftime

db = MySQLdb.connect(host="172.28.104.170", port = 3306, user="rusrat",passwd="Orion123", db="thebankfront")
cur = db.cursor()

cid = 1

query = "SELECT * FROM customers where PhotoId > 0"

cur.execute(query)

for row in cur.fetchall():
   print row[26]

db.close()

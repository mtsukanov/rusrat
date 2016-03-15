from celery import Celery
from celery.task.control import inspect
from time import sleep
from flask import json
import pika
import requests
import MySQLdb
import ctasks
import time
#import celeryconfig
from random import randint,choice

app = Celery(backend='amqp://',broker='redis://localhost/0', celery_event_queue_ttl = 300)
"""broker='amqp://guest:guest@localhost:5672//'"""

@app.task
def transgen():
    try:
        transid = randint(1,1000)
        cardid = randint(1,8)
        cardnumber = randint(10**15,10**16-1)
        accountid = randint(1,100)
        terminalid = randint(1,100)
        terminaltype = choice(['atm','pos','mobapp','onlinebank'])
        mcc = randint(1000,9999)
    
        transstatus = choice(['ok','refusal','error'])
        transdate = strftime("%d.%m.%Y %H:%M:%S",gmtime())
        transsum = randint(100,20000)
    except:
        return '1'
    try:
        transcur = choice(['rub','euro','usd','kzt'])
        transtype = randint(0,5)
        transinfo = choice(['proddetlimit','atmerror','cardcashlimit'])
    except:
        return '2'
    try:
        fulltrans = {'transid':transid,'cardid':cardid,'cardnumber':cardnumber,'accountid':accountid,'terminalid':terminalid,'terminaltype':terminaltype,'mcc':mcc,
'transstatus':transstatus,'transdate':transdate,'transsum':transsum,'transcur':transcur,'transtype':transtype,'transinfo':transinfo}
        #que_result = transgen.delay('trans_mq','t_mq',json.dumps(fulltrans,ensure_ascii=False),'application/json','trans_mq')
        return fulltrans
    except:
        return 'Error'


if __name__ == '__main__':
    app.worker_main()


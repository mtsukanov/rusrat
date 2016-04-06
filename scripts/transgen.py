import pika
import time
import pymssql
from time import gmtime, strftime,sleep
from random import randint,choice
from celery import Celery
from flask import json
from billiard.exceptions import Terminated
app = Celery(backend='amqp://',broker='redis://localhost/0', celery_event_queue_ttl = 300)
"""broker='amqp://guest:guest@localhost:5672//'"""
@app.task
def rabbitmq_add(queue,routing_key,message_body,content_type,exchange_name):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        channel.exchange_declare(exchange=exchange_name, durable=True, type='topic')
        channel.queue_bind(queue = queue, exchange = exchange_name, routing_key=routing_key)
        #channel.exchange_bind(queue = queue, exchange = exchange_name)
        channel.basic_publish(exchange=exchange_name,routing_key=routing_key,body=message_body,properties=pika.BasicProperties(content_type=content_type))
        connection.close()
        return 'Succed adding to rabbitmq'
    except Exception:
        return 'Failed adding to rabbitmq'


@app.task(throws=(Terminated,))
def transgen():
    global i
    global k
    global fullarr
    try:
        i=0
        fullarr = []
        conn = pymssql.connect(server = '172.28.106.17',user = 'rtdm',password = 'Orion123',database='CIDB')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM [TRANSData].[TRANSACTION]')
        data = cursor.fetchall()
        for row in data:
            print row[0]
        while i ==0 :
            transid = randint(1,1000)
            cardid = randint(1,10)
            cardnumber = randint(10**15,10**16-1)
            accountid = randint(1,100)
            terminalid = randint(1,100)
            #terminaltype = choice(['atm','pos','mobapp','onlinebank'])
            #mcc = randint(1000,9999)
            transstatus = choice(['ok','refusal','error'])
            transdate = strftime("%d.%m.%Y %H:%M:%S",gmtime())
            transsum = randint(100,20000)
            transcur = choice(['rub','eur','usd','kzt'])
            transtype = randint(0,5)
            transinfo = choice(['proddetlimit','atmerror','cardcashlimit'])
            fulltrans = {'TransID':transid,'CardID':cardid,'CardNumber':cardnumber,'AccountID':accountid,'TermID':terminalid,
'TransStatus':transstatus,'TransDate':transdate,'TransSum':transsum,'TransCurrency':transcur,'TransType':transtype,
'TransInfo':transinfo,'TransParam1':'','TransParam2':'','TransParam3':'','TransParam4':''}
            que_result = rabbitmq_add('trans_mq','t_mq',json.dumps(fulltrans,ensure_ascii=False),'application/json','trans_mq')
            print 'id= '+transgen.request.id
            fullarr.append(fulltrans)
            #i+=1
        return fullarr
    except Exception as e:
        return e

if __name__ == '__main__':
    app.worker_main()


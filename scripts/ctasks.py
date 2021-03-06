from celery import Celery
from celery.task.control import inspect
from time import sleep,gmtime, strftime,strptime
from datetime import timedelta,datetime
from flask import json
import pika
import requests
import MySQLdb
import psycopg2
import pymssql
import base64
import urllib
from billiard.exceptions import Terminated
from random import randint,choice

from time import gmtime, strftime


import redis
import pickle
dur = redis.StrictRedis(host='localhost',port=6379,db=0)

rtdmpath = '10.20.1.190'

mssqlpath = '10.20.1.192'

mysqlpath = '10.20.1.20'

lunapath= '10.20.1.22'

prodserver = '10.20.1.21:5000'

app = Celery(backend='amqp://',broker='redis://localhost/0', celery_event_queue_ttl = 300)
"""broker='amqp://guest:guest@localhost:5672//'"""






@app.task(trail=True)
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


@app.task(trail=True)
def mysql_select(db_,select_, from_, where_):
    db = MySQLdb.connect(host=mysqlpath, port = 3306, user="rusrat",passwd="Orion123", db=db_,use_unicode = True,charset='UTF8')
    cur = db.cursor()
    if select_ is None or select_ == '':
        select_ = '*'
    if from_ is None or from_ == '':
        return 'Invalid SQL'
    if where_ is None or where_ == '':
        where_ = '1'
          
    query = "SELECT "+select_+" FROM "+db_+"."+from_+" WHERE "+where_
    cur.execute(query)
    dataset = []
    for row in cur.fetchall():
        dataset.append(row)
    return dataset


@app.task(trail=True)
def mssql_select(schema_,db_,select_, from_, where_):
    db = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database=schema_,charset='UTF8')
    cur = db.cursor()
    if select_ is None or select_ == '':
        select_ = '*'
    if from_ is None or from_ == '':
        return 'Invalid SQL'
    query = "SELECT "+select_+" FROM "+db_+"."+from_
    if (where_ is not None) and (where_ != ''):
        query += " WHERE "+where_
    cur.execute(query)
    dataset = []
    for row in cur.fetchall():
        dataset.append(row)
    return dataset


@app.task(trail=True)
def call_rtdm(dns,event,inputs):
    rtdm_addr = "http://"+dns+"/RTDM/rest/runtime/decisions/"+event
    payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
    r = requests.post(rtdm_addr, json = payload)
    resp = r.json()
    print 'call_rtdm is succeed'
    return resp


@app.task(trail=True)
def call_service(service,inputs):
    service_adr = "http://"+prodserver+"/"+service
    payload = inputs
    r = requests.post(service_adr, json = payload)
    resp = r.json()
    print 'call_service '+service +' is succeed'
    return resp


@app.task(throws=(Terminated,))
def post(maxevent):
    global maxid 
    maxid = maxevent  
    while json.loads(dur.get('lunapar')) == 1:
        sleep(7)
        Out =[] 
        try:
            db = psycopg2.connect(host=lunapath, port = 5432, user="testuser",password="password", dbname="FaceStreamRecognizer")
        except Exception as e:
            return e
        cur = db.cursor()
        query = "SELECT event_id,event_time,similarity,first_name,last_name,middle_name,event_photo,birth_date FROM event WHERE search_result ='TRUE' and event_id >"+str(maxid)
        cur.execute(query)

        for row in cur.fetchall():
            isfirts = 0
            cur2 = db.cursor()
            timequery = "SELECT MAX(event_time) FROM event WHERE middle_name = '"+str(row[5])+"' and event_id <> "+str(row[0])
            cur2.execute(timequery)
            data = cur2.fetchone()
            lasttimereq = data[0] 
            if lasttimereq == None:
                lasttimereq = datetime.now()
                isfirts = 1
            payload1 = {"id":row[5],"image":base64.b64encode(str(row[6]))}
            r1 = requests.put("http://"+prodserver+"/active_queue?option=terminal",json = payload1)
            payload2 = {"name":row[3],"surname":row[4],"middlename":"","dob":str(row[7]),"id":int(row[5]),"status":"processing","reason":"unknown","location":"camera","area":"retail"}
            r2 = requests.post("http://"+prodserver+"/active_queue",json = payload2)
            LunaData = {"cid":int(row[5]),"cam":"Retail","time":str(datetime.now())}
            que_result = rabbitmq_add('luna_mq','l_mq',json.dumps(LunaData,ensure_ascii=False),'application/json','luna_mq')
            print "successed add to rabbitmq"
            date_s = datetime.strftime(datetime.now(),"%m/%d/%y %H:%M:%S")
            date_e = datetime.strftime(lasttimereq,"%m/%d/%y %H:%M:%S")
            date_ss = datetime.strptime(date_s,"%m/%d/%y %H:%M:%S")
            date_ee = datetime.strptime(date_e,"%m/%d/%y %H:%M:%S")
            print "difference = "+str((date_ss-date_ee).seconds)
            print lasttimereq
            if datetime.now() - lasttimereq >= timedelta(minutes=5) or isfirts == 1:
                payload3 = {"cid":int(row[5]),"scenario":"","beaconid":"","spotid":2,"spotname":"The Store","time":str(datetime.now().isoformat(sep='T')),"trigger":"Luna"}
                r3= call_rtdm.apply_async((rtdmpath,"geomainevent",payload3),retry=False)
                Out.append({"event_id":row[0],"event_time":str(row[1]),"similarity":row[2],"first_name":row[3],"last_name":row[4]})
        query2 = "SELECT MAX(event_id) FROM event"
        cur.execute(query2)
        data = cur.fetchone()
        maxid = data[0]
        print Out,maxid
    return 'ok'



@app.task(throws=(Terminated,),ignore_result=False)
def facetztask():
    while json.loads(dur.get('facetzpar')) == 1:
        sleep(10)
        dur_tmp = json.loads(dur.get('Sesslist'))
        for sessid in dur_tmp:
            url = "https://api.facetz.net/v2/facts/user.json?key=51af6192-c812-423d-ae25-43a036804632&query={%22user%22:{%22id%22:%22"+sessid+"%22},%22ext%22:{%22exchangename%22:%22sas_demo%22}}"
            print ("Print result for URL post: " + str(url))
            Formatted = []
            r = requests.get(url)
            #print ("Print decoded request result: " + str(r.text))
            print ("Print result of a request: " + str(r))
            i=1
            for el in r.json()['visits']:
                formatted_el = {}
                formatted_el['number'] = i
                formatted_el['ts'] = datetime.strftime(datetime.fromtimestamp(el['ts']/1000),"%Y-%m-%d %H:%M:%S")
                if 'www.' in urllib.unquote(el['url']):
                    editurl=urllib.unquote(el['url']).replace('www.','')
                else:
                    editurl=urllib.unquote(el['url'])
                if 'http' not in editurl:
                    editurl=''.join(('http://',editurl))
                else:
                    editurl = editurl
                if not editurl.endswith('/'):
                    editurl=''.join((editurl,'/'))
                formatted_el['url'] = editurl
                Formatted.append(formatted_el)
                i+=1
            if dur_tmp != []:
                Result = {"sys":{"id":r.json()['id']},"site":Formatted}
                que_result = rabbitmq_add('facetz_mq','f_mq',json.dumps(Result,ensure_ascii=False),'application/json','facetz_mq')
    return 'ok'

@app.task(throws=(Terminated,))
def transgen():
    fullarr = []
    conn = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB')
    cursor = conn.cursor()
    cursor.execute('SELECT Max(TransID) FROM [TRANSData].[TRANSACTION]')
    data = cursor.fetchone()
    maxtrans = int(data[0])
    cursor.execute('SELECT MAX(AccountID),MIN(AccountID) FROM [DataMart].[ACCOUNT]')
    data = cursor.fetchone()
    maxacc = int(data[0])
    minacc = int(data[1])
    while json.loads(dur.get('transgenpar')) == 1:
        sleep(3)
        transid = maxtrans
        accountid = randint(minacc,maxacc)
        cursor.execute('SELECT AccountType FROM [DataMart].[ACCOUNT] where AccountID='+str(accountid))
        data = cursor.fetchone()
        acctype = data[0]
        cursor.execute('SELECT AccountAmount,ProdDetID FROM [DataMart].[ACCOUNT] where AccountID='+str(accountid))
        data = cursor.fetchone()
        accamount =  data[0]
        proddetid = data[1]
        if acctype == 'card':
            cursor.execute('SELECT CardID FROM [DataMart].[Card] where AccountID='+str(accountid)) 
            data = cursor.fetchall()
            cardid= int(choice(data)[0])
            cursor.execute('SELECT CardNumber,CardCashLImit,CardType FROM [DataMart].[Card] where CardID='+str(cardid))
            data = cursor.fetchone()
            cardnumber = data[0]
            cardcashlimit = data[1]
            cardtype = data[2]
            cursor.execute('SELECT ProdDetLimit FROM [DataMart].[PRODUCTDETAILS] where ProdDetID='+str(proddetid))
            data = cursor.fetchone()
            prodlimit = data[0]
            transsum = int(accamount)+int(prodlimit)+50000
            if cardtype == 'credit':
                if transsum > cardcashlimit: 
                    transstatus = "reject"
                    transinfo = "cardcashlimit"
                if transsum > accamount+prodlimit:
                    transstatus = "reject"
                    transinfo = "proddetlimit"
                if transsum <= cardcashlimit and transsum <= accamount+prodlimit:
                    transstatus = choice(['ok','error'])
                    if transstatus == 'ok':
                        transinfo = 'ok'
                    else:
                        transinfo = 'atmerror'
            else:
                if transsum > cardcashlimit: 
                    transstatus = "reject"
                    transinfo = "cardcashlimit"
                if transsum > accamount: 
                    transstatus = "reject"
                    transinfo = "proddetlimit"  
                if transsum <= cardcashlimit and transsum <= accamount:
                    transstatus = choice(['ok','error'])
                    if transstatus == 'ok':
                        transinfo = 'ok'
                    else:
                        transinfo = 'atmerror'
        else:
            cardid=0
            cardnumber=0
            transsum = int(accamount)+50000
            transstatus = "ok"
            transinfo = 'ok'
        cursor.execute('SELECT MAX(TermID),MIN(TermID) FROM [TRANSData].[TERMINAL]')
        data = cursor.fetchone()
        maxtermid = data[0]
        mintermid = data[1]
        terminalid = randint(mintermid,maxtermid)
        transdate = strftime("%d.%m.%Y %H:%M:%S",gmtime())
        transcur = choice(['rub','eur','usd','kzt'])
        transtype = randint(0,5)

        fulltrans = {'TransID':transid,'CardID':cardid,'AccountID':accountid,'TermID':terminalid,'TransStatus':transstatus,'TransDate':transdate,'TransSum':transsum,'TransCurrency':transcur,'TransType':transtype,'TransInfo':transinfo,'TransParam1':'','TransParam2':'','TransParam3':'','TransParam4':''}
        que_result = rabbitmq_add('trans_mq','t_mq',json.dumps(fulltrans,ensure_ascii=False),'application/json','trans_mq')
        fullarr.append(fulltrans)
        maxtrans+=1
    print fullarr
    return make_response(jsonify({'Ratatoskr':fullarr}),200)


if __name__ == '__main__':
    app.worker_main()


from celery import Celery
from celery.task.control import inspect
from time import sleep
from time import gmtime, strftime,strptime
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
#import celeryconfig
from random import randint,choice
#import transgen
from time import gmtime, strftime

app = Celery(backend='amqp://',broker='redis://localhost/0', celery_event_queue_ttl = 300)
"""broker='amqp://guest:guest@localhost:5672//'"""



@app.task(trail=True)
def add(x, y):
	return x + y

@app.task
def publish(x):
	publish.apply_async(args=[x],queue='android_mq',routing_key='android_mq')
	return x

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
       #return 'Succed adding to rabbitmq'
    except Exception:
        return 'Failed adding to rabbitmq'

@app.task(trail=True)
def mysql_add():
    db_='thebankfront'
    db = MySQLdb.connect(host="172.28.104.170", port = 3306, user="rusrat",passwd="Orion123", db=db_)
    cur = db.cursor()
    query = "SELECT * FROM customers where PhotoId > 0"
    cur.execute(query)
    list_of_images = []
    for row in cur.fetchall():
        list_of_images.append(int(row[26]))
    return list_of_images

@app.task(trail=True)
def mysql_b_history_ins(db_,input_data):

    db = MySQLdb.connect(host="172.28.104.170", port = 3306, user="rusrat",passwd="Orion123", db=db_)
    cur = db.cursor()
    variables = [str(input_data["beacon_uuid"]),input_data["major"],input_data["minor"],input_data["spot_id"],input_data["detection_dttm"],input_data["detection_lvl"]]
    
    query = "INSERT INTO `ratatoskr`.`B_HISTORY` (`BEACON_UUID`, `MAJOR`, `MINOR`, `SPOT_ID`, `DETECTION_DTTM`, `DETECTION_LVL`) VALUES ("+str(variables)[1:-1]+");"
    cur.execute(query)
    db.commit()
    return query

@app.task(trail=True)
def mysql_select(db_,select_, from_, where_):
    db = MySQLdb.connect(host="172.28.104.170", port = 3306, user="rusrat",passwd="Orion123", db=db_,use_unicode = True,charset='UTF8')
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
    db = pymssql.connect(server = '172.28.106.17',user = 'rtdm',password = 'Orion123',database=schema_,charset='UTF8')
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

@app.task
def send_mq(arg):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='android_mq', durable = True,)
    channel.exchange_declare(exchange = 'android_mq',exchange_type='topic', durable = True)
    channel.basic_publish(exchange='',routing_key='android_mq',body=arg)
    connection.close()
    return str('Message sent: '+arg)

@app.task
def test_work(x):
	for i in range(1,10000):
		x = x+1
	return x

@app.task
def get_offer(cid,rtdm_ip):
	payload = {"clientTimeZone":"Europe/London","version":1,"inputs":{"CustomerID":cid,"ProdCatCode":"Leggings"}}
	r = requests.post(rtdm_ip, json = payload)
	resp = r.json()
	return resp




@app.task(trail=True)
def call_rtdm(dns,event,inputs):
    rtdm_addr = "http://"+dns+"/RTDM/rest/runtime/decisions/"+event
    payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
    r = requests.post(rtdm_addr, json = payload)
    resp = r.json()
    #resp = str(payload)+str(r.content)
    print 'call_rtdm is succeed'
    return resp


@app.task(trail=True)
def call_service(service,inputs):
    service_adr = "http://172.28.104.171:5000/"+service
    payload = inputs
    r = requests.post(service_adr, json = payload)
    resp = r.json()
    #resp = str(payload)+str(r.content)
    print 'call_service '+service +' is succeed'
    return resp


@app.task(trail=True)
def post(maxevent):
    i = 1
    global maxid 
    maxid = maxevent  
    while i==1:
        sleep(7)
        Out =[] 
        try:
            db = psycopg2.connect(host="172.28.104.180", port = 5432, user="testuser",password="password", dbname="FaceStreamRecognizer")
        except Exception as e:
            return e
        cur = db.cursor()
        query = "SELECT event_id,event_time,similarity,first_name,last_name,middle_name,event_photo,birth_date FROM event WHERE event_id >"+str(maxid)
        cur.execute(query)
        #query2 = "SELECT count(*) FROM event WHERE event_id >"+str(maxid)
        #cur.execute(query2)
        #data = cur.fetchone()
        #print "count = "+str(data[0])
        for row in cur.fetchall():
            cur2 = db.cursor()
            timequery = "SELECT MAX(event_time) FROM event WHERE middle_name = '"+str(row[5])+"' and event_id <> "+str(row[0])
            cur2.execute(timequery)
            data = cur2.fetchone()
            lasttimereq = data[0]        
            payload1 = {"id":row[5],"image":base64.b64encode(str(row[6]))}
            r1 = requests.put("http://172.28.104.171:5000/active_queue?option=terminal",json = payload1)
            payload2 = {"name":row[3],"surname":row[4],"middlename":"","dob":str(row[7]),"id":int(row[5]),"status":"processing","reason":"unknown","location":"camera","area":"retail"}
            r2 = requests.post("http://172.28.104.171:5000/active_queue",json = payload2)
                #inputs = {"IndivID":int(row[5]),"Channel":"Luna","PhotoDT":str(row[1].isoformat(sep='T')),"param1":"","param2":"","param3":0,"param4":0}
                #k = call_rtdm("172.28.106.245","lunaevent",inputs)
                #print k,inputs
            date_s = datetime.strftime(datetime.now(),"%m/%d/%y %H:%M:%S")
            date_e = datetime.strftime(lasttimereq,"%m/%d/%y %H:%M:%S")
            date_ss = datetime.strptime(date_s,"%m/%d/%y %H:%M:%S")
            date_ee = datetime.strptime(date_e,"%m/%d/%y %H:%M:%S")
            print "difference = "+str((date_ss-date_ee).seconds)
            if datetime.now() - lasttimereq >= timedelta(minutes=5) and row[2] > 85.00:
                payload3 = {"cid":int(row[5]),"scenario":"","beaconid":"","spotid":2,"spotname":"The Store","time":str(datetime.now().isoformat(sep='T')),"trigger":"Luna"}
                #r3 = requests.post("http://172.28.104.171:5000/geotrigger",json = payload3)
                r3= call_rtdm.apply_async(("172.28.106.245","geomainevent",payload3),retry=False)
                Out.append({"event_id":row[0],"event_time":str(row[1]),"similarity":row[2],"first_name":row[3],"last_name":row[4]})
        query2 = "SELECT MAX(event_id) FROM event"
        cur.execute(query2)
        data = cur.fetchone()
        maxid = data[0]
        print Out,maxid




@app.task(trail=True)
def facetztask(cid):
    url = "https://api.facetz.net/v2/facts/user.json?key=51af6192-c812-423d-ae25-43a036804632&query={%22user%22:{%22id%22:%22"+cid+"%22},%22ext%22:{%22exchangename%22:%22sas_demo%22}}"
    k =1 
    while k == 1:
        sleep(10)
        Formatted = []
        r = requests.get(url)
        Formatted.append({"id":r.json()['id']})
        i=1
        for el in r.json()['visits']:
            formatted_el = {}
            formatted_el['number'] = i
            formatted_el['ts'] = datetime.strftime(datetime.fromtimestamp(el['ts']/1000),"%Y-%m-%d %H:%M:%S")
            formatted_el['url'] = urllib.unquote(el['url'])
            Formatted.append(formatted_el)
            i+=1
        que_result = rabbitmq_add('facetz_mq','f_mq',json.dumps(Formatted,ensure_ascii=False),'application/json','facetz_mq')
        print Formatted



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
        cursor.execute('SELECT Max(TransID) FROM [TRANSData].[TRANSACTION]')
        data = cursor.fetchone()
        maxtrans = int(data[0])
        cursor.execute('SELECT MAX(AccountID),MIN(AccountID) FROM [DataMart].[ACCOUNT]')
        data = cursor.fetchone()
        maxacc = int(data[0])
        minacc = int(data[1])
        while i == 0 :
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
                #cursor.execute('SELECT MAX(CardID),MIN(CardID) FROM [DataMart].[Card]')
                #data = cursor.fetchone()
                #maxcardid = data[0]
                #mincardid = data[1]
                #cardid = randint(mincardid,maxcardid)
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
                #cards =0
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
            #terminaltype = choice(['atm','pos','mobapp','onlinebank'])
            #mcc = randint(1000,9999)

            fulltrans = {'TransID':transid,'CardID':cardid,'AccountID':accountid,'TermID':terminalid,
'TransStatus':transstatus,'TransDate':transdate,'TransSum':transsum,'TransCurrency':transcur,'TransType':transtype,
'TransInfo':transinfo,'TransParam1':'','TransParam2':'','TransParam3':'','TransParam4':''}
            que_result = rabbitmq_add('trans_mq','t_mq',json.dumps(fulltrans,ensure_ascii=False),'application/json','trans_mq')
            print 'id= '+transgen.request.id
            fullarr.append(fulltrans)
            maxtrans+=1
            #i+=1
        return fullarr
    except Exception as e:
        return e


if __name__ == '__main__':
    app.worker_main()


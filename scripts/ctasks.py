from celery import Celery
from celery.task.control import inspect
from time import sleep
import pika
import requests
import MySQLdb
#import celeryconfig

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
       return 'Succed adding to rabbitmq'
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
	r = requests.post(rtdm_ip,json = payload)
	resp = r.json()
	return resp

@app.task
def call_rtdm(dns,event,inputs):
    rtdm_addr = "http://"+dns+"/RTDM/rest/runtime/decisions/"+event
    payload = {
"clientTimeZone":"Europe/Moscow",
"version":1,
"inputs":"inputs"}
    r = requests.post(rtdm_addr,json = payload)
    resp = r.json()
    return {"y":"h"}


if __name__ == '__main__':
    app.worker_main()


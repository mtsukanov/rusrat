#!/var/beacon/clr/bin/python 
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         RATATOSKR WEB SERVICES 0.01                                                                                                                                       #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
###################################################################t##########################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF LIBRARIES                                                                                                                                             #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################



from flask import Flask, jsonify, abort,make_response,request,json 
from celery import Celery
from celery.result import ResultBase, AsyncResult
from time import gmtime, strftime,strptime
from ctasks import send_mq,add,rabbitmq_add,mysql_add,mysql_select,mysql_b_history_ins,call_rtdm
from datetime import timedelta,datetime
from flask import make_response, request, current_app
from functools import update_wrapper
from random import randint,choice
from transgen import transgen
from ctasks import call_rtdm
#import celeryconfig
#import  ctasks
import datetime
import time
import pika
import requests
import MySQLdb
import pymssql
#import transgen
#from celery.task.control import revoke
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF GLOBAL VARIABLES                                                                                                                                         #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################


atm_status = True

tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web', 
        'done': False
    }
]


server_ip = '172.28.104.171'
rid = ''
req_image = ''
list_of_images = []
lunaresp = 'never used'
lunaans = 'never used'


app_server = "ruscilab"
web_server = "labinso.sas.com"
soa_server = "172.28.104.171:5000"
sync = 1
freq_in = 30
freq_out = 5
freq_sync = 180


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF COMMON FUNCTIONS                                                                                                                                         #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################


#Head decorator

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True, content=None):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Content-Type'] = content

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Headers'] = headers
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

#Celery initiator
def make_celery(app):
    celery = Celery(app.import_name)
    celery.config_from_object('celeryconfig')
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


def get_client(cid):
    db = MySQLdb.connect(host="172.28.104.170", port = 3306, user="rusrat",passwd="Orion123", db="thebankfront",use_unicode = True,charset='UTF8')
    cur = db.cursor()
    query = "SELECT * FROM customers where CID="+str(cid)
    cur.execute(query)
    photoid = 0
    for row in cur.fetchall():
        output = row
    
    return output

def get_cid_byphotoid(photoid):
    db = MySQLdb.connect(host="172.28.104.170", port = 3306, user="rusrat",passwd="Orion123", db="thebankfront")
    cur = db.cursor()
    query = "SELECT * FROM customers where PhotoID="+str(photoid)
    cur.execute(query)
    cid = 0
    for row in cur.fetchall():
        cid = row[0]
    
    return cid

    

def get_all_clients():
    db = MySQLdb.connect(host="172.28.104.170", port = 3306, user="rusrat",passwd="Orion123", db="thebankfront")
    cur = db.cursor()
    query = "SELECT * FROM customers where PhotoId > 0"
    cur.execute(query)
    list_of_images = []
    for row in cur.fetchall():
        list_of_images.append(int(row[26]))
    return list_of_images


#Server start
app = Flask(__name__)


app.config.update(
 
    BROKER_URL='amqp://guest:guest@localhost:5672//'
 

)

celery = make_celery(app)




"""
@app.route('/', methods=['GET'])
def get_tasks():
    return jsonify({'tasks': tasks})

@app.route('/mclient_key=<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
    return jsonify({'task': task[0]})
"""
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF JUNK SERVICES                                                                                                                                            #
#        
#source /var/beacon/clr/bin/activate
#cd /var/beacon/clr/scripts                                                                                                                                                                 #
#############################################################################################################################################################################################

@app.route('/params', methods=['GET'])
def get_offer():
    
    cid_str = request.args.get('mclient_id')
    rtdm_ip = request.args.get('rtdm_ip')
    cid = int(cid_str)

    rtdm_path = "/RTDM/rest/runtime/decisions/SAS_for_Retail_Best_Retail_Oriented_Product_Promotion"
    rtdm_url="http://"+rtdm_ip+rtdm_path
    payload = {"clientTimeZone":"Europe/London","version":1,"inputs":{"CustomerID":cid,"ProdCatCode":"Leggings"}}
    r = requests.post(rtdm_url,json = payload)
    resp = r.json()
   
    output = resp['outputs']
    title = output['Offer2']
    description = output['Offer2URL']
    answer = [{'title':title,'description':description}]


    return jsonify({'offer':answer})






@app.route('/task', methods=['POST'])
def create_taskp():
    if not request.json or not 'title' in request.json:
        abort(400)
    new_task = {
        "opcode":"i",
        "Test_ID": tasks[-1]["id"] + 1,
        "Test_String": request.json["title"],
        "description": request.json.get('description', ""),
        "done": False

    }
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='android_mq')
    channel.basic_publish(exchange='',routing_key='android_mq',body=str(new_task))
    tasks.append(new_task)
    msg = jsonify({'task': new_task}), 201
    #ctasks.publish(new_task)
    connection.close()
    return msg



@app.route('/a', methods=['POST'])
def create_task():
    if not request.json or not 'title' in request.json:
        abort(418)
    ntime = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    new_task = {
    "opcode": "i",
   # "Test_ID": tasks[-1]["id"] + 1,
	"Test_ID": "shit",
   # "": ntime,
	#"Test_String": request.json["title"]}
	"Test_String": "Fuck this"}

    x = str(new_task)
    x = x.replace("'",'"')
    result = send_mq.delay(x)
    return 'Success'


@app.route('/send', methods=['POST'])
def create_task2():
    Str = request.json["client_key"]
    status = 1
    #msg = Str + 1
    return jsonify({'Response':status})

@app.route('/bulk', methods=['POST'])
def create_load():
    cid = request.json["mclient_id"]
    rtdm_ip = request.json["rtdm_ip"]
    rtdm_path = "/RTDM/rest/runtime/decisions/SAS_for_Retail_Best_Retail_Oriented_Product_Promotion"
    rtdm_url="http://"+rtdm_ip+rtdm_path
    payload = {"clientTimeZone":"Europe/London","version":1,"inputs":{"CustomerID":cid,"ProdCatCode":"Leggings"}}
    r = requests.post(rtdm_url,json = payload)
    resp = r.json()
    o = r.content
       
    return o




@app.route('/nbo', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def get_nbo_req():
    
    cid = request.json["cid"]
    channel = request.json["channel"]
    context = request.json["context"]
    device = request.json["device"]
    regtime = request.json["regtime"]
    reqtime = request.json["reqtime"]
    timezone = request.json["timezone"]
    param1 = request.json["param1"]
    param2 = request.json["param2"]
    param3 = request.json["param3"]
    param4 = request.json["param4"]
    param5 = request.json["param5"]
    param6 = request.json["param6"]
    param7 = request.json["param7"]
    
    inputs = {"cid":cid,"channel":channel,"context":context,"device":device,"regtime":regtime,"reqtime":reqtime,"timezone":timezone,"param1":param1,
"param2":param2,"param3":param3,"param4":param4,"param5":param5,"param6":param6,"param7":param7}
    

    dns = "172.28.106.245"
    event = "frontmainevent"
    #event = "SAS_Activity_echo_string"
    #inputs = {"in_string":"I rule"}
    rtdm_addr = "http://"+dns+"/RTDM/rest/runtime/decisions/"+event
    payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
    r = requests.post(rtdm_addr,json = payload)
    resp = str(r)
    return make_response(jsonify({"A":r.json()}),201)

"""
def call_rtdm(dns,event,inputs):
    rtdm_addr = "http://"+dns+"/RTDM/rest/runtime/decisions/"+event
    payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
    r = requests.post(rtdm_addr,data = payload)
    #resp = r.json()
    resp = str(rtdm_addr)+str(r.headers)+str(r.text)
    return resp
"""

@app.route('/test_rtdm', methods=['POST'])
def test_rtdm():
    rtdm_ip = "172.28.106.245"
    rtdm_path = "/RTDM/rest/runtime/decisions/SAS_Activity_echo_string"
    rtdm_url="http://"+rtdm_ip+rtdm_path
    payload = {"clientTimeZone":"Europe/London","version":1,"inputs":{"in_string":"I rule"}}
    r = requests.post(rtdm_url,json = payload)
    resp = r.json()
    o = r.content
       
    return o


@app.route('/communication', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def test_rednet():
    #global req_path
    try:
        login =  request.json["login"] 
        login = request.json["login"]
        psw = request.json["psw"]
        phones = request.json["phones"]
        mes = request.json["mes"]
        sender = request.json["sender"]
        try:
            subj = request.json["subj"] 
        except:
            subj = 'undefined'
        try:
            mail = request.json["mail"] 
            req_path = "https://smsc.ru/sys/send.php?login="+login+"&psw="+psw+"&phones="+phones+"&mes="+mes+"&sender="+sender+"&subj="+subj+"&mail="+str(mail)
        except Exception:
            req_path = "https://smsc.ru/sys/send.php?login="+login+"&psw="+psw+"&phones="+phones+"&mes="+mes+"&sender="+sender    
        #param1 = request.json["param1"]
        #param2 = request.json["param2"]
        #param3 = request.json["param3"]
        #param4 = request.json["param4"] 
    except Exception:
        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415)           
    try:
        r = requests.get(req_path) 
        answer = r.content
    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'Ratatoskr':'connection error'}),111)   
    return make_response(jsonify({'Ratatoskr':'Success!'}),200)
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /MOBILE_GET                                                                                                                                              #o
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/mobile_get', methods=['GET'])

def mobile_get_all():
    cid = request.args.get('client_id')
    context = "sync"
    channel = "mobile"
    device = "mobile"
    regtime = "2012-04-23T18:25:43.511Z"
    reqtime = "2012-04-23T18:25:43.511Z"
    timezone = "1"
    param1 ="1"
    param2 = "1"
    param3 = 1
    param4 = 1
    param5 = ["1"]
    param6 = [1]
    param7 = True
    resp = None
    Clients =[]
    Offers = []
    Products = []
    Transactions = []
    WIFI = []
    GPS = []
    Beacon = []
    if cid is None:
        query_customers = 'Login is not null'
        query_tranz = None
        query_offers = None
        query_prods = 't1.PID = t2.PID'
        query_beacon = None
        query_wifi = None
        query_gps = None
        try:
            result_mysql_offers = mysql_select('thebankfront',None,'offers',query_offers)
        except Exception:
            response = {"Ratatoskr":"Something wrong with offline offers"}
            return make_response(jsonify(response),500)
    else:
        try:
            dns = "http://"+server_ip+":5000/nbo"
            inputs = {"cid":int(cid),"channel":channel,"context":context,"device":device,"regtime":regtime,"reqtime":reqtime,"timezone":timezone,"param1":param1,
"param2":param2,"param3":param3,"param4":param4,"param5":param5,"param6":param6,"param7":param7}
        
            dns = "172.28.106.245"
            event = "frontmainevent"

            rtdm_addr = "http://"+dns+"/RTDM/rest/runtime/decisions/"+event
            payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
            r = requests.post(rtdm_addr,json = payload)
            resp = r.json()
            i = 0
            for row in resp["outputs"]["offercode"]:
                #offer = {'i':i}
                offer = {'i':i,'clientid': resp["outputs"]["cid"], 'description':resp["outputs"]["briefdetails"][i], 'generated_dttm':'','image':'','offerid':resp["outputs"]["offercode"][i],'payment':resp["outputs"]["payment"][i],'priority':resp["outputs"]["prio"][i],'rate':resp["outputs"]["rate"][i],'recieved_dttm':'','secret':'','sent_dttm':'','sum':resp["outputs"]["amount"],'termination_dttm':'','type':'financial','visibility':1}
                Offers.append(offer)
                i += 1
            return make_response(jsonify({'Offers':Offers, 'OUTPUT':resp["outputs"]}),201) 
                  
            
        except Exception as e:
            response = {"Ratatoskr":"R:"+str(e)}
            return make_response(jsonify(response),500)
      
        try:
            resp = r.json()
            response = {"Ratatoskr":"Try was OK calling NBO:"+str(resp)+str(dns)}
            return make_response(jsonify(response),500)
        except Exception:
            response = {"Ratatoskr":"Error calling NBO:"+str(Exception)+str(dns)}
            return make_response(jsonify(response),500)

        query_customers = 'Login is not null AND CID ='+cid
        query_tranz = 'CID ='+cid
        #query_offers = 'CustomerID ='+cid
        query_prods = 't1.PID = t2.PID and t1.CID ='+cid
        query_beacon = None
        query_wifi = None
        query_gps = None
    try:
        result_mysql_sel = mysql_select('thebankfront',None,'customers',query_customers)
        result_mysql_tranz = mysql_select('thebankfront',None,'transhistory',query_tranz)
        #result_mysql_offers = mysql_select('thebankfront',None,'offers',query_offers)
        result_mysql_prods = mysql_select('thebankfront','t1.CID, t2.PName, t2.PDesc, t1.PAmount,t2.PImage, t1.PRate, t1.PPayment, t2.PID, t1.PStart, t1.PEnd','customers as t0 inner join productdetails as t1 inner join products as t2',query_prods)
        result_mysql_beacon = mysql_select('ratatoskr',None, 'BEACONS',query_beacon)
        result_mysql_wifi = mysql_select('ratatoskr',None, 'WIFI',query_wifi)
        result_mysql_gps = mysql_select('ratatoskr',None, 'GPS',query_gps)
    except Exception:
        response = {"Ratatoskr":"Your request made me sick. Either parameters were unexpected or DB schema was cruely changed. Anyway this won't work, sorry for inconvenience."}
        return make_response(jsonify(response),500)

#GET CLIENTS
    for row in result_mysql_sel:
        client = {}
        client["clientid"] = row[0]
        client["clientimage"]=""
        client["name"] = row[1]
        client["surname"] = row[3]
        client["email"] = row[16]
        client["phone"] = row[5]
        client["login"] = row[27]
        client["password"] = row[28]
        client["loyaltyscore"] = row[29]
        Clients.append(client)
#GET OFFERS
    for row in result_mysql_offers:
        offer = {}
        offer["clientid"] = row[0]
        offer["offerid"] = row[1]
        offer["name"] = row[3]
        offer["duration"] = 12
        offer["type"] = 'financial'#row[9]
        offer["description"] = row[4]
        offer["sum"] = row[6]
        #offer["image"] = row[5]
        offer["image"] = ""
        offer["rate"] = row[7]
        offer["payment"] = row[19]
        offer["secret"] = row[15]
        offer["visibility"] = row[16]
        offer["priority"] = row[12]
        offer["generated_dttm"] = row[17]
        offer["recieved_dttm"] = row[0]
        offer["termination_dttm"] = row[18]
        offer["sent_dttm"] = int(round(time.time()*1))
        Offers.append(offer)
#GET PRODUCTS
    for row in result_mysql_prods:
        product = {} 
        product["clientid"] = row[0]
        product["name"] = row[1]
        product["type"] = 'financial'#row[9]
        product["description"] = row[2]
        product["sum"] = row[3]
        product["duration"] = 12
        #product["image"] = row[4]
        product["image"] = ""
        product["rate"] = row[5]
        product["payment"] = row[6]
        product["productid"] = row[7]
        product["purchased_dttm"] = str(row[8])#str(row[8].day)+"."+str(row[8].month)+"."+str(row[8].year)
        product["exparation_dttm"] = str(row[9])

        Products.append(product)

#GET SETTINGS

    Settings = []
    setting =    {
    "app_server" : app_server,
    "web_server" : web_server,
    "soa_server" : "172.28.104.171:5000",
    "sync" : sync,
    "freq_in" : freq_in,
    "freq_out" : freq_out,
    "freq_sync" : freq_sync}
    Settings.append(setting)
#GET TRANSACTIONS
    for row in result_mysql_tranz:
        tranz = {}
        tranz["tranid"] = row[0]
        tranz["agent"] = row[1]
        tranz["sum"] = row[4]
        tranz["tran_dttm"] = "1400000"
        tranz["clientid"] = row[2]
        Transactions.append(tranz)
#GET WIFI
    for row in result_mysql_wifi:
        wifi = {}
        wifi["id"] = row[0]
        wifi["ssid"] = row[1]
        wifi["level"] = row[3]
        WIFI.append(wifi)
#GET BEACONS
    for row in result_mysql_beacon:
        beacon = {}
        beacon["uuid"] = row[0]
        beacon["major"] = row[1]
        beacon["minor"] = row[2]
        beacon["rssi"] = row[7]
        Beacon.append(beacon)
#GET GPS
    for row in result_mysql_gps:
        gps = {}
        gps["id"] = row[0]
        gps["latitude"] = row[1]
        gps["longitude"] = row[3]
        GPS.append(gps)

   
    response = {"Clients":Clients,"Products":Products,"Offers":Offers,"Transactions":Transactions,"Settings":Settings,"GPS":GPS,"WIFI":WIFI,"BEACONS":Beacon}

    return make_response(jsonify({"Ratatoskr":response}),200)

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /GETRESPONSEHISTORY                                                                                                                                             #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/getresponsehistory', methods=['GET','POST', 'OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def getresponsehistory():
    cid = request.args.get('cid')
    #cid = 1
    conn = pymssql.connect(server = '172.28.106.17',user = 'rtdm',password = 'Orion123',database='CIDB')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM RTData.RESPONSE_HISTORY where CID='+str(cid))
    data = cursor.fetchall()
    Response = []
    for row in data:
        response = {'cid':row[0],'channel':row[1],'context':row[2],'device':row[3],'offerid':row[4],'resptype':row[5],'respname':row[6],'respid':row[7],'resptime':row[8],'resptimestr':row[9],'param1':row[10],'param2':row[11],'param3':row[12],'param4':row[13],'param5':row[14],'param6':row[15],'param7':row[16]}
        Response.append(response)
    return make_response(jsonify({'Ratatoskr':Response}),200)


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /MOBILE_POST                                                                                                                                             #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/mobile_post', methods=['POST'])
def mobile_post_all():
    try:
        sys = request.json['sys']
        wifi = request.json['wifi']
        beacon = request.json['beacon']
        gps = request.json['gps']
        trigger =  request.json['trigger']
        message = {"sys":sys,"wifi":wifi,"gps":gps,"beacon":beacon, "trigger": trigger,"opcode": "i"}
        result_mq = rabbitmq_add.delay('geo_mq','_mq',json.dumps(message, ensure_ascii=False),'application/json','geo_mq')
        return make_response(jsonify({'Ratatoskr':'request processed'}),201)
    except Exception:
        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415)

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /SYNC_UPDT                                                                                                                                            #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/rtdm_test', methods=['POST'])
def testis():
    zayka = ''
    zayka = str(request)
    return make_response(jsonify({'Ratatoskr':zayka}),418)
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /SYNC_UPDT                                                                                                                                            #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/sync_updt', methods=['POST'])
def sync_updt():

    global app_server
    global web_server
    global soa_server
    global sync
    global freq_in
    global freq_out
    global freq_sync
    try:
        app_server = request.json['app_server']
        web_server = request.json['web_server']
        soa_server = request.json['soa_server']
        sync = request.json['sync']
        freq_in = request.json['freq_in']
        freq_out = request.json['freq_out']
        freq_sync = request.json['freq_sync']

        Settings =     {
    "app_server" : app_server,
    "web_server" : web_server,
    "soa_server" : soa_server,
    "sync" : sync,
    "freq_in" : freq_in,
    "freq_out" : freq_out,
    "freq_sync" : freq_sync}

        return make_response(jsonify({'Ratatoskr':'request processed'}),201)
    except Exception:

        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415)

@app.route('/sync_updt', methods=['GET'])
def sync_updt2():

    Settings =     {
    "app_server" : app_server,
    "web_server" : web_server,
    "soa_server" : soa_server,
    "sync" : sync,
    "freq_in" : freq_in,
    "freq_out" : freq_out,
    "freq_sync" : freq_sync}

    return make_response(jsonify(Settings),200)

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /OFFER_ACCEPT                                                                                                                                            #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
    
@app.route('/offer_accept', methods=['OPTIONS'])
@crossdomain(origin='*',content = 'application/json',headers = 'Content-Type')
def send_options2():
    return make_response(jsonify({'Ratatoskr':'POST, GET'}))





@app.route('/offer_accept', methods=['POST','GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def offer_accept():
    try: 
        visibility = request.json['visibility']
        option = 0
    except:
        option = 1
        #return make_response(jsonify({'Ratatoskr':'response you are looking for'}),518) 
    if option == 0:    
        try:
            context = request.json['type']
            visibility = request.json['visibility']
            priority = request.json['priority']
            accepted_dttm = request.json['accepted_dttm']
            cid = request.json['clientid']
            offerid = request.json['offerid']
        
            channel = 'mobile_app'
            resptype = 'direct'
            device = 'in future releases'
                   
            if (priority == 1): 
                respname = "Accepted"
                respid = 1
            elif (visibility == 0 and priority == 0):
                respname = "Denied"
                respid = 2
            else:
                respname = "undefined"
                respid = None
    
            inputs = {"cid":cid,
"channel": channel,
"context" : context,
"device" : device,
"offerid" : offerid,
"resptype" : resptype,
"respname" : respname,
"respid" : respid,
"resptime" : accepted_dttm,
"resptimestr" : str(accepted_dttm),
"param1" : None,
"param2" : None,
"param3" : None,
"param4" : None,
"param5" : None,
"param6" : None,
"param7" : None}
            #return make_response(jsonify({'Ratatoskr':'request processed'}),201)
        except Exception:
            return make_response(jsonify({'Ratatoskr':'error processing mobile'}),415)       
    else:
        try:
            cid = request.json['cid']

            channel = request.json['channel']
            context = request.json['context']
            device = request.json['device']

            offerid = request.json['offerid']
            resptype = request.json['resptype']
            respname = request.json['respname']
            respid = request.json['respid']

            resptime = request.json['resptime']
            param1 = request.json['param1']
            param2 = request.json['param2']
            param3 = request.json['param3']
            param4 = request.json['param4']
            param5 = request.json['param5']
            param6 = request.json['param6']
            param7 = request.json['param7']
        except Exception as e:
            return make_response(jsonify({'Ratatoskr':'input data is corrupted','e':str(e)}),406) 
        try:
            inputs = {"cid":cid,
"channel": channel,

"context" : context,
"device" : device,
"offerid" : offerid,
"resptype" : resptype,
"respname" : respname,
"respid" : respid,
"resptime" : resptime,
"resptimestr" : resptime,
"param1" : param1,
"param2" : param2,
"param3" : param3,
"param4" : param4,
"param5" : param5,
"param6" : param6,
"param7" : param7
}
            #return make_response(jsonify({'Ratatoskr':inputs}),201)
            
        except Exception:
            return make_response(jsonify({'Ratatoskr':'error processing site'}),418)  
    #result = call_rtdm("172.28.106.245","responsehistoryevent",inputs)
    try:
        blat = call_rtdm.apply_async(("172.28.106.245","responsehistoryevent",inputs),retry=True)
        time.sleep(5)       
        return make_response(jsonify({'Ratatoskr':blat.status}),201)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'Some problem occures in delay()'}),418)  
    #return make_response(jsonify(result),201)
     
        #[v for v in result.collect-()
        #     if not isinstance(v, (ResultBase, tuple))]
        #return make_response(str(v[1]),201)


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /LAUNCH                                                                                                                                            #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/launch', methods=['POST'])
def launch():
    try:
        clientid = request.json['clientid']
        login = request.json['login']
        password = request.json['password']
        scenario = request.json['scenario']
        Status = {'clientid':clientid,'login':login,'password':password,'scenario':scenario}

        return make_response(jsonify({'Ratatoskr':'request processed'}),201)
    except Exception:

        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415)



taskid = 0
status = ''
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /TRANSACTION GENERATOR                                                                                                                                        #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/transgenerate', methods=['GET','POST'])
def transgenerate():
    global taskid
    global status 
    try:
        param = request.json['param']
        if param == True:      
            taskid=transgen.delay()
            time.sleep(2)
            status = taskid.status
            while status == 'SUCCESS':
                taskid=transgen.delay()
                time.sleep(2)
                status = taskid.status
            #taskid = transgen.delay().id
            #print transgen.AsyncResult(transgen.request.id).state
            return make_response(jsonify({'Ratatoskr':'Task '+str(taskid)+' has been added to RabbitMQ. Status: '+status}),200)
        else:
            taskid.revoke(terminate=True)
            time.sleep(2)
            status = taskid.status
            return make_response(jsonify({'Ratatoskr':'Task '+str(taskid)+' has been terminated. Status: '+status}),200)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':e}),415)

@app.route('/mssql', methods=['GET','POST'])
def mssql():
    try:
        accountid = 13
        conn = pymssql.connect(server = '172.28.106.17',user = 'rtdm',password = 'Orion123',database='CIDB')
        cursor = conn.cursor()
        cursor.execute('SELECT AccountType FROM [DataMart].[ACCOUNT] where AccountID='+str(accountid))
        data = cursor.fetchone()
        acctype = data[0]
        cursor.execute('SELECT AccountAmount,ProdDetID FROM [DataMart].[ACCOUNT] where AccountID='+str(accountid))
        data = cursor.fetchone()
        accamm = data[0]
        prodid = data[1]
        cursor.execute('SELECT ProdDetLimit FROM [DataMart].[PRODUCTDETAILS] where ProdDetID='+str(prodid))
        data = cursor.fetchone()
        prodlmit = data[0]
        print 'accamm= '+str(accamm)+", prod= "+str(prodlmit)
        return make_response(jsonify({'Ratatoskr':'ok'}),200)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':e}),415)
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /ACTIVE_QUEUE                                                                                                                                     #
#                                                                                                                                                                                           #
########################################################################################################################################################
Client_list = []
Terminal =[]
client_cnt=1
updated = 0

@app.route('/active_queue', methods=['POST','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def active_queue():
    global client_cnt
    global Client_list
    global Terminal
    global updated
    global upd
   
    try:
        client_fname = request.json['name']
        client_lname = request.json['surname']
        client_mname = request.json['middlename']
        client_dob = request.json['dob']
        client_id = request.json['id']
        client_status = request.json['status']
        client_reason = request.json['reason']
        client_location = request.json['location']
        client_area = request.json['area']
    except:
        return make_response(jsonify({'Ratatoskr':'Incorrect input'}),415) 
    if Client_list == []:
        Client_profile = {'client_num':str(client_cnt),'time':strftime("%d.%m.%Y %H:%M:%S",gmtime()),'id':client_id,'name':client_fname,'last_name':client_lname,'middle_name':client_mname,'dob':client_dob,'status':client_status,'reason':client_reason,'location':client_location,"area":client_area}
        Client_list.append(Client_profile)
        client_cnt+=1  
    else:
        updated = 0
        for obj in Client_list:
            if obj['id'] == client_id:
                obj['location'] = client_location
                obj['reason'] = client_reason
                obj['time'] = strftime("%d.%m.%Y %H:%M:%S",gmtime())
                updated = 1 
        if updated == 0:
            Client_profile = {'client_num':str(client_cnt),'time':strftime("%d.%m.%Y %H:%M:%S",gmtime()),'id':client_id,'name':client_fname,'last_name':client_lname,'middle_name':client_mname,'dob':client_dob,'status':client_status,'reason':client_reason,'location':client_location,"area":client_area}
            Client_list.append(Client_profile)
            client_cnt+=1     
    return make_response(jsonify({'Ratatoskr':'good','TEST': Client_list}),200)

@app.route('/act', methods=['GET'])
def rururu(): 
    return make_response(jsonify({'TEST': Client_list}),200)

@app.route('/active_queue', methods=['GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def CList():
    global Client_list
    currdate = strftime("%d.%m.%Y %H:%M:%S",gmtime())
    Newcommers = []
    Full = []
    opt = request.args.get('option')
    if (opt is not None):
        if (opt == "new"):
            for obj in Client_list:
                if datetime.datetime.strptime(currdate,'%d.%m.%Y %H:%M:%S') - datetime.datetime.strptime(obj['time'],'%d.%m.%Y %H:%M:%S') < datetime.timedelta(0,10) and obj['location'] == 'terminal':
                    Newcommer_profile = {'client_num':obj['client_num'],'time':obj['time'],'id':obj['id'],'name':obj['name'],'last_name':obj['last_name'],'middle_name':obj['middle_name'],'dob':obj['dob'],'status':obj['status'],'reason':obj['reason'],'location':obj['location'],'area':obj['area'],'photo':get_client(obj['id'])[25].replace(" ","+")}
                    Newcommers.append(Newcommer_profile)
            return make_response(jsonify({'Ratatoskr':Newcommers}),200)
        if (opt == "full"):
            for obj in Client_list:
                Full_profile = {'client_num':obj['client_num'],'time':obj['time'],'id':obj['id'],'name':obj['name'],'last_name':obj['last_name'],'middle_name':obj['middle_name'],'dob':obj['dob'],'status':obj['status'],'reason':obj['reason'],'location':obj['location'],'area':obj['area'],'photo':get_client(obj['id'])[25].replace(" ","+")}
                Full.append(Full_profile)
            return make_response(jsonify({'Ratatoskr':Full}),200)
        if (opt == "terminal"):
            return make_response(jsonify({'Ratatoskr':Terminal}),200)
    else:
        if Client_list != []:
            return make_response(jsonify({'Ratatoskr':Client_list}),200)
        else:
            return make_response(jsonify({'Ratatoskr':'There are no clients in queue'}),200)


@app.route('/active_queue', methods=['PUT'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def dltclt():
    opt = request.args.get('option')
    if (opt is not None):
        if (opt == "terminal"):
            try:
                client_id = request.json['id']
                client_image = request.json['image']
            except:
                return make_response(jsonify({'Ratatoskr':'Incorrect input'}),415)
            if Terminal == []:
                Terminal_profile = {'client_id':client_id,'client_image':client_image}
                Terminal.append(Terminal_profile)
            else:
                upd = 0
                for obj in Terminal:
                    if obj['client_id'] == client_id:
                        obj['client_image'] = client_image
                        upd = 1 
                if upd == 0:
                    Terminal_profile = {'client_id':client_id,'client_image':client_image}
                    Terminal.append(Terminal_profile)
            return make_response(jsonify({'Ratatoskr':'Success'}),200)
    else:
        try:
            cid = request.json['id']
        except:
            return make_response(jsonify({'Ratatoskr':'No correct id'}),415)
        for i in reversed(range(len(Client_list))):
            if Client_list[i].get('id') == cid:
                Client_list.pop(i)
        return make_response(jsonify({'Ratatoskr':Client_list}),200)
            
            







#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /BEACONS                                                                                                                                                 #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################

@app.route('/beacon_reg', methods=['POST'])
def register_beacon():
    r = request.json
    ntime = int(round(time.time()*1))
    beacon_uuid = str(request.json["beacon_uuid"])
    result_mysql_sel = mysql_select('ratatoskr',None,'BEACONS',None)
    #check if beacon is in DB
    for row in result_mysql_sel:
        if row[0] == beacon_uuid:
            domestic_beacon = True
            r['spot_id'] = int(row[3])
            spot_id = int(row[3])
            break 
        else:
            return make_response(jsonify({'Ratatoskr':'Beacon is not registered (wrong uuid)'}),200)
    #if beacon is in DB, proceed
    result_b_hist_ins=mysql_b_history_ins.delay('ratatoskr',r)
    #create queue for ESP
    major = request.json["major"]
    minor = request.json["minor"]
    detection_dttm = request.json["detection_dttm"]
    detection_lvl = request.json["detection_lvl"]
    message = {"opcode": "i","beacon_uuid":beacon_uuid,'spot_id':spot_id, 'major':major, 'minor':minor,'detection_dttm':detection_dttm,'detection_lvl':detection_lvl,'registration_dttm':ntime}
    message = str(message)
    message = message.replace("'",'"')
    result_mq = rabbitmq_add.delay('beacons_mq','_mq',message,'application/json','beacons_mq')
  
    return make_response(jsonify({'Ratatoskr':'Beacon registered'}),201)

@app.route('/beacon_reg', methods=['GET'])
def get_beacon_list():
    result_mysql_sel = mysql_select('ratatoskr',None,'BEACONS',None)
    return make_response(jsonify({'List of beacons':result_mysql_sel}),200)
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /ATM                                                                                                                                                     #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################

@app.route('/atm_status', methods=['GET'])
@crossdomain(origin='*')
def get_atm_status():
    global atm_status
    
    change = request.args.get('change')
    
    if (change is not None):
        if (change == "true"):
            atm_status = True
        else:
            atm_status = False
    return make_response(jsonify({'status':atm_status}),200)

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /ESP                                                                                                                                                     #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/geo', methods=['GET','POST'])
@crossdomain(origin='*')
def get_geo():

    result_mysql_beacon = mysql_select('ratatoskr',None, 'BEACONS',None)
    result_mysql_wifi = mysql_select('ratatoskr',None, 'WIFI',None)
    result_mysql_gps = mysql_select('ratatoskr',None, 'GPS',None)

    WIFI = []
    GPS = []
    Beacon = []

#GET WIFI
    for row in result_mysql_wifi:
        wifi = {}
        wifi["id"] = row[0]
        wifi["ssid"] = row[1]
        wifi["level"] = row[3]
        WIFI.append(wifi)
#GET BEACONS
    for row in result_mysql_beacon:
        beacon = {}
        beacon["uuid"] = row[0]
        beacon["major"] = row[1]
        beacon["minor"] = row[3]
        Beacon.append(beacon)
#GET GPS
    for row in result_mysql_gps:
        gps = {}
        gps["id"] = row[0]
        gps["latitude"] = row[1]
        gps["longitude"] = row[3]
        GPS.append(gps)

    response = {"GPS":GPS,"WIFI":WIFI,"BEACONS":Beacon}

    return make_response(jsonify(response),201)




#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /BANNER                                                                                                                                                 #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################

@app.route('/banner', methods=['POST','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def banner():
    try:
        UID = request.json["uid"]
        placement = request.json["placement"]
        banner_id = request.json["banner_id"]
        if banner_id == 'cabinet':
            banner_code = '<div style="height:270px;width:825px;background:linear-gradient(to right,#DDDCD9,white 600px)"><div style="height:270px;width:230px;float:left"><img id="label_img" src="http://www.evro-almaz.by/images/app/label_2.png" style="width:307px;height:200px;position:relative;right:25%;transform:rotate(25deg)"></img></div><div style="heigth:270px;width:315px;float:left"><h2 style="text-align:center;position:relative;margin-top:70px;color:blue">New Collection.<br>Try it now.</h2></div><div style="height:270px;width:275px;float:left"><img id="prod_img" src="http://www.evro-almaz.by/images/app/girl_jeans_1.png" style="height:100%;float:right"></img></div></div>'
        elif banner_id == 'slider':
            banner_code = '<div style="height:400px;width:760px;background-image:url(http://www.evro-almaz.by/images/app/slider_1.png);background-size:cover"></div>'
        elif banner_id == 'right':
            banner_code = '<div style="height:400px;width:350px;background-image:url(http://www.evro-almaz.by/images/app/right_finalsale_1.png);background-size:cover"></div>'  
        elif banner_id == 'leftdown':
            banner_code = '<div style="height:400px;width:250px;background-image:url(http://www.evro-almaz.by/images/app/leftdown_1.png);background-size:cover"><div style="background-color:white;opacity:0.5;border-radius:14px;position:relative;text-align:center;top:80%"><h3>Do not miss</h3></div></div>'  
        elif banner_id == 'left':
            banner_code = '<div style="height:170px;width:255px;background-image:url(http://www.evro-almaz.by/images/app/deleft_1.png);background-size:cover"></div>'  
        else:
            banner_code = 'no banner with specified banner_id'
        time.sleep(1)
        return banner_code
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':e}))








@app.route('/ccard', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def card():
    
    IndivID = request.json["IndivID"]
    AppForename = request.json["AppForename"]
    AppSurname = request.json["AppSurname"]
    AppMiddlename = request.json["AppMiddlename"]
    AppEducation = request.json["AppEducation"]
    AppAge = request.json["AppAge"]
    AppPassportNumber = request.json["AppPassportNumber"]
    AppFamilySize = request.json["AppFamilySize"]
    AppCarOwner = request.json["AppCarOwner"]
    AppMobile = request.json["AppMobile"]
    AppEmail = request.json["AppEmail"]
    AppJobPos = request.json["AppJobPos"]
    AppIncome = request.json["AppIncome"]
    AppJobExp = request.json["AppJobExp"]
    
    inputs = {"IndivID":IndivID,"AppForename":AppForename,"AppSurname":AppSurname,"AppMiddlename":AppMiddlename,"AppEducation":AppEducation,"AppAge":AppAge,"AppPassportNumber":AppPassportNumber,"AppFamilySize":AppFamilySize,
"AppCarOwner":AppCarOwner,"AppMobile":AppMobile,"AppEmail":AppEmail,"AppJobPos":AppJobPos,"AppIncome":AppIncome,"AppJobExp":AppJobExp}
    

    dns = "172.28.106.245"
    event = "scoringevent"
    #event = "SAS_Activity_echo_string"
    #inputs = {"in_string":"I rule"}
    rtdm_addr = "http://"+dns+"/RTDM/rest/runtime/decisions/"+event
    payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
    r = requests.post(rtdm_addr,json = payload)
    resp = str(r)
    return make_response(jsonify({"A":r.json()}),201)




#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /LUNA                                                                                                                                                    #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################

@app.route('/luna', methods=['GET'])
@crossdomain(origin='*')
def result_luna():
    return make_response(jsonify({'Ratatoskr':lunaresp,'Luna':lunaans, 'image':req_image, 'rid':rid}))
    
@app.route('/luna', methods=['OPTIONS'])
@crossdomain(origin='*',headers = 'Content-Type')
def send_options():
    return make_response(jsonify({'Ratatoskr':'PUT, GET'}))

@app.route('/luna', methods=['PUT'])
@crossdomain(origin='*',headers = 'Content-Type', content = 'application/json')
def call_luna():
    global lunaresp
    global lunaans
    global req_image
    global lunaans
    global list_of_images
    global rid
    image = ''
    try:
        image = request.json["data"]
    except Exception:
        return make_response(jsonify({'Ratatoskr':'Missing attribute data (image)'}),422)
    if (image == ""):
        return make_response(jsonify({'Ratatoskr':'Empty attribute data (image)'}),422)
    req_image = image
    #rid - applicant image , cid - client ID , bare - write to DB (True - no, False - yes)    
    try:
        rid = request.json["rid"]
    except Exception:
        rid = 500000
    if rid < 500000:
        rid = rid+500000
    try:
        cid = request.json["cid"]
    except Exception:
        cid = ''
    try:
        bare = request.json["bare"]
    except Exception:
        bare = True
    try:
        match_flg = request.json["match"]
    except Exception:
        match_flg = False

    #url = "http://172.28.104.180:8083/4/templates?id="+str(rid)
    url = "http://172.28.104.180:8083/4/templates"
    #usr = "test"
    #psw = "password"
    
    payload = {"image":image, "bare":bare}
    try:
        #r = requests.post(url,auth=(usr,psw),json = payload)
        r = requests.post(url,json = payload)
        lunaans = r.json()
        status = str(r)
    except Exception:
        lunaresp = 'Luna service is unreachable or unavailable'
        lunaans = 'Luna service is unreachable or unavailable'
        return make_response(jsonify({'Ratatoskr':lunaresp}),  415)  

     
    if ((("200") in status)  and (match_flg == False)):
        lunaresp = 'Luna has processed the image'
        return make_response(jsonify({'Ratatoskr': lunaresp,'Luna':str(r.json()),'score':r.json()["score"]}),  200)

    elif ((("201") in status)  and (match_flg == False)):  
        lunaresp = 'Luna has processed and saved the image'
        rid = r.json()["id"]
        return make_response(jsonify({'Ratatoskr': lunaresp,'Luna':str(r.json()),'score':r.json()["score"],'rid':rid}),  201)

    elif ((("201") in status)  and (match_flg == True)): 
        if cid != '':
            try:
                candidates = str(get_client(cid)[26])
            except Exception:
               lunaresp = 'Client not found'
               return make_response(jsonify({'Ratatoskr': lunaresp}), 500)
        else:
            candidates = str(get_all_clients())[1:-1]
         

        rid = r.json()["id"]
        url_get = "http://172.28.104.180:8083/4/similar_templates?id="+str(rid)+"&candidates="+candidates
        #g = requests.get(url_get,auth=(usr,psw))
        g = requests.get(url_get)
        
        try:
           v = []
           for item in g.json().iteritems():
               v.append(item) 
           score = v[0][1][0]["similarity"]
           photoid = v[0][1][0]["id"]
           clientid = get_cid_byphotoid(photoid)
           clientinfo = get_client(clientid)
           #clientinfo = json.loads(get_client(clientid))
           #return make_response(jsonify({'Ratatoskr': clientid}), 200)
        except Exception:
            lunaresp = 'Client photo not found in Luna. Check cid or photoid'
            return make_response(jsonify({'Ratatoskr': lunaresp,'url':url_get,'rid':rid,'photoid':photoid}), 500) 

        lunaresp = 'Luna has saved and matched the image'
        name = clientinfo[1]
        surname = clientinfo[3]
        middlename = clientinfo[2]
        gender = clientinfo[6]
        mobile = clientinfo[5]
        dob = str(clientinfo[9])
        

        return make_response(jsonify({'Ratatoskr':lunaresp,'score':score, 'client':clientid, 
'name':name,'surname':surname, 'middlename':middlename, 'gender':gender, 'mobile':mobile, 'dob':dob,'Luna':g.text, 'url':url_get,'rid':rid}), 201) 

    elif ((("200") in status)  and (match_flg == True)): 
        lunaresp = 'That will not work. Maybe \'bare\' should be \'false\' or there is an ambiguous \'match\' option?'
        return make_response(jsonify({'Ratatoskr': lunaresp}), 422) 

    elif ("500" in status):
        lunaresp = 'Luna failed on upload'
        return make_response(jsonify({'Ratatoskr': lunaresp}), 451)       
    else:
        lunaresp = 'Ooops... something unexpected happened'
        return make_response(jsonify({'Ratatoskr': lunaresp+' Response code is '+status}), 418) 


#Error handler
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'Ratatoskr': 'Service not found'}), 404)

if __name__ == '__main__':
    app.run(host=server_ip,debug=True)
#threaded = True processes = 4




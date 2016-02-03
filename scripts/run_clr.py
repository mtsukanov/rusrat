#!/var/beacon/clr/bin/python 
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         RATATOSKR WEB SERVICES 0.01                                                                                                                                       #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF LIBRARIES                                                                                                                                             #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################



from flask import Flask, jsonify, abort,make_response,request,json
from celery import Celery
from celery.result import ResultBase, AsyncResult
from time import gmtime, strftime
from ctasks import send_mq,add,rabbitmq_add,mysql_add,mysql_select,mysql_b_history_ins,call_rtdm
from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

#import celeryconfig
import  ctasks
import time
import pika
import requests
import MySQLdb


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
web_server = "ruswbsrvr"
soa_server = "rusrat:5000"
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



#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /MOBILE_GET                                                                                                                                              #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/mobile_get', methods=['GET'])

def mobile_get_all():
    cid = request.args.get('client_id')
    if cid is None:
        query_customers = 'Login is not null'
        query_tranz = None
        query_offers = None
        query_prods = 't1.PID = t2.PID'
        query_beacon = None
        query_wifi = None
        query_gps = None
    else:
        query_customers = 'Login is not null AND CID ='+cid
        query_tranz = 'CID ='+cid
        query_offers = 'CustomerID ='+cid
        query_prods = 't1.PID = t2.PID and t1.CID ='+cid
        query_beacon = None
        query_wifi = None
        query_gps = None
    try:
        result_mysql_sel = mysql_select('thebankfront',None,'customers',query_customers)
        result_mysql_tranz = mysql_select('thebankfront',None,'transhistory',query_tranz)
        result_mysql_offers = mysql_select('thebankfront',None,'offers',query_offers)
        result_mysql_prods = mysql_select('thebankfront','t1.CID, t2.PName, t2.PDesc, t1.PAmount,t2.PImage, t1.PRate, t1.PPayment, t2.PID, t1.PStart, t1.PEnd','customers as t0 inner join productdetails as t1 inner join products as t2',query_prods)
        result_mysql_beacon = mysql_select('ratatoskr',None, 'BEACONS',query_beacon)
        result_mysql_wifi = mysql_select('ratatoskr',None, 'WIFI',query_wifi)
        result_mysql_gps = mysql_select('ratatoskr',None, 'GPS',query_gps)
    except Exception:
        response = {"Ratatoskr":"Your request made me sick. Either parameters were unexpected or DB schema was cruely changed. Anyway this won't work, sorry for inconvenience."}
        return make_response(jsonify(response),500)
    Clients =[]
    Offers = []
    Products = []
    Transactions = []
    WIFI = []
    GPS = []
    Beacon = []
#GET CLIENTS
    for row in result_mysql_sel:
        client = {}
        client["clientid"] = row[0]
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
        offer["type"] = 'financial'#row[9]
        offer["description"] = row[4]
        offer["sum"] = row[6]
        offer["image"] = row[5]
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
        product["image"] = row[4]
        product["rate"] = row[5]
        product["payment"] = row[6]
        product["productid"] = row[7]
        product["purchased_dttm"] = str(row[8])#str(row[8].day)+"."+str(row[8].month)+"."+str(row[8].year)
        product["exparation_dttm"] = str(row[9])

        Products.append(product)

#GET SETTINGS
    Settings =     {
    "app_server" : app_server,
    "web_server" : web_server,
    "soa_server" : soa_server,
    "sync" : sync,
    "freq_in" : freq_in,
    "freq_out" : freq_out,
    "freq_sync" : freq_sync}
#GET TRANSACTIONS
    for row in result_mysql_tranz:
        tranz = {}
        tranz["tranid"] = row[0]
        tranz["agent"] = row[1]
        tranz["sum"] = row[2]
        tranz["tran_dttm"] = row[3]
        tranz["clientid"] = row[4]
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
        beacon["minor"] = row[3]
        Beacon.append(beacon)
#GET GPS
    for row in result_mysql_gps:
        gps = {}
        gps["id"] = row[0]
        gps["latitude"] = row[1]
        gps["longitude"] = row[3]
        GPS.append(gps)

   
    response = {"Clients":Clients,"Products":Products,"Offers":Offers,"Transactions":Transactions,"Settings":Settings,"GPS":GPS,"WIFI":WIFI,"BEACONS":Beacon}

    return make_response(jsonify(response, ensure_ascii=False),200)

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /MOBILE_POST                                                                                                                                             #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/mobile_post', methods=['POST'])
def mobile_post_all():
    sys = request.json['sys']
    wifi = request.json['wifi']
    beacon = request.json['beacon']
    gps = request.json['gps']
    trigger =  request.json['trigger']
    message = {"sys":sys,"wifi":wifi,"gps":gps,"beacon":beacon, "trigger": trigger,"opcode": "i"}
    result_mq = rabbitmq_add.delay('geo_mq','_mq',json.dumps(message, ensure_ascii=False),'application/json','geo_mq')

    return make_response(jsonify({'test':'a'}),201)




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

    return make_response(jsonify(Settings),201)

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
@app.route('/offer_accept', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def offer_accept():
    try: 
        visibility = request.json['visibility']
        option = 0
    except:
        option = 1
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
                respname = "accepted"
                respid = 1
            elif (visibility == 0 and priority == 0):
                respname = "rejected"
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
            return make_response(jsonify({'Ratatoskr':'request processed'}),201)
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
        except Exception:
            return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),406) 
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
"resptimestr" : str(resptime),
"param1" : param1,
"param2" : param2,
"param3" : param3,
"param4" : param4,
"param5" : param5,
"param6" : param6,
"param7" : param7
}
            return make_response(jsonify({'Ratatoskr':inputs}),201)
        except Exception:
            return make_response(jsonify({'Ratatoskr':'error processing site'}),418)  
#        result = call_rtdm.delay("172.28.106.245",'responsehistoryevent',inputs)
#        [v for v in result.collect()
#            if not isinstance(v, (ResultBase, tuple))]
#
#        return make_response(str(v[1]),201)


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /LAUNCH                                                                                                                                            #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/launch', methods=['POST'])
def launch():
    scenario = ""
    clientid = request.json['clientid']
    login = request.json['login']
    password = request.json['password']
    scenario = scenario.json['scenario']
    Status = {'clientid':clientid,'login':login,'password':password,'scenario':scenario}

    return make_response(jsonify(Status)}),201)


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
@crossdomain(origin='*')
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

    url = "http://luna.visionlabs.ru:8082/templates?id="+str(rid)
    usr = "SAS_LunaDemoAccess"
    psw = "U8mD8Q"
    
    payload = {"image":image, "bare":bare}
    try:
        r = requests.put(url,auth=(usr,psw),json = payload)
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
        url_get = "http://luna.visionlabs.ru:8082/similar_templates?id="+str(rid)+"&candidates="+candidates
        g = requests.get(url_get,auth=(usr,psw))
        
        try:
           v = []
           for item in g.json().iteritems():
               v.append(item) 
           score = v[0][1][0]["similarity"]
           photoid = v[0][1][0]["id"]
           clientid = get_cid_byphotoid(photoid)
           clientinfo = get_client(clientid)
           #clientinfo = json.loads(get_client(clientid))
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



resptime

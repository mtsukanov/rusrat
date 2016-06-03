#!/var/beacon/clr/bin/python 
# coding: utf-8
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
from ctasks import send_mq,add,rabbitmq_add,mysql_add,mysql_select,mysql_b_history_ins,call_rtdm,mssql_select,call_service
from datetime import timedelta,datetime
from flask import make_response, request, current_app
from functools import update_wrapper
from random import randint,choice
from transgen import transgen
from ctasks import call_rtdm,post
#import celeryconfig
#import  ctasks
import datetime
import time
import pika
import requests
import MySQLdb
import pymssql
import psycopg2;
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
web_server = "http://labinfo.sas.com"
soa_server = "172.28.104.171:5000"
sync = 1
freq_in = 15
freq_out = 10
freq_sync = 20


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

def get_max_eventid_luna():
    db = psycopg2.connect(host="172.28.104.180", port = 5432, user="testuser",password="password", dbname="FaceStreamRecognizer")
    cur = db.cursor()
    query2 = "SELECT MAX(event_id) FROM event"
    cur.execute(query2)
    data = cur.fetchone()
    max_eventid = data[0]
    return max_eventid



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


@app.route('/rus', methods=['GET'])
def test2rus():
    Str = request.args.get('p')
    return jsonify({'Response':'Русские — Википедия','RUS':Str})




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

@app.route('/geotrigger', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def geotrigger():
    try:
        cid =  request.json["cid"] 
        scenario = request.json["scenario"] 
        beaconid =  request.json["beaconid"]
        trigger = request.json["trigger"]  
        spotid =  request.json["spotid"] 
        spotname =  request.json["spotname"] 
        time =  request.json["time"] 
        Geo = {
        'cid' :  int(cid) ,
        'scenario' : scenario,
        'beaconid' :  beaconid ,
        'spotid' :  int(spotid),
        'spotname' : spotname,
        'time' :  datetime.datetime.strptime(time,"%m/%d/%y %H:%M:%S").isoformat(sep='T'),
        'trigger':trigger}
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'Andrey, your data is corrupted. Look what you did:'+str(e)}),415)    
    try:
        result_mysql_custdet = mysql_select('thebankfront','FirstName,MiddleName,LastName,CAST(DateOfBirth AS CHAR) ','customers',"CID="+str(cid))
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'SQL request seems to be incorrect. Here are details:'+str(e)}),416) 
    if spotname == "The Bank":
        area = "bank"
    elif spotname == "The Store":
        area = "retail"
    if trigger != 'Luna':
        for row in result_mysql_custdet:
            payload = {"name":row[0],"surname":row[2],"middlename":row[1],"dob":str(row[3]),"id":cid,"status":"processing","reason":"visit","location":spotname,"area":area}
        try:
            result = call_service.apply_async(("active_queue",payload),retry=True)    
        except Exception as e:
            return make_response(jsonify({'Ratatoskr':'Some problems with python queue service.Further details: '+str(e)}),417)  
    try:
        rtdm = call_rtdm.apply_async(("172.28.106.245","geomainevent",Geo),retry=True)      
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'Some problems with RTDM request.Further details: '+str(e)}),418)    
    #return make_response(jsonify({'Ratatoskr':'So far so good'}),200)
    return make_response(jsonify({'Ratatoskr':str(rtdm)}),200)



#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /EMAIL                                                                                                                                            #
#                                                                                                                                                                                           #
#####################################################################################################################################################
@app.route('/email', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def email():
    global req_path
    try:
        apikey =  request.args.get("apikey")
        subject = request.args.get("subject")
        fromw = request.args.get("from")
        from_name = request.args.get("from_name")
        tow = request.args.get("to")
        charset = request.args.get("charset")
        template = request.args.get("template")
        merge_title =  request.args.get("merge_title")
        merge_firstname = request.args.get("merge_firstname")
        merge_lastname = request.args.get("merge_lastname")
        merge_websiteurl = json.loads(request.args.get("merge_websiteurl"))
        OfferImg = merge_websiteurl["offerimg"]
        MainTxt = merge_websiteurl["maintxt"]
        DescTxt = merge_websiteurl["desctxt"]
        FName = merge_websiteurl["name"]
        LName = merge_websiteurl["lname"]
        MName = merge_websiteurl["mname"]
        ID = merge_websiteurl["id"]
        url = "http://thebank.sas.com/CreditScoring/creditcard.html%3Fofferimg="+OfferImg+"%26maintxt="+MainTxt+"%26desctxt="+DescTxt+"%26lname="+LName+"%26name="+FName+"%26mname="+MName+"%26id="+ID

    except:
        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415)
    req_path =   "https://api.elasticemail.com/v2/email/send?apikey="+apikey+"&subject="+subject+"&from="+fromw+"&from_name="+from_name+"&to="+tow+"&charset="+charset+"&template="+template+"&merge_title="+merge_title+"&merge_firstname="+merge_firstname+"&merge_lastname="+merge_lastname+"&merge_websiteurl="+url
    try:
        r = requests.get(req_path) 
        answer = r.content
    except:
        return make_response(jsonify({'Ratatoskr':'connection error'}),404)   
    return make_response(jsonify({'Ratatoskr':answer}),200)


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /PostgreSQL                                                                                                                                      #
#                                                                                                                                                                                           #
##################################################################################################################################################### 

#@app.route('/decode', methods=['POST','GET','OPTIONS'])
#@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def deco():
    time.sleep(3)
    maxid = get_max_eventid_luna()
    result = post.apply_async([maxid])    
    #print 'ok'  
    return make_response(jsonify({'Ratatoskr':str(result)}),200)
deco()

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /SMS                                                                                                                                              #
#                                                                                                                                                                                           #
#####################################################################################################################################################
@app.route('/sms', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def sms():
    global req_path
    try:
        login =  request.args.get("login") 
        psw = request.args.get("psw")
        phones = request.args.get("phones")
        mes = request.args.get("mes")
        sender = request.args.get("sender")
        #param1 = request.json["param1"]
        #param2 = request.json["param2"]
        #param3 = request.json["param3"]
        #param4 = request.json["param4"] 
    except Exception:
        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415) 
    req_path = "https://smsc.ru/sys/send.php?charset=utf-8&login="+login+"&psw="+psw+"&phones="+phones+"&mes="+mes+"&sender="+sender    
    try:
        r = requests.get(req_path) 
        answer = r.content
    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'Ratatoskr':'connection error'}),404)   
    return make_response(jsonify({'Ratatoskr':'Success!'}),200)

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /
#FasetZ                                                                                                                     #
#                                                                                                                                                                                           #
####################################################################################################################################################

@app.route('/fasetz', methods=['GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def fasetz():
    Arr1 = [1,2,3,4,5,6]
    Arr2 = [4,5,3,8,11,12,33,1]
    ArrOut=[]
    for i in Arr1:
        for l in Arr2:
             if i==l:
                  ArrOut.append(l)
    return make_response(jsonify({'Ratatoskr':ArrOut}),200)










#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /
#Save in MSSQL_SERVER                                                                                                                         #
#                                                                                                                                                                                           #
####################################################################################################################################################
@app.route('/mssqlsave', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def mssqlsave():
    try:
        CID = request.json["CID"]
        FirstName = request.args.get("FirstName").encode('utf-8')
        LastName = request.args.get("LastName").encode('utf-8')
        MiddleName = request.args.get("MiddleName").encode('utf-8')
        Passport = request.json["Passport"] 
        MobileNumber = request.json["MobileNumber"] 
        Gender = request.json["Gender"] 
        Age = request.json["Age"] 
        AgeGroup = request.json["AgeGroup"] 
        DateOfBirth = request.json["DateOfBirth"] 
        MaritalStatus = request.json["MaritalStatus"] 
        Children = request.json["Children"] 
        Education = request.json["Education"] 
        Occupation = request.json["Occupation"] 
        Income = request.json["Income"] 
        Email = request.json["Email"] 
        PhoneNumber = request.json["PhoneNumber"] 
        Vkontakte = request.json["Vkontakte"]
        Facebook = request.json["Facebook"] 
        Country = request.args.get("Country").encode('utf-8')
        City = request.args.get("City").encode('utf-8') 
        PhotoID = request.json["PhotoID"]  
        LanguageID = request.json["LanguageID"]  
        Street = request.args.get("Street").encode('utf-8') 
        State = request.args.get("State").encode('utf-8') 
    except:
        return make_response(jsonify({'Ratatoskr':'Input is incorrect'}),400)    
    try:
        conn = pymssql.connect(server = '172.28.106.17',user = 'rtdm',password = 'Orion123',database='CIDB')
        cursor = conn.cursor()
    except:
        return make_response(jsonify({'Ratatoskr':'Connection failed'}),400)  
    cursor.execute("SELECT COUNT(IndivID) FROM [DataMart].[INDIVIDUAL] WHERE IndivID="+str(CID))
    data = cursor.fetchone()
    count = data[0]
    if count == 0:
        query1=(
        "INSERT INTO [DataMart].[INDIVIDUAL] (IndivID) VALUES ("+str(CID)+")"
        "INSERT INTO [DataMart].[INDIVIDUAL_DEMOGRAPHIC] (IndivID) VALUES ("+str(CID)+")"
        "INSERT INTO [DataMart].[INDIVIDUAL_SOCIAL] (IndivID) VALUES ("+str(CID)+")"
        "INSERT INTO [DataMart].[INDIVIDUAL_PASSPORT] (IndivID) VALUES ("+str(CID)+")"
        )
        cursor.execute(query1)
    sql1 = (
    "UPDATE [DataMart].[INDIVIDUAL] SET "
    "Forename = '"+str(FirstName)+"',"
    "Surname='"+str(LastName)+"',"
    "Middlename='"+str(MiddleName)+"',"
    "Mobile='"+str(MobileNumber)+"',"
    "Birthdate='"+str(DateOfBirth)+"',"
    "Email='"+str(Email)+"',"
    "Phone='"+str(PhoneNumber)+"',"
    "PhotoID='"+str(PhotoID)+"'"
    "WHERE IndivID="+str(CID)+"")
    sql2 = (
    "UPDATE [DataMart].[INDIVIDUAL_DEMOGRAPHIC] SET "
    "Gender = '"+str(Gender)+"',"
    "Age='"+str(Age)+"',"
    "AgeGroupID='"+str(AgeGroup)+"',"
    "MartialStatus='"+str(MaritalStatus)+"',"
    "Children='"+str(Children)+"',"
    "EducationID='"+str(Education)+"',"
    "JobID='"+str(Occupation)+"',"
    "Income='"+str(Income)+"',"
    "LanguageID='"+str(LanguageID)+"'"
    "WHERE IndivID="+str(CID)+"")
    sql3 = (
    "UPDATE [DataMart].[INDIVIDUAL_PASSPORT] SET "
    "PassportNumber = '"+str(Passport)+"',"
    "PassportCountry='"+str(Country)+"',"
    "PassportCity='"+str(City)+"',"
    "PassportState='"+str(State)+"',"
    "PassportStreet='"+str(Street)+"' "
    "WHERE IndivID="+str(CID)+"")
    sql4 = (
    "UPDATE [DataMart].[INDIVIDUAL_SOCIAL] SET "
    "VkName = '"+str(Vkontakte)+"',"
    "FacebookName='"+str(Facebook)+"'"
    "WHERE IndivID="+str(CID)+" COMMIT ")
    try:
        cursor.execute(sql1)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'Update INDIVIDUAL table failed'}),400)  
    try:
        cursor.execute(sql2)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'Update INDIVIDUAL_DEMOGRAPHIC table failed'}),400)  
    try:
        cursor.execute(sql3)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'Update INDIVIDUAL_PASSPORT table failed'}),400)  
    try:
        cursor.execute(sql4)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'Update INDIVIDUAL_SOCIAL table failed'}),400) 
    return make_response(jsonify({'Ratatoskr':'ok'}),200)    


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /MOBILE_GET                                                                                                                                              #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/mobile_get', methods=['GET'])

def mobile_get_all():
    global LastMobileGet
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
    LastMobileGet = {"LastRequestTime":strftime("%d.%m.%Y %H:%M:%S",gmtime()),"cid":cid}
    if cid is None:
        query_customers = 'Login is not null'
        query_tranz = ''
        query_offers = None
        query_prods = "WHERE IndivID > 0"
        query_prods_det = None
        query_beacon = None
        query_wifi = None
        query_gps = None
        try:
            #result_mysql_offers = mysql_select('thebankfront',None,'offers',query_offers)
            result_mssql_offers = mssql_select('CIDB','DataMart',None,'OFFER',query_offers)
            #GET OFFERS
            for row in result_mssql_offers:
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
        except Exception as e:
            response = {"Ratatoskr":e}
            return make_response(jsonify(response),500)
    else:
        try:
            #dns = "http://"+server_ip+":5000/nbo"
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
                #offer = {'i':i,'clientid': int(resp["outputs"]["cid"]), 'description':resp["outputs"]["briefdetails"][i], 'generated_dttm':'','image':'','offerid':resp["outputs"]["offercode"][i],'payment':resp["outputs"]["payment"][i],'priority':resp["outputs"]["prio"][i],'rate':resp["outputs"]["rate"][i],'recieved_dttm':'','secret':'','sent_dttm':'','sum':resp["outputs"]["amount"],'termination_dttm':'','type':'financial','visibility':1}
                offer = {'clientid': str(int(resp["outputs"]["cid"])), 'description':resp["outputs"]["briefdetails"][i], 'generated_dttm':'','image':'','name':resp["outputs"]["offername"][i],'offerid':int(resp["outputs"]["offercode"][i]),'payment':resp["outputs"]["payment"][i],'priority':int(resp["outputs"]["prio"][i]),'rate':resp["outputs"]["rate"][i],'duration':12,'recieved_dttm':'','secret':'','sent_dttm':'','sum':resp["outputs"]["amount"][i],'termination_dttm':'','type':resp["outputs"]["offertype"][i],'visibility':1}
                Offers.append(offer)
                i += 1
            #return make_response(jsonify({'Offers':Offers, 'OUTPUT':resp["outputs"]}),201) 
                  
            
        except Exception as e:
            response = {"Ratatoskr":"R:"+str(e)}
            return make_response(jsonify(response),500)      
        try:
            resp = r.json()
            response = {"Ratatoskr":"Try was OK calling NBO:"+str(resp)+str(dns)}
            #return make_response(jsonify(response),500)
        except Exception:
            response = {"Ratatoskr":"Error calling NBO:"+str(Exception)+str(dns)}
            return make_response(jsonify(response),500)

        query_customers = 'Login is not null AND CID ='+cid
        query_tranz = "AccountID IN (SELECT AccountID from [DataMart].[Account] WHERE IndivID= "+cid+")"
        query_offers = 'IndivID ='+cid
        query_prods = "WHERE IndivID ="+cid
        query_beacon = None
        query_wifi = None
        query_gps = None
    try:
        result_mysql_sel = mysql_select('thebankfront',None,'customers',query_customers)
        result_mssql_offers = mssql_select('CIDB','DataMart',None,'OFFER',query_offers)
        result_mssql_tranz = mssql_select('CIDB','TRANSData','TermID,TransSum,TransDate,TransID,AccountID','[TRANSACTION]',query_tranz)
        result_mysql_beacon = mysql_select('ratatoskr',None, 'BEACONS',query_beacon)
        result_mysql_wifi = mysql_select('ratatoskr',None, 'WIFI',query_wifi)
        result_mysql_gps = mysql_select('ratatoskr',None, 'GPS',query_gps)
        db = pymssql.connect(server = '172.28.106.17',user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
        cur = db.cursor()
        query = (
        " SELECT ProdDetRate,ProdDetAmount,ProdDetPayment,ProdDetPeriod,ProdDetName,t1.ProdDetID,t1.ProdID,t2.ProdDesc,t2.ProdName,t2.ProdType,t3.IndivId,t1.ProdDetValidFrom,t1.ProdDetValidTo,t2.ProdType "
        " FROM [CIDB].[DataMart].[PRODUCTDETAILS] as t1 inner join [CIDB].[DataMart].[PRODUCT] as t2 on t1.ProdID = t2.ProdID inner join [CIDB].[DataMart].[ACCOUNT] as t3 on t3.ProdDetID = t1.ProdDetID"
        " WHERE t1.ProdDetID IN (SELECT ProdDetID FROM [CIDB].[DataMart].[ACCOUNT]"+query_prods+")")
        cur.execute(query)
    except Exception as e:
        response = {"Ratatoskr":e}
        return make_response(jsonify(response),500)
        #"Your request made me sicks. Either parameters were unexpected or DB schema was cruely changed. Anyway this won't work, sorry for inconvenience."
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
#GET PRODUCTS
    for row in cur.fetchall():
        product = {} 
        product["clientid"] = int(row[10])
        product["sum"] = row[1]
        product["duration"] = row[3]
        #product["image"] = row[4]
        product["image"] = ""
        product["rate"] = row[0]
        product["payment"] = row[2]
        product["productid"] = row[5]
        product["purchased_dttm"] = row[11]#str(row[8].day)+"."+str(row[8].month)+"."+str(row[8].year)
        product["exparation_dttm"] = row[12]#str(row[9])
        product["name"] = row[4]    
        product["type"] = row[13]#row[9]
        product["description"] = row[7]
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
    for row in result_mssql_tranz:
        tranz = {}
        tranz["tranid"] = row[3]
        tranz["agent"] = row[0]
        tranz["sum"] = row[1]
        tranz["tran_dttm"] ="140451295"
        tranz["clientid"] =  mssql_select('CIDB','DataMart','CAST(IndivID AS INT)','[ACCOUNT]','AccountID='+str(row[4]))[0][0]
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
        gps["longitude"] = row[2]
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
#                         BLOCK OF /mtsukanov                                                                                                                                             #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
HistArr=[]
@app.route('/mobile_post', methods=['POST','GET'])
def mobile_post_all():
    global LastMobile
    global HistArr
    HistArr.append({strftime("%d.%m.%Y %H:%M:%S",gmtime()):request.data})
    try:
        sys = request.json['sys']
        wifi = request.json['wifi']
        beacon = request.json['beacon']
        gps = request.json['gps']
        trigger =  request.json['trigger']
        message = {"sys":sys,"wifi":wifi,"gps":gps,"beacon":beacon, "trigger": trigger,"opcode": "i"}
        LastMobile = message
        result_mq = rabbitmq_add.delay('geo_mq','_mq',json.dumps(message, ensure_ascii=False),'application/json','geo_mq')
        return make_response(jsonify({'Ratatoskr':'request processed'}),201)
    except Exception:
        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415)

@app.route('/hist', methods=['GET'])
def hist():
    var = HistArr
    return make_response(jsonify({"Ratatoskr":var}),200)





#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /GET LAST RESULTS                                                                                                                                           #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/getlast', methods=['GET'])
def lastrequest():
    try:
        launch = LastLaunch
    except:
        launch = "The service hasn't been requested after server reboot"
    try:
        offer = LastOffer
    except:
        offer = "The service hasn't been requested after server reboot"
    try:
        mobile = LastMobile
    except:
        mobile = "The service hasn't been requested after server reboot"
    try:
        sync = LastSync
    except:
        sync = "The service hasn't been requested after server reboot"
    try:
        mobileget = LastMobileGet
    except:
        mobileget = "The service hasn't been requested after server reboot"
    try:
        return make_response(jsonify({'launch':launch,'offer_accept':offer,'mobile_post':mobile,'sync_updt':sync,'mobile_get':mobileget}),200)
    except Exception:
        return make_response(jsonify({'Ratatoskr':'Some error occures'}),415)

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /GET ANALYTICS DATA                                                                                                                                         #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/get_analytics', methods=['POST','OPTIONS','GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def get_analytics():
    try:
        cid = request.json['cid']
    except Exception:
        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415)
    tr = []
    aggr = []
    db = pymssql.connect(server = '172.28.106.17',user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
    mssql_accid = ("SELECT AccountID FROM [DataMart].[ACCOUNT] WHERE IndivID="+cid)
    cur = db.cursor()
    cur.execute(mssql_accid)  
    for row in cur.fetchall(): 
        msssql_trans_query = "AccountID = "+ str(int(row[0]))+"AND TransStatus = 'ok'"
        mssql_trans = mssql_select('CIDB','[TRANSData]','TransDate,TransSum,TransType,TermID','[TRANSACTION]', msssql_trans_query)
        for row2 in mssql_trans:
             trans = {}
             trans['TransData'] = row2[0]
             trans['Sum'] = row2[1]
             trans['Type'] = row2[2]
             trans['TermID'] = row2[3]
             trans['MCC'] = int(mssql_select('CIDB','[TRANSData]','MCC','[Terminal]','TermID = '+str(trans['TermID']))[0][0])
             trans['Category'] = mssql_select('CIDB','[TRANSData]','MCCName','[MCC]','MCC = '+str(int(trans['MCC'])))[0][0]
             trans['Lat'] = mssql_select('CIDB','[TRANSData]','TermLatitude','[Terminal]','TermID = '+str(trans['TermID']))[0][0]
             trans['Lon'] = mssql_select('CIDB','[TRANSData]','TermLongitude','[Terminal]','TermID = '+str(trans['TermID']))[0][0]
             trans['Account'] = int(row[0])
             tr.append(trans)     
    mssql_agrr = (
    "SELECT SUM(TransSum)/(SELECT SUM(TransSum) from [CIDB].[TRANSData].[TRANSACTION] WHERE TransType =1 AND AccountID IN (SELECT AccountID FROM [DataMart].[ACCOUNT] WHERE IndivID="+cid+") AND TransStatus = 'ok')*100,SUM(TransSum) as Sum,t2.MCC,t3.MCCName "
    "FROM [CIDB].[TRANSData].[TRANSACTION] as t1 inner join [CIDB].[TRANSData].[TERMINAL] as t2 on t1.TermID = t2.TermID inner join [CIDB].[TRANSData].[MCC] as t3 on t2.MCC=t3.MCC "
    "WHERE t1.TransType =1 AND AccountID IN (SELECT AccountID FROM [DataMart].[ACCOUNT] WHERE IndivID="+cid+") AND TransStatus = 'ok'"
    "GROUP BY t1.TermID,t2.MCC,t3.MCCName")
    cur = db.cursor()
    cur.execute(mssql_agrr)
    for row in cur.fetchall():
        aggegate = {}
        aggegate['Percent'] = row[0]
        aggegate['Sum'] = row[1]  
        aggegate['Category'] = row[3]
        aggr.append(aggegate)
    return make_response(jsonify({'Transaction_list':tr,'Aggregate':aggr}),200)

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /NEW PRODUCTS                                                                                                                                    #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/new_products', methods=['POST','OPTIONS','GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def new_products():
    db = pymssql.connect(server = '172.28.106.17',user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
    cid = request.args.get('cid')
    proddetid = request.args.get('proddetid')
    if (proddetid is not None):
        cur = db.cursor()
        query = (
        " SELECT ProdImgID FROM [CIDB].[DataMart].[PRODUCTDETAILS] as t1 inner join [CIDB].[DataMart].[PRODUCT] as t2 on t1.ProdID =  t2.ProdID WHERE t1.ProdDetId = "+proddetid)
        cur.execute(query)
        details = cur.fetchone()
        proddet = {}
        proddet['ImageID'] = details[0]
        return make_response(jsonify({'ProductsDetails':proddet}),200)
    if (cid is not None):
        Products=[]         
        cur = db.cursor()
        query = (
        " SELECT ProdDetRate,ProdDetAmount,ProdDetPayment,ProdDetPeriod,ProdDetName,t1.ProdDetID,t1.ProdID,t2.ProdDesc,t2.ProdName,t2.ProdType,t1.ProdDetValidFrom,t1.ProdDetValidTo"
        " FROM [CIDB].[DataMart].[PRODUCTDETAILS] as t1 inner join [CIDB].[DataMart].[PRODUCT] as t2 on t1.ProdID = t2.ProdID inner join [CIDB].[DataMart].[ACCOUNT] as t3 on t3.ProdDetID = t1.ProdDetID"
        " WHERE t1.ProdDetID IN (SELECT ProdDetID FROM [CIDB].[DataMart].[ACCOUNT] WHERE IndivID="+cid+")")
        cur.execute(query)
        for row in cur.fetchall():
            prods = {}
            prods['Rate'] = row[0]
            prods['Amount'] = row[1]
            prods['Payment'] = row[2]
            prods['Duration'] = row[3]
            prods['Name'] = row[4]
            prods['ProductID'] = row[5]
            prods['Description'] = row[7]
            prods['FromDate'] = row[10]
            prods['ToDate'] = row[11]
            Products.append(prods)
        return make_response(jsonify({'Products':Products}),200)
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /SYNC_UPDT                                                                                                                                            #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/sync_updt', methods=['POST'])
def sync_updt():
    global LastSync
    global app_server
    global web_server
    global soa_server
    global sync
    global freq_in
    global freq_out
    global freq_sync
    global Settings
    try:
        app_server = request.json['app_server']
        web_server = request.json['web_server']
        soa_server = request.json['soa_server']
        sync = request.json['sync']
        freq_in = request.json['freq_in']
        freq_out = request.json['freq_out']
        freq_sync = request.json['freq_sync']
        LastSync = {"LastRequestTime":strftime("%d.%m.%Y %H:%M:%S",gmtime()),"app_server":app_server,"web_server":web_server,"soa_server":soa_server,"sync":sync,"freq_in":freq_in,"freq_out":freq_out,"freq_sync":freq_sync}
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
    global LastOffer
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
            #LastOffer = {"LastRequestTime":strftime("%d.%m.%Y %H:%M:%S",gmtime()),"type":context,"visibility":visibility,"priority":priority,"accepted_dttm":accepted_dttm,"cid":cid,"offerid":offerid}
            LastOffer = request.data
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
    #.isoformat(sep='T')
            inputs = {"cid":cid,
"channel": channel,
"context" : context,
"device" : device,
"offerid" : offerid,
"resptype" : resptype,
"respname" : respname,
"respid" : respid,
"resptime" : datetime.datetime.now().isoformat(sep='T'),
"resptimestr" : str(accepted_dttm),
"param1" : None,
"param2" : None,
"param3" : None,
"param4" : None,
"param5" : None,
"param6" : None,
"param7" : None}
            #return make_response(jsonify({'Ratatoskr':'request processed'}),201)
        except Exception as e:
            return make_response(jsonify({'Ratatoskr':e}),415)       
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
        result = call_rtdm.apply_async(("172.28.106.245","responsehistoryevent",inputs),retry=True)    
        return make_response(jsonify({'Ratatoskr':str(result)}),201)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':e}),418)  
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
    global LastLaunch
    try:
        clientid = request.json['clientid']
        login = request.json['login']
        password = request.json['password']
        scenario = request.json['scenario']
        Status = {'clientid':clientid,'login':login,'password':password,'scenario':scenario}
        LastLaunch = {"LastRequestTime":strftime("%d.%m.%Y %H:%M:%S",gmtime()),"clientid":clientid,"login":login,"password":password,"scenario":scenario}
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
                if datetime.datetime.strptime(currdate,'%d.%m.%Y %H:%M:%S') - datetime.datetime.strptime(obj['time'],'%d.%m.%Y %H:%M:%S') < datetime.timedelta(0,10) and (obj['location'] == 'terminal' or obj['location'] == 'camera'):
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

@app.route('/atm_status', methods=['POST'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def set_atm_status():
    try:
        TID= request.json["TID"]
        Status = request.json["Status"]
    except:
        return make_response(jsonify({'Ratatoskr':'TID is incorrect'}),400)
    conn = pymssql.connect(server = '172.28.106.17',user = 'rtdm',password = 'Orion123',database='CIDB')
    cursor = conn.cursor()
    sql=(
        
        "UPDATE [TRANSData].[TERMINAL] SET TermStatus='"+Status+"' WHERE TermID="+str(TID)+""
        "COMMIT")
    cursor.execute(sql)     
    return make_response(jsonify({'Ratatoskr':'Terminal status has been updated'}),200)
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
            banner_code = '<div style="heighOrion123t:400px;width:250px;background-image:url(http://www.evro-almaz.by/images/app/leftdown_1.png);background-size:cover"><div style="background-color:white;opacity:0.5;border-radius:14px;position:relative;text-align:center;top:80%"><h3>Do not miss</h3></div></div>'  
        elif banner_id == 'left':
            banner_code = '<div style="height:170px;width:255px;background-image:url(http://www.evro-almaz.by/images/app/deleft_1.png);background-size:cover"></div>'  
        else:
            banner_code = 'no banner with specified banner_id'
        time.sleep(1)
        return banner_code
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':e}))







#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /CreditCard                                                                                                                                                #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################

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
    

    #dns = "172.28.106.245"
    #event = "scoringevent"
    #event = "SAS_Activity_echo_string"
    #inputs = {"in_string":"I rule"}
    #rtdm_addr = "http://"+dns+"/RTDM/rest/runtime/decisions/"+event
    #payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
    #r = requests.post(rtdm_addr,json = payload)
    #resp = str(r)
    try:
        result = call_rtdm.apply_async(("172.28.106.245","scoringevent",inputs),retry=True)    
        #res = call_rtdm.AsyncResult(str(result))
        #time.sleep(15)
        return make_response(jsonify({'Ratatoskr':str(result)}),201)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':e}),418) 

    #return make_response(jsonify({"A":r.json()}),201)


@app.route('/ccard', methods=['PUT'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def cardcheck():
    try:
        task = request.json["task_id"]
    except:
        return make_response(jsonify({'Ratatoskr':"Task ID is corrupt"}),418) 
    res = call_rtdm.AsyncResult(task)
    isready = res.ready()
    while (isready == False):
        isready = res.ready()
    if isready == True:
        return make_response(jsonify({'Ratatoskr':res.get()}),201)  
    

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /LimitControl                                                                                                                                            #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/limit', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def limit():
    try:
        Limit = request.json["Limit"]
        CID = request.json["CID"]
        TID = request.json["TID"]
        Type = request.json["Type"]
    except:
        return make_response(jsonify({"Ratatoskr":'input values are corrupt'}),400)
    conn = pymssql.connect(server = '172.28.106.17',user = 'rtdm',password = 'Orion123',database='CIDB')
    cursor = conn.cursor()
    cursor.execute('SELECT CardCashLImit FROM [DataMart].[Card] WHERE IndivID ='+str(CID))
    data = cursor.fetchone()
    curlimit = int(data[0])
    cursor.execute('SELECT TermStatus FROM [TRANSData].[TERMINAL] WHERE TermID ='+str(TID))
    data = cursor.fetchone()
    termstatus = data[0]
    if termstatus == "nocash":
        trans={'TransID':randint(1,10000),'CardID':1,'AccountID':1,'TermID':TID,
'TransStatus':'error','TransDate':strftime("%d.%m.%Y %H:%M:%S",gmtime()),'TransSum':Limit,'TransCurrency':'rub','TransType':Type,
'TransInfo':"atmerror",'TransParam1':'','TransParam2':'','TransParam3':'','TransParam4':''}
        que_result = rabbitmq_add('trans_mq','t_mq',json.dumps(trans,ensure_ascii=False),'application/json','trans_mq')
        return make_response(jsonify({"Ratatoskr":'ATM has no money'}),202)
    elif termstatus == "work":
        if curlimit-Limit >= 0:
            trans={'TransID':randint(1,10000),'CardID':1,'AccountID':1,'TermID':TID,
'TransStatus':'ok','TransDate':strftime("%d.%m.%Y %H:%M:%S",gmtime()),'TransSum':Limit,'TransCurrency':'rub','TransType':Type,
'TransInfo':"",'TransParam1':'','TransParam2':'','TransParam3':'','TransParam4':''}
            que_result = rabbitmq_add('trans_mq','t_mq',json.dumps(trans,ensure_ascii=False),'application/json','trans_mq')
            return make_response(jsonify({"Ratatoskr":'Transaction has been generated'}),200)
        else:
            trans={'TransID':randint(1,10000),'CardID':1,'AccountID':1,'TermID':TID,
'TransStatus':'refusal','TransDate':strftime("%d.%m.%Y %H:%M:%S",gmtime()),'TransSum':Limit,'TransCurrency':'rub','TransType':Type,
'TransInfo':"proddetlimit",'TransParam1':'','TransParam2':'','TransParam3':'','TransParam4':''}
            que_result = rabbitmq_add('trans_mq','t_mq',json.dumps(trans,ensure_ascii=False),'application/json','trans_mq')
            return make_response(jsonify({"Ratatoskr":'Limit is exceeded'}),201)
    else:
        return make_response(jsonify({"Ratatoskr":'ATM is out of servce'}),203)


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




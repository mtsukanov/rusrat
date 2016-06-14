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
#from transgen import transgen
from ctasks import call_rtdm,post,facetztask,transgen
#import celeryconfig
#import  ctasks
import datetime
import time
import pika
import requests
import MySQLdb
import pymssql
import psycopg2
import urllib
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
    return make_response(jsonify({"Ratatoskr":r.json()}),201)

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

@app.route('/decode', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def deco():
    time.sleep(3)
    maxid = get_max_eventid_luna()
    result = post.apply_async([maxid])    
    #print 'ok'  
    return make_response(jsonify({'Ratatoskr':str(result)}),200)
#deco()

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

@app.route('/facetz', methods=['GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def facetz():
    cid =  request.args.get("cid") 
    result = facetztask.apply_async([cid])   
    return make_response(jsonify({'Ratatoskr':str(result)}),200)




@app.route('/facetz2', methods=['GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def facetz2():
    cid =  request.args.get("cid") 
    url = "https://api.facetz.net/v2/facts/user.json?key=51af6192-c812-423d-ae25-43a036804632&query={%22user%22:{%22id%22:%22"+cid+"%22},%22ext%22:{%22exchangename%22:%22sas_demo%22}}"
    Formatted = []
    r = requests.get(url)
    Formatted.append({"id":r.json()['id']})
    i=1
    for el in r.json()['visits']:
        formatted_el = {}
        formatted_el['number'] = i
        formatted_el['ts'] = datetime.datetime.strftime(datetime.datetime.fromtimestamp(el['ts']/1000),"%Y-%m-%d %H:%M:%S")
        formatted_el['url'] = urllib.unquote(el['url'])
        Formatted.append(formatted_el)
        i+=1
    return make_response(jsonify({'Ratatoskr':Formatted}),200)









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
                offer = {'clientid': str(int(resp["outputs"]["cid"])), 'description':resp["outputs"]["briefdetails"][i], 'generated_dttm':'','image':'iVBORw0KGgoAAAANSUhEUgAAAZAAAAEsCAYAAADtt+XCAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAAAYdEVYdFNvZnR3YXJlAHBhaW50Lm5ldCA0LjAuNvyMY98AAP+BSURBVHhe7P11dBxZlvUNm5mxXOVihu5CM5MsZrRllNmybFmWZUsyW2ZmZmZmZmZ2ucrFVd09TdM9PTM9z7Pfs0/kzQylw+Xqed/1rfWtij/2iogbkZGZgvOLfc6FAgBcuXLlypWrf1mOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja5cuXLlytWz5NjoypUrV65cPUuOja6cNXjeJnzaLhM1QrqhcnBPVAqxVDm0lx771ANVpL1KkGyDu6FaUDdUD+6O54Is8fU1Q7rjxdBueDm8B16PTsU78f3wQZsB+LhDFmp1yka9bkPQtNdItEwbg8D+4xCWOQVR2dOQOHQ2kkfOR8cxC9F1/FL0mLwMfWasRvqc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','name':resp["outputs"]["offername"][i],'offerid':int(resp["outputs"]["offercode"][i]),'payment':resp["outputs"]["payment"][i],'priority':int(resp["outputs"]["prio"][i]),'rate':resp["outputs"]["rate"][i],'duration':12,'recieved_dttm':'','secret':'','sent_dttm':'','sum':resp["outputs"]["amount"][i],'termination_dttm':'','type':resp["outputs"]["offertype"][i],'visibility':1}
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
        LastMobile = {"LastRequestTime":strftime("%d.%m.%Y %H:%M:%S",gmtime()),"sys":sys,"wifi":wifi,"gps":gps,"beacon":beacon, "trigger": trigger,"opcode": "i"}
        result_mq = rabbitmq_add.delay('geo_mq','g_mq',json.dumps(message, ensure_ascii=False),'application/json','geo_mq')
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
        " SELECT ProdImg FROM [CIDB].[DataMart].[PRODIMG] WHERE ProdID IN (SELECT ProdID FROM [CIDB].[DataMart].[PRODUCTDETAILS] WHERE ProdDetId = "+proddetid+")")
        cur.execute(query)
        details = cur.fetchone()os
        proddet = {}
        proddet['ProdImg'] = details[0]
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
#                         BLOCK OF /GET OFFER IMAGES                                                                                                                                    #
#                                                                                                                                                                                           #
##############################################################################################################################################################
@app.route('/offer_img',  methods=['POST','OPTIONS','GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def offer_img():
    db = pymssql.connect(server = '172.28.106.17',user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
    offerid = request.json['offerid']
    if offerid != 0:
        cur = db.cursor()
        query = (
        " SELECT ProdImg FROM [CIDB].[DataMart].[PRODIMG] WHERE ProdID = (SELECT ProdID FROM [CIDB].[DataMart].[OFFER] WHERE OfferID = "+str(offerid)+")")
        cur.execute(query)
        return make_response(jsonify({'OfferImages':cur.fetchone()[0]}),200)
    return make_response(jsonify({"OfferImages":"OfferID shouldn't be equal to 0"}),200)


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
    result_mq = rabbitmq_add.delay('beacons_mq','b_mq',message,'application/json','beacons_mq')
  
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




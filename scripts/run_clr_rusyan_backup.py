#!/var/beacon/clr/bin/python 
# coding: utf-8
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         RATATOSKR WEB SERVICES 1.01                                                                                                                                       #
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
from ctasks import rabbitmq_add,mysql_select,call_rtdm,mssql_select,call_service
from datetime import timedelta,datetime
from flask import make_response, request, current_app
from functools import update_wrapper
from random import randint,choice
from ctasks import call_rtdm,post,facetztask,transgen
from celery.task.control import revoke
import copy
import datetime
import time
import pika
import requests
import MySQLdb
import pymssql
import psycopg2
import urllib
import re
import base64
import zmq

########################__CYRILLIC SYMBOLS SUPPORT__##########
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
##############################################################
########################__DURABLE STORE__#####################
import redis
import pickle
dur = redis.StrictRedis(host='localhost',port=6379,db=0)
##############################################################


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF GLOBAL VARIABLES                                                                                                                                         #
#                                                                                                                                                                                           #
############################################################################################################################################################################################
server_ip = '10.20.1.21'

app_server = "10.20.1.190"
web_server = "labinfo.sas-mic.local"
soa_server = "10.20.1.21:5000"

sync = 1
freq_in = 15
freq_out = 10
freq_sync = 20

rtdmpath = '10.20.1.190'
mssqlpath = '10.20.1.192'
mysqlpath = '10.20.1.20'
lunapath= '10.20.1.22'

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF COMMON FUNCTIONS                                                                                                                                         #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################

tvoffer = {'Title': 'ZoomZoom', 'Forename': 'ZoomZoom', 'Surname': 'ZoomZoom', 'OfferName': 'ZoomZoom', 'OfferDesc': 'ZoomZoom'}
red_tvoffer_def = dur.set('tvoffer_tmp_def',json.dumps(tvoffer))
red_tvflag = dur.set('tvflagpar',json.dumps(0))
#Head decorator
def crossdomain(origin=None, methods=None, headers=None,max_age=21600, attach_to_all=True,automatic_options=True, content=None):
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

#Get client information
def get_client(cid):
    db = MySQLdb.connect(host=mysqlpath, port = 3306, user="rusrat",passwd="Orion123", db="thebankfront",use_unicode = True,charset='UTF8')
    cur = db.cursor()
    query = "SELECT * FROM customers where CID="+str(cid)
    cur.execute(query)
    photoid = 0
    for row in cur.fetchall():
        output = row 
    return output




#Get client info by photoID
def get_cid_byphotoid(photoid):
    db = MySQLdb.connect(host=mysqlpath, port = 3306, user="rusrat",passwd="Orion123", db="thebankfront")
    cur = db.cursor()
    query = "SELECT * FROM customers where PhotoID="+str(photoid)
    cur.execute(query)
    cid = 0
    for row in cur.fetchall():
        cid = row[0]
    
    return cid

    
#Get all clients info
def get_all_clients():
    db = MySQLdb.connect(host=mysqlpath, port = 3306, user="rusrat",passwd="Orion123", db="thebankfront")
    cur = db.cursor()
    query = "SELECT * FROM customers where PhotoId > 0"
    cur.execute(query)
    list_of_images = []
    for row in cur.fetchall():
        list_of_images.append(int(row[26]))
    return list_of_images

#Get latest event in PostreSQL
def get_max_eventid_luna():
    db = psycopg2.connect(host=lunapath, port = 5432, user="testuser",password="password", dbname="FaceStreamRecognizer")
    cur = db.cursor()
    query2 = "SELECT MAX(event_id) FROM event"
    cur.execute(query2)
    data = cur.fetchone()
    max_eventid = data[0]
    return max_eventid






#Server start
app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_TASK_SERIALIZER'] = 'pickle'
app.config['CELERY_ACCEPT_CONTENT'] = 'pickle'

app.config.update(
    #BROKER_URL='amqp://guest:guest@localhost:5672//'
    BROKER_URL='redis://localhost:6379/0'
 )

celery = make_celery(app)


@app.route('/dbtest', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def get_clientu2():
    a = get_client(150001)
    return make_response(jsonify({a}),201)


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF SERVICES                                                                                                                                            #
#        
#source /var/beacon/clr/bin/activate
#cd /var/beacon/clr/scripts                                                                                                                                                                 #
#############################################################################################################################################################################################



@app.route('/zmqs', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def zmqs():
    context = zmq.Context() 
    reciever = context.socket(zmq.PULL)
    reciever.connect("tcp://10.20.1.24:80")
    res = reciever.recv_json()
    return make_response(jsonify({"Ratatoskr":'ok'}),201)


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
    

    event = "frontmainevent"
    rtdm_addr = "http://"+rtdmpath+"/RTDM/rest/runtime/decisions/"+event
    payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
    r = requests.post(rtdm_addr,json = payload)
    resp = str(r)
    return make_response(jsonify({"Ratatoskr":r.json()}),201)





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
        'time' :  datetime.datetime.strptime(time,"%d.%m.%Y %H:%M:%S").isoformat(sep='T'),
        'trigger':trigger}
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'Incorrect input.Details:'+str(e)}),415)    
    try:
        result_mysql_custdet = mysql_select('thebankfront','FirstName,MiddleName,LastName,CAST(DateOfBirth AS CHAR) ','customers',"CID="+str(cid))
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'SQL request seems to be incorrect. Here are details:'+str(e)}),416) 
    if spotname == "The Bank":
        area = "bank"
    elif spotname == "The Store":
        area = "retail"
    else:
        area = "sasrussia"
    if trigger != 'Luna':
        for row in result_mysql_custdet:
            payload = {"name":row[0],"surname":row[2],"middlename":row[1],"dob":str(row[3]),"id":cid,"status":"processing","reason":"visit","location":spotname,"area":area}
        try:
            result = call_service.apply_async(("active_queue",payload),retry=True)    
        except Exception as e:
            return make_response(jsonify({'Ratatoskr':'Some problems with python queue service.Further details: '+str(e)}),417)  
    try:
        rtdm = call_rtdm.apply_async((rtdmpath,"geomainevent",Geo),retry=True)      
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'Some problems with RTDM request.Further details: '+str(e)}),418)    
    return make_response(jsonify({'Ratatoskr':str(rtdm)}),200)



#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /EMAIL                                                                                                                                            #
#                                                                                                                                                                                           #
#####################################################################################################################################################
@app.route('/email', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def email():
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
        if 'Credit_Card' in template:
            OfferImg = merge_websiteurl["offerimg"]
            MainTxt = merge_websiteurl["maintxt"]
            DescTxt = merge_websiteurl["desctxt"]
            FName = merge_websiteurl["name"]
            LName = merge_websiteurl["lname"]
            MName = merge_websiteurl["mname"]
            ID = merge_websiteurl["id"]
            LangCode = merge_websiteurl["lang"]        
            url = "http://thebank.sas-mic.local/CreditScoring/creditcard.php%3Fofferimg="+OfferImg+"%26maintxt="+MainTxt+"%26desctxt="+DescTxt+"%26lname="+LName+"%26name="+FName+"%26mname="+MName+"%26id="+ID+"%26lang="+LangCode
        if 'Travel_Insurance' in template:
            ID = merge_websiteurl["id"]
            Title = merge_websiteurl["Title"]
            FName = merge_websiteurl["name"]
            LName = merge_websiteurl["lname"]
            MName = merge_websiteurl["mname"]
            LangCode = merge_websiteurl["lang"] 
            db = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
            cur = db.cursor()
            cur.execute("SELECT OfferID FROM [DataMart].[OFFER] WHERE IndivID="+str(ID)+" AND ProdID='5'")
            offerid = cur.fetchone()[0]
            url = "http://thebank.sas-mic.local/insurance.php%3Ftitle="+Title+"%26fname="+FName+"%26lname="+LName+"%26mname="+MName+"%26id="+ID+"%26lang="+LangCode+"%26offerid="+str(offerid)
        print url
    except Exception  as e:
        return make_response(jsonify({'Ratatoskr':e}),415)
    path = "https://api.elasticemail.com/v2/email/send?apikey="+apikey+"&subject="+subject+"&from="+fromw+"&from_name="+from_name+"&to="+tow+"&charset="+charset+"&template="+template+"&merge_title="+merge_title+"&merge_firstname="+merge_firstname+"&merge_lastname="+merge_lastname+"&merge_websiteurl="+url
    bool_tmp = dur.set('req_path',path)
    try:
        r = requests.get(dur.get('req_path')) 
        answer = r.content
    except:
        return make_response(jsonify({'Ratatoskr':'connection error'}),404)   
    return make_response(jsonify({'Ratatoskr':answer}),200)


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /Cameracheck                                                                                                                                      #
#                                                                                                                                                                                           #
##################################################################################################################################################### 

bool_tmp = dur.set('lunapar',json.dumps(1))#start LUNA with ON status

@app.route('/cameracheck', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def camparam():
     param = request.args.get('param')
     if param == 'True': 
         bool_tmp = dur.set('lunapar',json.dumps(1))
         maxid = get_max_eventid_luna()
         resultcam = post.apply_async([maxid])  
     else:
         bool_tmp = dur.set('lunapar',json.dumps(0))
     return make_response(jsonify({'Cameracheck':json.loads(dur.get('lunapar'))}),200)


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /Color Scheme                                                                                                                                     #
#                                                                                                                                                                                           #
#####################################################################################################################################################

bool_tmp = dur.set('SchemeColor',json.dumps({"Front":"rgb(91, 155, 213)","Retail":"rgb(251, 164, 78)"}))

@app.route('/color', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def color():
    if request.method == 'GET':
        return make_response(jsonify({'Color':json.loads(dur.get('SchemeColor'))}),200)
    if request.method == 'POST':
        try:
            context = request.json['context']
            color = request.json['color']
        except:
            return make_response(jsonify({'Color':'Invalid color input'}),400)
        dur_tmp = json.loads(dur.get('SchemeColor'))
        dur_tmp[context] = color
        bool_tmp = dur.set('SchemeColor',json.dumps(dur_tmp))
        return make_response(jsonify({'Color':'Color was successfully changed'}),200)


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /CredCardApp                                                                                                                                  #
#                                                                                                                                                                                           #
#####################################################################################################################################################
@app.route('/CredCardApp', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def CredCardApp():
    try:
        cost = request.json["cost"]
        limitpoints = request.json["limitpoints"]
        mycat = request.json["mycat"]
        country = request.json["country"]
        table = request.json["table"]
    except:
        return make_response(jsonify({'CredCardApp':'Incorrect input'}),400)
    url = "http://10.20.1.190/SASBIWS/services/CreditCardApp_WebService"
    headers = {'content-type':'text/xml'}
    body = """
           <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cred="http://tempuri.org/CreditCardApp_WebService">
           <soapenv:Header/>
           <soapenv:Body>
           <cred:creditCardApp_StoredProcces>
           <cred:parameters>
               <!--Optional:-->
               <cred:cost>"""+str(cost)+"""</cred:cost>
               <!--Optional:-->
               <cred:limitpoints>"""+str(limitpoints)+"""</cred:limitpoints>
               <!--Optional:-->
               <cred:mycat>"""+mycat+"""</cred:mycat>
               <!--Optional:-->
               <cred:country>"""+country+"""</cred:country>
               <!--Optional:-->
               <cred:table>"""+table+"""</cred:table>
           </cred:parameters>
           </cred:creditCardApp_StoredProcces>
           </soapenv:Body>
           </soapenv:Envelope>
           """
    try:
        response = requests.post(url,data=body,headers=headers)
    except Exception as e:
        return make_response(jsonify({'CredCardApp':e}),400)
    Miles = {}
    Points = {}
    Cashback = {}
    db = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
    cur = db.cursor()
    cur.execute("SELECT Id,Maintenance,Miles,Cash,Cashback,Points from [RTData].[CardSetId] WHERE Type = 'M'")
    data = cur.fetchone()
    if data is not None:
        Miles = {"Id":data[0],"Maintenance":data[1],"Miles":data[2],"Cash":data[3]}
    cur.execute("SELECT Id,Maintenance,Miles,Cash,Cashback,Points from [RTData].[CardSetId] WHERE Type = 'P'")
    data = cur.fetchone()
    if data is not None:
        Points = {"Id":data[0],"Maintenance":data[1],"Points":data[5]}
    cur.execute("SELECT Id,Maintenance,Miles,Cash,Cashback,Points from [RTData].[CardSetId] WHERE Type = 'C'")
    data = cur.fetchone()
    if data is not None:
        Cashback = {"Id":data[0],"Maintenance":data[1],"Cashback":data[4]}
    Output = {"Miles":Miles,"Points":Points,"Cashback":Cashback}
    return make_response(jsonify({'CredCardApp':Output}),200)
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /ESP UPDATE                                                                                                                                    #
#                                                                                                                                                                                           #
#####################################################################################################################################################
@app.route('/updateesp', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def espupdt():
    try:
        CardID = request.args.get('CardID')
        CardNumber = request.args.get('CardNumber')
        AccountID = request.args.get('AccountID')
        IndivID = request.args.get('IndivID')
        CardPin = request.args.get('CardPin')
        CardCVC = request.args.get('CardCVC')
        CardType = request.args.get('CardType')
        CardType2 = request.args.get('CardType2')
        CardValidFrom = "2019-08-21 21:00:00.00000000"
        CardValidTo = "2019-08-21 21:00:00.00000000"
        CardStatus = request.args.get('CardStatus')
        CardCashLimit = request.args.get('CardCashLImit')
        CardParam1 = request.args.get('CardParam1')
        CardParam2 = request.args.get('CardParam2')
        CardParam3 = request.args.get('CardParam3')
        CardParam4 = request.args.get('CardParam4')

        AccountValidFrom = "2019-08-21 21:00:00.00000000"
        AccountValidTo = "2019-08-21 21:00:00.00000000"
        AccountBalance = request.args.get('AccountBalance')
        AccountPrice = request.args.get('AccountPrice')
        ProdDetID = request.args.get('ProdDetID')
        AccountType = request.args.get('AccountType')
        AccountStatus = request.args.get('AccountStatus')
        AccountAmount = request.args.get('AccountAmount')
        AccountPayment = request.args.get('AccountPayment')
        AccountParam1 = request.args.get('AccountParam1')
        AccountParam2 = request.args.get('AccountParam2')
        AccountParam3 = request.args.get('AccountParam3')
        AccountParam4 = request.args.get('AccountParam4')
        HHoldID = request.args.get('HHoldID')
        Title = request.args.get('Title')
        Forename = request.args.get('Forename')
        Surname = request.args.get('Surename')
        Phone = request.args.get('Phone')
        Mobile = request.args.get('Mobile')
        Fax = request.args.get('Fax')
        Email = request.args.get('Email')
        CustomerSince = "2019-08-21 21:00:00.00000000"
        STATUS = request.args.get('STATUS')
        Birthdate = "2019-08-21 21:00:00.00000000"
        Agent = request.args.get('Agent')
        MarketingSegment = request.args.get('MarketingSegment')
        Random = request.args.get('Random')
        Middlename = request.args.get('Middlename')
        PhotoID = request.args.get('PhotoID')
        VipFlag = request.args.get('VipFlag')
        IndivParam1 = request.args.get('IndivParam1')
        IndivParam2 = request.args.get('IndivParam2')
        IndivParam3 = request.args.get('IndivParam3')
        IndivParam4 = request.args.get('IndivParam4')
        ProdDetName = request.args.get('ProdDetName')
        ProdID = request.args.get('ProdID')
        ProdDetDesc = request.args.get('ProdDetDesc')
        ProdDetImgID = request.args.get('ProdDetImgID')
        ProdDetPrice = request.args.get('ProdDetPrice')
        ProdDetStatus= request.args.get('ProdDetStatus')
        ProdDetRate= request.args.get('ProdDetRate')
        ProdDetAmount= request.args.get('ProdDetAmount')
        ProdDetPayment= request.args.get('ProdDetPayment')
        ProdDetBalance= request.args.get('ProdDetBalance')
        ProdDetLimit= request.args.get('ProdDetLimit')
        ProdDetPeriod= request.args.get('ProdDetPeriod')
        CashBackRate= request.args.get('CashBackRate')
        ProdDetValidFrom= "2019-08-21 21:00:00.00000000"
        ProdDetValidTo= "2019-08-21 21:00:00.00000000"
        ProdDetParam1= request.args.get('ProdDetParam1')
        ProdDetParam2= request.args.get('ProdDetParam2')
        ProdDetParam3= request.args.get('ProdDetParam3')
        ProdDetParam4= request.args.get('ProdDetParam4')
        ProdType= request.args.get('ProdType')
        ProdPrice= request.args.get('ProdPrice')
        ProdParam1= request.args.get('ProdParam1')
        ProdParam2= request.args.get('ProdParam2')
        ProdParam3= request.args.get('ProdParam3')
        ProdParam4= request.args.get('ProdParam4')
        ProdName= request.args.get('ProdName')
        ProdImgID= request.args.get('ProdImgID')
        ProdDesc= request.args.get('ProdDesc')
        ProdBrief= request.args.get('ProdBrief')
        Age= request.args.get('Age')
        AgeGroupID= request.args.get('AgeGroupID')
        Income= request.args.get('Income')
        IncomeGroupID= request.args.get('IncomeGroupID')
        Gender= request.args.get('Gender')
        JobID= request.args.get('JobID')
        LanguageID= request.args.get('LanguageID')
        MartialStatus= request.args.get('MartialStatus')
        EducationID= request.args.get('EducationID')
        ReligionID= request.args.get('ReligionID')
        JobStartDate= "2019-08-21 21:00:00.00000000"
        Children= request.args.get('Children')
        DriverLicense= request.args.get('DriverLicense')
        CarOwner= request.args.get('CarOwner')
        Username= request.args.get('Username')
        Password= request.args.get('Password')
        AccountCreated= "2019-08-21 21:00:00.00000000"
        LastLogin= "2019-08-21 21:00:00.00000000"
        DemogrParam1= request.args.get('DemogrParam1')
        DemogrParam2= request.args.get('DemogrParam2')
        DemogrParam3= request.args.get('DemogrParam3')
        DemogrParam4= request.args.get('DemogrParam4')
    except:
        return make_response(jsonify({'EspUpdate':'Input data is incorrect. Good luck!'}),418)  
    esp_url="http://ruscilabcomp:44445/SASESP/windows/CILAB_ver5_0/Continuous_Query_1/CARD/state?value=injected"
    esp_headers= {'content-type':'text/csv'}
    esp_event = "I,N,"+str(CardID)+","+str(CardNumber)+","+str(AccountID)+","+str(IndivID)+","+str(CardPin)+","+str(CardCVC)+","+str(CardType)+","+str(CardType2)+","+str(CardValidFrom)+","+str(CardValidTo)+","+str(CardStatus)+","+str(CardCashLimit)+","+str(CardParam1)+","+str(CardParam2)+","+str(CardParam3)+","+str(CardParam4)
    bin_esp_event = esp_event.encode()
    print esp_event

    esp_url2="http://ruscilabcomp:44445/SASESP/windows/CILAB_ver5_0/Continuous_Query_1/AccountDetailedView/state?value=injected"
    esp_event2 = "I,N,"+str(AccountID)+","+str(AccountValidFrom)+","+str(AccountValidTo)+","+str(IndivID)+","+str(AccountBalance)+","+str(AccountPrice)+","+str(ProdDetID)+","+str(AccountType)+","+str(AccountStatus)+","+str(AccountAmount)+","+str(AccountPayment)+","+str(AccountParam1)+","+str(AccountParam2)+","+str(AccountParam3)+","+str(AccountParam4)+","+str(HHoldID)+","+str(Title)+","+str(Forename)+","+str(Surname)+","+str(Phone)+","+str(Mobile)+","+str(Fax)+","+str(Email)+","+str(CustomerSince)+","+str(STATUS)+","+str(Birthdate)+","+str(Agent)+","+str(MarketingSegment)+","+str(Random)+","+str(Middlename)+","+str(PhotoID)+","+str(VipFlag)+","+str(IndivParam1)+","+str(IndivParam2)+","+str(IndivParam3)+","+str(IndivParam4)+","+str(ProdDetName)+","+str(ProdID)+","+str(ProdDetDesc)+","+str(ProdDetImgID)+","+str(ProdDetPrice)+","+str(ProdDetStatus)+","+str(ProdDetRate)+","+str(ProdDetAmount)+","+str(ProdDetPayment)+","+str(ProdDetBalance)+","+str(ProdDetLimit)+","+str(ProdDetPeriod)+","+str(CashBackRate)+","+str(ProdDetValidFrom)+","+str(ProdDetValidTo)+","+str(ProdDetParam1)+","+str(ProdDetParam2)+","+str(ProdDetParam3)+","+str(ProdDetParam4)+","+str(ProdType)+","+str(ProdPrice)+","+str(ProdParam1)+","+str(ProdParam2)+","+str(ProdParam3)+","+str(ProdParam4)+","+str(ProdName)+","+str(ProdImgID)+","+str(ProdDesc)+","+str(ProdBrief)+","+str(Age)+","+str(AgeGroupID)+","+str(Income)+","+str(IncomeGroupID)+","+str(Gender)+","+str(JobID)+","+str(LanguageID)+","+str(MartialStatus)+","+str(EducationID)+","+str(ReligionID)+","+str(JobStartDate)+","+str(Children)+","+str(DriverLicense)+","+str(CarOwner)+","+str(Username)+","+str(Password)+","+str(AccountCreated)+","+str(LastLogin)+","+str(DemogrParam1)+","+str(DemogrParam2)+","+str(DemogrParam3)+","+str(DemogrParam4)
    bin_esp_event2 = esp_event2.encode()
    print esp_event2

    esp_url3="http://ruscilabcomp:44445/SASESP/windows/CILAB_ver5_0/Continuous_Query_1/Accounts/state?value=injected"
    esp_event3 = "I,N,"+str(AccountID)+","+str(AccountValidFrom)+","+str(AccountValidTo)+","+str(IndivID)+","+str(AccountBalance)+","+str(AccountPrice)+","+str(ProdDetID)+","+str(AccountType)+","+str(AccountStatus)+","+str(AccountAmount)+","+str(AccountPayment)+","+'python'+","+str(AccountParam2)+","+str(AccountParam3)+","+str(AccountParam4)
    bin_esp_event3 = esp_event3.encode()
    print esp_event3

    try:      
        r = requests.put(esp_url3,data = bin_esp_event3,headers=esp_headers)
        r = requests.put(esp_url2,data = bin_esp_event2,headers=esp_headers)  
        r = requests.put(esp_url,data = bin_esp_event,headers=esp_headers)    
    except Exception as e:
        return make_response(jsonify({'EspUpdate':e}),400)
    return make_response(jsonify({'EspUpdate':bin_esp_event2}),200)  
    



#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /ServicesStatus                                                                                                                                  #
#                                                                                                                                                                                           #
####################################################################################################################################################

@app.route('/ServicesStatus', methods=['GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def ServicesStatusGET():
     Services = {"atm":json.loads(dur.get('atm_status')),"transgen":json.loads(dur.get('transgenpar')),"facetz":json.loads(dur.get('facetzpar')),"luna":json.loads(dur.get('lunapar'))}
     return make_response(jsonify({'Ratatoskr':Services}),200)  


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /LoyaltyScore                                                                                                                               #
#                                                                                                                                                                                           #c
####################################################################################################################################################

@app.route('/loyalty', methods=['GET','POST','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def loyalty():
    try:
        cid = request.json['cid']
    except:
        return make_response(jsonify({'Loyalty':'input data is corrupt'}),418)
    db = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
    cur = db.cursor()
    cur.execute('SELECT Max(LoyaltyScore) FROM [DataMart].[CARD] WHERE IndivID = '+str(cid))
    loyalty = cur.fetchone()
    return make_response(jsonify({'Loyalty':loyalty[0]}),200) 



#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /SERVICE LIST                                                                                                    #
#                                                                                                                                                                                           #
##################################################################################################################################################

bool_tmp = dur.set('ServiceList',json.dumps({"Offurl":'ruscilab.sas-mic.local',"Mesurl":'10.20.1.21:5000',"Infurl":'labinfo.sas-mic.local'}))

@app.route('/service_list',  methods=['POST','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def service_list_post():
    try:
        offurl = request.json['offurl']
        mesurl = request.json['mesurl']
        infurl = request.json['infurl']
    except:
        return make_response(jsonify({'Ratatoskr':'Input error'}),415)  
    dur_tmp = json.loads(dur.get('ServiceList'))
    if offurl != "":
         dur_tmp['Offurl'] = offurl
    if mesurl != "":
         dur_tmp['Mesurl'] = mesurl
    if infurl != "":
         dur_tmp['Infurl'] = infurl
    bool_tmp = dur.set('ServiceList',json.dumps(dur_tmp))
    return make_response(jsonify({'Ratatoskr':'Service list has been successfully updated'}),200)  

@app.route('/service_list',  methods=['GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def service_list_get():
    return make_response(jsonify({'Ratatoskr':json.loads(dur.get('ServiceList'))}),200)  
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /Contact Policy                                                                                                                                              #
#                                                                                                                                                                                           #
#####################################################################################################################################################
@app.route('/contactpol', methods=['POST','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def contactpol():
    try:
        #link = request.json['link']
        #login = request.json['login']
        #psw = request.json['psw']
        individ = request.json['IndivID']
        phones = request.json['phones']
        mes = request.json['mes']
        channel = request.json['Channel']
        sender = request.json['sender']
        param1 = request.json['param1']
        param2 = request.json['param2']
        param3 = request.json['param3']
        param4 = request.json['param4']
    except:
        return make_response(jsonify({'ContactPolicy':'Incorrect input'}),418)
    inputs={"IndivID":individ,"Channel":channel,"phones":phones,"mes":mes,"sender":sender,"param1":param1,"param2":param2,"param3":param3,"param4":param4}
    dns = "10.20.1.190"
    event = "smsevent"
    rtdm_addr = "http://"+dns+"/RTDM/rest/runtime/decisions/"+event
    payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}    
    try:
        result = call_rtdm.apply_async((dns,"smsevent",inputs),retry=True)  
    except Exception as e:
        return make_response(jsonify({'ContactPolicy':e}),400)
    return make_response(jsonify({'ContactPolicy':'Success'}),200)  
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /SMS                                                                                                                                              #
#                                                                                                                                                                                           #
#####################################################################################################################################################
@app.route('/sms', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def sms():
    try:
        login =  request.args.get("login") 
        psw = request.args.get("psw")
        phones = request.args.get("phones")
        mes = request.args.get("mes")
        sender = request.args.get("sender")
    except Exception:
        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415)    
    bool_tmp = dur.set('req_path',"https://smsc.ru/sys/send.php?charset=utf-8&login="+login+"&psw="+psw+"&phones="+phones+"&mes="+mes+"&sender="+sender )
    try:
        r = requests.get(dur.get('req_path')) 
        answer = r.content
    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'Ratatoskr':'connection error'}),404)   
    return make_response(jsonify({'Ratatoskr':'Success!'}),200)


### TVBESTOFFER ###

@app.route('/tvbestoffer', methods=['GET', 'OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def tvbestoffer():
    try:
        title = request.args.get("Title")
        forename = request.args.get("Forename")
        surname = request.args.get("Surname")
        offername = request.args.get("OfferName")
        offerdesc = request.args.get("OfferDesc")
    except Exception:
        return make_response(jsonify({'Ratatoskr':'Input data is incorrect'},415))
    tvoffer = {'Title': title, 'Forename': forename, 'Surname': surname, 'OfferName': offername, 'OfferDesc': offerdesc}
    red_tvoffer = dur.set('tvoffer_tmp',json.dumps(tvoffer))#1st changed string
    red_tvflag = dur.set('tvflagpar',json.dumps(1))
    return make_response(jsonify({'Ratatoskr':str(tvoffer)}),200)

##################

### TVSTATUS ###

@app.route('/tvstatus', methods=['GET', 'OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def tvstatus():
    red_tvflag = dur.get('tvflagpar')
    tvoffer = dur.get('tvoffer_tmp')
    #print ("Current TVFLAG Value is: " + str(red_tvflag))
    try:
        reset = request.args.get("reset")
        if reset is not None:
            red_tvflag = dur.set('tvflagpar',json.dumps(0))
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':str(e)+str(reset)}),400)
    try:
        if int(red_tvflag) == 0:
            #tvoffer_def = dur.get('tvoffer_tmp_def')
            return make_response(jsonify({'Ratatoskr':json.loads(dur.get('tvoffer_tmp_def'))}),200)
        else:
            return make_response(jsonify({'Ratatoskr':json.loads(dur.get('tvoffer_tmp'))}),200)
    except Exception:
        return "Something Goes Wrong" #make_response(jsonify({'Ratatoskr': 'NoData'}),415)

################



#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /
#FasetZ                                                                                                                     #
#                                                                                                                                                                                           #
####################################################################################################################################################
#Initialization of active sessions list
#bool_tmp = dur.set('Sesslist',json.dumps([]))
if dur.get('Sesslist') == None:
    bool_tmp = dur.set('Sesslist',json.dumps([]))

@app.route('/facetz2', methods=['GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def facetz2():
    cid =  request.args.get("cid") 
    url = "https://api.facetz.net/v2/facts/user.json?key=51af6192-c812-423d-ae25-43a036804632&query={%22user%22:{%22id%22:%22"+cid+"%22},%22ext%22:{%22exchangename%22:%22sas_demo%22}}"
    Formatted = []
    try:
        r = requests.get(url)
        Formatted.append({"id":r.json()['id']})
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'Facetz is not responding'}),404)  
    i=1
    try:
        for el in r.json()['visits']:
            formatted_el = {}
            formatted_el['number'] = i
            formatted_el['ts'] = datetime.datetime.strftime(datetime.datetime.fromtimestamp(el['ts']/1000),"%Y-%m-%d %H:%M:%S")
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
        return make_response(jsonify({'Ratatoskr':Formatted}),200)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'Other error'}),404)  




bool_tmp = dur.set('facetzpar',json.dumps(1))#Set Facets service ON status
@app.route('/facetzmanage', methods=['GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def facetzmanage(): 
    param = request.args.get("param")
    if param == "True":
        try:
            bool_tmp = dur.set('facetzpar',json.dumps(1))
            resultface = facetztask.apply_async()  
        except Exception as e:
            return make_response(jsonify({'Ratatoskr':'facetztask is not invoking'}),404)  
    else:
        bool_tmp = dur.set('facetzpar',json.dumps(0))
        dur_tmp = json.loads(dur.get('Sesslist'))
        dur_tmp = []
        bool_tmp = dur.set('Sesslist',json.dumps(dur_tmp))
    return make_response(jsonify({'Facetzmanage':json.loads(dur.get('facetzpar'))}),200)
    
    
@app.route('/facetzshit', methods=['GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def facetzshit(): 
    
    while json.loads(dur.get('facetzpar')) == 1: 
        dur_tmp = json.loads(dur.get('Sesslist'))
        for sessid in dur_tmp:
            try:
                url = "https://api.facetz.net/v2/facts/user.json?key=51af6192-c812-423d-ae25-43a036804632&query={%22user%22:{%22id%22:%22"+sessid+"%22},%22ext%22:{%22exchangename%22:%22sas_demo%22}}"
                Formatted = []
                r = requests.get(url)
                return make_response(jsonify({'Facetzmanage':str(r)}),500)
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
            except Exception as e:
                return make_response(jsonify({'Facetzmanage':str(e)}),500)
            try:
                if dur_tmp != []:
                    Result = {"sys":{"id":r.json()['id']},"site":Formatted}
                    que_result = rabbitmq_add('facetz_mq','f_mq',json.dumps(Result,ensure_ascii=False),'application/json','facetz_mq')
                    return make_response(jsonify({'Facetzshit':'queue'}),418)
            except Exception as e:
                return make_response(jsonify({'Facetzmanage':'Error lev 2'}),500)
    print ("djiodqwlkjqwdlkjqwdlkj")
    return make_response(jsonify({'Facetzshit':json.loads(dur.get('facetzpar'))}),200)
    


@app.route('/facetz', methods=['GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def facetz():
    visitid =  request.args.get("visitid") 
    dur_tmp = json.loads(dur.get('Sesslist'))
    if visitid is None:
        return make_response(jsonify({'Ratatoskr':json.loads(dur.get('Sesslist'))}),201)
    if visitid not in dur_tmp and json.loads(dur.get('facetzpar')) == 1:
        dur_tmp.append(visitid)
        bool_tmp = dur.set('Sesslist',json.dumps(dur_tmp))
        return make_response(jsonify({'Ratatoskr':'VisitID has been added to Lesslist'}),200)
    else:
        return make_response(jsonify({'Ratatoskr':'This visitid is already exists'}),200)

     

        

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /
#Online Bank Login                                                                                                                   #
#                                                                                                                                                                                           #
##################################################################################################################################################
@app.route('/obank', methods=['POST','GET','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def obank():
    try:
        sessid = request.json['sessid']
    except:
        sessid = "NULL"
    try:    
        login = request.json['login']
    except:
        login = "NULL"
    try:
        phone = request.json['phone']
    except:
        phone = "NULL"
    try:
        email = request.json['email']
    except:
        email = "NULL"
    fields = "(SessionID,"
    vals = "('"+sessid+"',"
    if login != "":
        fields += 'Login,' 
        vals += "'"+login+"',"
    if phone != "":
        fields += 'Phone,'
        vals += "'"+phone+"',"
    if email != "":
        fields += 'Email,'
        vals += "'"+email+"',"
    fields += "Timestamp)"
    vals += str(int(time.time()))+")"
    conn = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB')
    cursor = conn.cursor()
    if phone != "" or email != "" or login != "":
        cursor.execute("INSERT INTO [DataMart].[FACETZ] "+fields+" VALUES "+vals)
        conn.commit()
    esp_url="http://ruscilabcomp:44445/SASESP/windows/CI_Facetz/Continuous_Query_1/Facetz/state?value=injected"
    esp_headers= {'content-type':'text/csv'}
    esp_event = "I,N,"+sessid+","+email+","+phone+","+login+","+str(int(time.time()))
    bin_esp_event = esp_event.encode()
    try:
        r = requests.put(esp_url,data = bin_esp_event,headers=esp_headers)
    except Exception as e:
        return make_response(jsonify({'OnlineBank':str(e)}),418)
        #return make_response(jsonify({'OnlineBank':e}),418)
    return make_response(jsonify({'OnlineBank':r.content}),200)

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /
#DPI                                                                                                                        #
#                                                                                                                                                                                           #
####################################################################################################################################################
@app.route('/dpi', methods=['POST','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def dpi():
    try:
        timestamp = request.json['timestamp']
        ip = request.json['ip']
        hash_ = request.json['hash']
        ua = request.json['ua']
        domain = request.json['domain']
        uri = request.json['uri']
        cookie = request.json['cookie']
        referer = request.json['referer']
    except:
        return make_response(jsonify({'DpiService':'Input is incorrect'}),418)
    return make_response(jsonify({'DpiService':'Success'}),200)
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
        LanguageID = request.args.get("LanguageID")
        Password = request.args.get("Password")
        Title = request.args.get("Title")
        Street = request.args.get("Street").encode('utf-8') 
        State = request.args.get("State").encode('utf-8') 
    except:
        return make_response(jsonify({'Ratatoskr':'Input is incorrect'}),400)    
    try:
        conn = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB')
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

    sql1="UPDATE [DataMart].[INDIVIDUAL] SET Forename ='"+str(FirstName)+"',Surname='"+str(LastName)+"',Middlename='"+str(MiddleName)+"',Mobile='"+str(MobileNumber)+"',Birthdate='"+str(DateOfBirth)+"',Email='"+str(Email)+"',Phone='"+str(PhoneNumber)+"',"
    if Title != 'undefined':
        sql1 += "Title='"+str(Title)+"',"
    sql1 += "PhotoID='"+str(PhotoID)+"' WHERE IndivID="+str(CID)+""
    print sql1

    sql2 = "UPDATE [DataMart].[INDIVIDUAL_DEMOGRAPHIC] SET Gender = '"+str(Gender)+"',Age='"+str(Age)+"',AgeGroupID='"+str(AgeGroup)+"',MartialStatus='"+str(MaritalStatus)+"',Children='"+str(Children)+"',EducationID='"+str(Education)+"',JobID='"+str(Occupation)+"',"
    if LanguageID != 'undefined':
        sql2 += "LanguageID='"+str(LanguageID)+"',"
    if Password != 'undefined':
        sql2 += "Password='"+str(Password)+"',"
    sql2 += "Income='"+str(Income)+"' WHERE IndivID="+str(CID)+""
    print sql2


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
    bool_tmp = dur.set('LastMobileGet',json.dumps({"LastRequestTime":strftime("%d.%m.%Y %H:%M:%S",gmtime()),"cid":cid}))
    db = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
    cur = db.cursor()
#CID IS NOT SPECIFIED
    if cid is None:
        query_customers = "Login is not null ORDER BY CID DESC"
        query_tranz = ''
        query_offers = None
        query_prods = "WHERE IndivID > 0"
        query_prods_det = None
        query_beacon = None
        query_wifi = None
        query_gps = None
        try:
            result_mssql_offers = mssql_select('CIDB','DataMart',None,'OFFER',query_offers)
            result_mssql_offimg = mssql_select('CIDB','DataMart','ProdImg','PRODIMG',query_offers)
            query = (" SELECT t2.ProdType,t3.ProdImg from [CIDB].[DataMart].[OFFER] as t1 inner join [CIDB].[DataMart].[PRODUCT] as t2 on t1.ProdID = t2.ProdID inner join [CIDB].[DataMart].[ProdImg]  as t3 on t2.ProdID = t3.ProdID")
            cur.execute(query)
            prodtype = cur.fetchall()
            query = ("Select a1.IndivID,LScore from ((select * from [DataMart].[INDIVIDUAL_DEMOGRAPHIC] where Password <> '0' and IndivID > '150000') as a1 left join (select IndivID,CAST(MAX(LoyaltyScore)as INT) as LScore from [DataMart].[CARD] GROUP BY IndivID) as a2 on a1.IndivID = a2.IndivID) ORDER BY IndivID DESC")
            cur.execute(query)
            loyalty = cur.fetchall()            
            #GET OFFERS
            """
            i = 0
            for row in result_mssql_offers:
                offer = {}
                offer["clientid"] = row[23]
                offer["offerid"] = row[20]
                offer["name"] = row[0]
                offer["duration"] = 12
                offer["type"] = prodtype[i][0]
                offer["description"] = row[19]
                offer["sum"] = row[3]
                #offer["image"] = prodtype[i][1]
                offer["image"] = ''
                offer["rate"] = row[2]
                offer["payment"] = row[4]
                offer["secret"] = ''
                offer["visibility"] = 1
                offer["priority"] = row[22]
                offer["generated_dttm"] = int(round(time.time()*1))
                offer["recieved_dttm"] = int(round(time.time()*1))
                offer["termination_dttm"] = int(round(time.time()*1))
                offer["sent_dttm"] = int(round(time.time()*1))
                Offers.append(offer)
                i+=1"""
        except Exception as e:
            response = {"Ratatoskr":e}
            print str(response)
            return make_response(jsonify(response),500)

#CID IS SPECIFIED
    else:
        try:
            inputs = {"cid":int(cid),"channel":channel,"context":context,"device":device,"regtime":regtime,"reqtime":reqtime,"timezone":timezone,"param1":param1,
"param2":param2,"param3":param3,"param4":param4,"param5":param5,"param6":param6,"param7":param7}       
            event = "frontmainevent"
            rtdm_addr = "http://"+rtdmpath+"/RTDM/rest/runtime/decisions/"+event
            payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
            r = requests.post(rtdm_addr,json = payload)
            resp = r.json()
            #request for offer images
            temp_table =("CREATE TABLE #TEMP (offercode int,ord int)")
            cur.execute(temp_table)
            for k in range(len(resp['outputs']['offercode'])):
                insert_order = "INSERT INTO #TEMP(offercode,ord) VALUES("+str(resp['outputs']['offercode'][k])+","+str(k)+")"
                cur.execute(insert_order)
            query = (
            " WITH TEMP as (SELECT ProdID,offercode,ord,IndivID from [CIDB].[DataMart].[OFFER] as t1 INNER JOIN #TEMP as t2 on t1.OfferID =    t2.offercode)" 
            " SELECT t3.ProdImg FROM TEMP as t1 inner join [CIDB].[DataMart].[OFFER] as t2 on t1.ProdID = t2.ProdID and t1.IndivID = t2.IndivID inner join [CIDB].[DataMart].[PRODIMG] as t3 on t1.ProdID = t3.ProdID ORDER BY ord")
            cur.execute(query)
            off_imgs = cur.fetchall()
            cur.execute("DROP TABLE #TEMP")   
            if len(off_imgs) < 3:
                for l in range(3-len(off_imgs)):
                    off_imgs.append(" ");
            i = 0
            for row in resp["outputs"]["offercode"]:
                offer = {'clientid': str(int(resp["outputs"]["cid"])), 'description':resp["outputs"]["advdetails"][i], 'generated_dttm':int(round(time.time()*1)),'image':off_imgs[i][0],'name':resp["outputs"]["offername"][i],'offerid':int(resp["outputs"]["offercode"][i]),'payment':resp["outputs"]["payment"][i],'priorigty':int(resp["outputs"]["prio"][i]),'rate':resp["outputs"]["rate"][i],'duration':12,'recieved_dttm':int(round(time.time()*1)),'secret':'','sent_dttm':int(round(time.time()*1)),'sum':resp["outputs"]["amount"][i],'termination_dttm':int(round(time.time()*1)),'type':resp["outputs"]["offertype"][i],'visibility':1}
                Offers.append(offer)
                i += 1
        except Exception as e:
            response = {"Ratatoskr":"R:"+str(e)}
            return make_response(jsonify(response),500)      
        try:
            resp = r.json()
            response = {"Ratatoskr":"Try was OK calling NBO:"+str(resp)+str(rtdmpath)}
        except Exception:
            response = {"Ratatoskr":"Error calling NBO:"+str(Exception)+str(rtdmpath)}
            return make_response(jsonify(response),500)
        query_customers = "Login is not null AND CID ="+cid
        query_tranz = " WHERE t2.AccountID IN (SELECT AccountID from [DataMart].[Account] WHERE IndivID= "+cid+")"
        query_offers = 'IndivID ='+cid
        query_prods = "WHERE IndivID ="+cid
        query_beacon = None
        query_wifi = None
        query_gps = None
        query = ("Select IndivID,CAST(MAX(LoyaltyScore) as INT) as LScore from [DataMart].[CARD] WHERE IndivID="+cid+" GROUP BY IndivID")  
        cur.execute(query)  
        loyalty = cur.fetchall()
        if loyalty == []:
             loyalty = [(0,0)]
        print loyalty
    try:
        result_mysql_sel = mysql_select('thebankfront',None,'customers',query_customers)
        result_mssql_offers = mssql_select('CIDB','DataMart',None,'OFFER',query_offers)
        result_mysql_beacon = mysql_select('ratatoskr',None, 'BEACONS',query_beacon)
        result_mysql_wifi = mysql_select('ratatoskr',None, 'WIFI',query_wifi)
        result_mysql_gps = mysql_select('ratatoskr',None, 'GPS',query_gps)
        query = (
        " SELECT ProdDetRate,ProdDetAmount,ProdDetPayment,ProdDetPeriod,ProdDetName,t1.ProdDetID,t1.ProdID,t2.ProdDesc,t2.ProdName,t2.ProdType,t3.IndivId,t1.ProdDetValidFrom,t1.ProdDetValidTo,t2.ProdType,t4.ProdImg "
        " FROM [CIDB].[DataMart].[PRODUCTDETAILS] as t1 inner join [CIDB].[DataMart].[PRODUCT] as t2 on t1.ProdID = t2.ProdID inner join [CIDB].[DataMart].[ACCOUNT] as t3 on t3.ProdDetID = t1.ProdDetID inner join [CIDB].[DataMart].[PRODIMG] as t4 on t1.ProdID = t4.ProdID"
        " WHERE t1.ProdDetID IN (SELECT ProdDetID FROM [CIDB].[DataMart].[ACCOUNT]"+query_prods+")")
        cur.execute(query)
        prodqres = cur.fetchall()   
        transq = ("SELECT t1.TermID,t1.TransSum,t1.TransDate,t1.TransID,t2.IndivID FROM [CIDB].[TRANSData].[TRANSACTION] as t1 inner join [CIDB].[DataMart].[ACCOUNT] as t2 on t1.AccountID = t2.AccountID " + query_tranz)
        cur.execute(transq)
        transqres = cur.fetchall()
    except Exception as e:
        response = {"Ratatoskr":e}
        return make_response(jsonify(response),500)


#GET CLIENTS
    lcnt = 0
    for row in result_mysql_sel:
        client = {}
        client["clientid"] = row[0]
        client["clientimage"]=row[25].replace(" ","+")
        #client["clientimage"]=(row[25].replace(" ","+"),'')[cid == None]
        client["name"] = row[1]
        client["surname"] = row[3]
        client["email"] = row[16]
        client["phone"] = row[5]
        client["login"] = row[27]
        client["password"] = row[28]
        #client["loyaltyscore"] = (loyalty[lcnt][1],0)[loyalty[lcnt][1] == None]
        client["loyaltyscore"] = 0
        Clients.append(client)
        lcnt += 1
#GET PRODUCTS
    for row in prodqres:
        product = {} 
        product["clientid"] = int(row[10])
        product["sum"] = row[1]
        product["duration"] = row[3]
        product["image"] = (row[14],'')[cid == None]
        product["rate"] = row[0]
        product["payment"] = row[2]
        product["productid"] = row[5]
        product["purchased_dttm"] = row[11]
        product["exparation_dttm"] = row[12]
        product["name"] = row[4]    
        product["type"] = row[13]
        product["description"] = row[7]
        Products.append(product)
#GET SETTINGS
    Settings = []
    setting =    {
    "app_server" : app_server,
    "web_server" : web_server,
    "soa_server" : soa_server,
    "sync" : sync,
    "freq_in" : freq_in,
    "freq_out" : freq_out,
    "freq_sync" : freq_sync}
    Settings.append(setting)
#GET TRANSACTIONS
    for row in transqres:
        tranz = {}
        tranz["tranid"] = row[3]
        tranz["agent"] = row[0]
        tranz["sum"] = row[1]
        tranz["tran_dttm"] =str(int(time.mktime(row[2].timetuple())))
        tranz["clientid"] =  str(row[4])
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
    conn = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB')
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

#bool_tmp = dur.set('HistArr',json.dumps([]))

if dur.get('HistArr') == None:
    bool_tmp = dur.set('HistArr',json.dumps([]))


@app.route('/mobile_post', methods=['POST','GET','OPTIONS'])
def mobile_post_all():
    dur_tmp =json.loads(dur.get('HistArr'))
    dur_tmp.append({strftime("%d.%m.%Y %H:%M:%S",gmtime()):json.loads(request.data)})
    dur.set('HistArr',json.dumps(dur_tmp))
    try:
        sys = request.json['sys']
        wifi = request.json['wifi']
        beacon = request.json['beacon']
        gps = request.json['gps']
        trigger =  request.json['trigger']
        bool_tmp = dur.set('LastMobile',json.dumps({"LastRequestTime":strftime("%d.%m.%Y %H:%M:%S",gmtime()),"sys":sys,"wifi":wifi,"gps":gps,"beacon":beacon, "trigger": trigger,"opcode": "i"}))
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415)
    if sys["clientid"]>150000:
        message = {"sys":sys,"wifi":wifi,"gps":gps,"beacon":beacon, "trigger": trigger,"opcode": "i"}
        result_mq = rabbitmq_add.delay('geo_mq','g_mq',json.dumps(message, ensure_ascii=False),'application/json','geo_mq')
        return make_response(jsonify({'Ratatoskr':'request processed'}),201)
    else:
        return make_response(jsonify({'Ratatoskr':'incorrect request data'}),418)



@app.route('/hist', methods=['GET'])
def hist():
    return make_response(jsonify({"Ratatoskr":json.loads(dur.get('HistArr'))}),200)





#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /GET LAST RESULTS                                                                                                                                           #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/getlast', methods=['GET'])
def lastrequest():
    if dur.get('LastLaunch') == None:
        bool_tmp = dur.set('LastLaunch',json.dumps([]))
    if dur.get('LastOffer') == None:
        bool_tmp = dur.set('LastOffer',json.dumps([]))
    if dur.get('LastMobile') == None:
        bool_tmp = dur.set('LastMobile',json.dumps([]))
    if dur.get('LastSync') == None:
        bool_tmp = dur.set('LastSync',json.dumps([]))
    if dur.get('LastMobileGet') == None:
        bool_tmp = dur.set('LastMobileGet',json.dumps([]))
    try:
        return make_response(jsonify({'launch':json.loads(dur.get('LastLaunch')),'offer_accept':json.loads(dur.get('LastOffer')),'mobile_post':json.loads(dur.get('LastMobile')),'sync_updt':json.loads(dur.get('LastSync')),'mobile_get':json.loads(dur.get('LastMobileGet'))}),200)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':e}),415)

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
    db = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
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
    query = ("SELECT DISTINCT CAST(t3.MCC AS int) FROM [TRANSData].[TRANSACTION] as t1 inner join [TRANSData].[TERMINAL] as t2 on t1.TermID = t2.TermID inner join [TRANSData].[MCC] as t3 on t2.MCC = t3.MCC WHERE TransStatus='ok' AND TransSum>0 AND TransType = 1 AND AccountID IN (SELECT AccountID FROM [DataMart].[ACCOUNT] WHERE IndivID="+cid+")")
    cur = db.cursor()
    cur.execute(query) 
    mcc = cur.fetchall()
    query3 = ("SELECT SUM(TransSum) FROM [TRANSData].[TRANSACTION] as t1 inner join [TRANSData].[TERMINAL] as t2 on t1.TermID = t2.TermID inner join [TRANSData].[MCC] as t3 on t2.MCC = t3.MCC WHERE TransStatus='ok' AND TransSum>0 AND TransType = 1 AND AccountID IN (SELECT AccountID FROM [DataMart].[ACCOUNT] WHERE IndivID="+cid+")")
    cur.execute(query3) 
    transsum = cur.fetchone()[0]
    MCC = []
    Result = []
    for row in mcc:
        MCC.append(row[0])
    for row in MCC:
        query2 = ("SELECT  SUM(TransSum) FROM [TRANSData].[TRANSACTION] as t1 inner join [TRANSData].[TERMINAL] as t2 on t1.TermID = t2.TermID inner join [TRANSData].[MCC] as t3 on t2.MCC = t3.MCC WHERE t3.MCC = "+str(row)+" AND TransStatus='ok'AND TransType = 1 AND AccountID IN (SELECT AccountID FROM [DataMart].[ACCOUNT] WHERE IndivID="+cid+")")
        query4 = ("SELECT  t3.MCCName FROM [TRANSData].[TRANSACTION] as t1 inner join [TRANSData].[TERMINAL] as t2 on t1.TermID = t2.TermID inner join [TRANSData].[MCC] as t3 on t2.MCC = t3.MCC WHERE t3.MCC = "+str(row)+" AND TransStatus='ok'AND TransSum>0 AND TransType = 1 AND AccountID IN (SELECT AccountID FROM [DataMart].[ACCOUNT] WHERE IndivID="+cid+")")
        cur.execute(query2) 
        mccsum = cur.fetchone()[0]
        cur.execute(query4) 
        mcccat = cur.fetchone()[0]
        percent = (mccsum/transsum)*100
        MCCSUM = {"Category":mcccat,"Sum":mccsum,"Percent":percent}
        Result.append(MCCSUM)
    return make_response(jsonify({'Transaction_list':tr,'Aggregate':Result}),200)


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /NEW PRODUCTS                                                                                                                                    #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/new_products', methods=['POST','OPTIONS','GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def new_products():
    db = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
    cid = request.args.get('cid')
    proddetid = request.args.get('proddetid')
    if (proddetid is not None):
        cur = db.cursor()
        query = (
        " SELECT ProdImg FROM [CIDB].[DataMart].[PRODIMG] WHERE ProdID IN (SELECT ProdID FROM [CIDB].[DataMart].[PRODUCTDETAILS] WHERE ProdDetId = "+proddetid+")")
        cur.execute(query)
        details = cur.fetchone()
        proddet = {}
        proddet['ProdImg'] = details[0]
        return make_response(jsonify({'ProductsDetails':proddet}),200)
    if (cid is not None):
        Products=[]         
        cur = db.cursor()
        query = (
                " SELECT ProdDetRate,ProdDetAmount,ProdDetPayment,ProdDetPeriod,ProdDetName,t1.ProdDetID,t1.ProdID,t1.ProdDetDesc,t2.ProdName,t2.ProdType,t1.ProdDetValidFrom,t1.ProdDetValidTo"
        " FROM [CIDB].[DataMart].[PRODUCTDETAILS] as t1 inner join [CIDB].[DataMart].[PRODUCT] as t2 on t1.ProdID = t2.ProdID inner join [CIDB].[DataMart].[ACCOUNT] as t3 on t3.ProdDetID = t1.ProdDetID"
        " WHERE t1.ProdDetID IN (SELECT ProdDetID FROM [CIDB].[DataMart].[ACCOUNT] WHERE IndivID='"+cid+"')")
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
#                         BLOCK OF /BUY PRODS                                                                                                    #
#                                                                                                                                                                                           #
########################################################################################################################################################
@app.route('/buyprod', methods=['POST','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def buyprod():
    try:
        prodname = request.args.get('prodname')
        amount = request.json['amount']
        cid = request.json['cid']
        purdate = request.json['purdate']
    except:
        return make_response(jsonify({'BuyProdService':'incorrect input'}),400) 
    db = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
    cur = db.cursor()
    cur.execute("INSERT INTO [CIDB].[DataMart].[BUYPROD] VALUES ("+str(cid)+",'"+prodname+"',"+str(amount)+",'"+str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+"')")
    db.commit()
    return make_response(jsonify({'BuyProdService':'ok'}),200)

@app.route('/buyprod', methods=['GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def getbuyprod():
    try:
        cid = request.args.get('cid')
    except:  
        return make_response(jsonify({'BuyProdService':'incorrect input'}),400) 
    db = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
    cur = db.cursor()
    cur.execute("SELECT * FROM [CIDB].[DataMart].[BUYPROD] WHERE cid = "+cid)    
    prods = cur.fetchall()
    Result = []
    for row in prods:
         prod={}
         prod['cid'] = row[0]
         prod['prodname'] = row[1]
         prod['amount'] = row[2]
         prod['date'] = row[3]
         Result.append(prod)
    return make_response(jsonify({'BuyProdService':Result}),200)
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /GET OFFER IMAGES                                                                                                                                    #
#                                                                                                                                                                                           #
##############################################################################################################################################################
@app.route('/offer_img',  methods=['POST','OPTIONS','GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def offer_img():
    db = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
    cur = db.cursor()
    offerid = request.json['offerid']
    if offerid != 0:
        offcodes = re.findall("\d+",offerid)
        temp_table =("CREATE TABLE #TEMP (offercode int,ord int)")
        cur.execute(temp_table)
        for i in range(len(offcodes)):
            insert_order = "INSERT INTO #TEMP(offercode,ord) VALUES("+str(offcodes[i])+","+str(i)+")"
            cur.execute(insert_order)
        query = (
        " WITH TEMP as (SELECT ProdID,offercode,ord,IndivID from [CIDB].[DataMart].[OFFER] as t1 INNER JOIN #TEMP as t2 on t1.OfferID = t2.offercode)" 
        " SELECT t3.ProdImg FROM TEMP as t1 inner join [CIDB].[DataMart].[OFFER] as t2 on t1.ProdID = t2.ProdID and t1.IndivID = t2.IndivID inner join [CIDB].[DataMart].[PRODIMG] as t3 on t1.ProdID = t3.ProdID ORDER BY ord")
        cur.execute(query)
        tst = cur.fetchall()
        cur.execute("DROP TABLE #TEMP")       
        return make_response(jsonify({'OfferImages':tst}),200)
    else:
        return make_response(jsonify({"OfferImages":"OfferID shouldn't be equal to 0"}),418)




#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /NEW CUSTOMER OFFERS                                                                                                    #
#                                                                                                                                                                                           #
###################################################################################################################################################
@app.route('/newcustoffers',  methods=['POST','OPTIONS','GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def freshmeatprods():
    try:
        cid = request.json['cid']
        langid = request.json['langid']
    except:
        return make_response(jsonify({"Ratatoskr":"It seems like no cid was send "}),400)
    try:
        is_newcust= mssql_select('CIDB','DataMart',None,'OFFER','IndivID ='+str(cid))
    except:
        return make_response(jsonify({"Ratatoskr":"Some problems with SQL request.First of all, check sql connection"}),400)
    if is_newcust == []:
        try:
            conn = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB',charset="UTF-8")
            cursor = conn.cursor()
            select_max_offer = ("Select MAX(OfferID) FROM [DataMart].[OFFER]")
            cursor.execute(select_max_offer) 
            maxoffer = cursor.fetchone()[0]
            select_offer_temp = ("Select * from [DataMart].[OFFER_TEMPLATE] WHERE LanguageID="+str(langid))
            cursor.execute(select_offer_temp)   
            templates = cursor.fetchall()   
            i = maxoffer+1
            for row in templates:  
                print i    
                insert_queue = (
                "INSERT INTO [DataMart].[OFFER](OfferName,OfferStatus,OfferRate,OfferAmount,OfferPayment,OfferPrice,OfferBalance,OfferLimit,OfferPeriod,CashBackRate,OfferDetValidFrom,OfferDetValidTo,OfferValidFrom,OfferValidTo,OfferParam1,OfferParam2,OfferParam3,OfferParam4,OfferLoyaltyScore,OfferDesc,OfferImgID,OfferPrio,ProdID,IndivID,OfferID) VALUES ( '"+row[0]+"' ,'"+row[1]+"' ,'"+str(row[2])+"' ,'"+str(row[3])+"' ,'"+str(row[4])+"' ,'"+str(row[5])+"' ,'"+str(row[6])+"' ,'"+str(row[7])+"' ,'"+str(row[8])+"' ,'"+str(row[9])+"' ,'"+str(row[10])+"' ,'"+str(row[11])+"' ,'"+str(row[12])+"' ,'"+str(row[13])+"' ,'"+row[14]+"' ,'"+row[15]+"' ,'"+str(row[16])+"' ,'"+str(row[17])+"' ,'"+str(row[18])+"' ,'"+row[19].encode("utf-8","ignore")+"' ,'"+str(row[20])+"' ,'"+str(row[21])+"' ,'"+str(row[22])+"' ,'"+str(cid)+"','"+str(i)+"')")
                i+=1
                cursor.execute(insert_queue)
            conn.commit()
            return make_response(jsonify({"Ratatoskr":"Offers for newcommer were succesfully created"}),200)
        except Exception as e:
            return make_response(jsonify({"Ratatoskr":"Some problems with inserting offers for new customer occured"}),400)
    else:
        return make_response(jsonify({"Ratatoskr":"Offers for this client are already exist"}),201)

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /CONTACTS UPDATE                                                          #
#                                                                                                                                                                                           #
###################################################################################################################################################
@app.route('/contactupd',  methods=['POST','OPTIONS','GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def contactupd():
    try:
        cid = request.json['cid']
    except:
       return make_response(jsonify({"ContactUpdate":"Incorrect input"}),400)
    ms = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB',charset='UTF8')
    my = MySQLdb.connect(host=mysqlpath, port = 3306, user="rusrat",passwd="Orion123", db='thebankfront',use_unicode = True,charset='UTF8')
    cur = ms.cursor()
    try:
        cur.execute("UPDATE [DataMart].[INDIVIDUAL] SET Mobile = '79104117361', Email = 'sasdemo@sasbap.demo.com' WHERE IndivID <>" + str(cid))
        ms.commit()
    except:
        return make_response(jsonify({"ContactUpdate":"Some error occurred while updating MSSQL DB"}),418)
    cur = my.cursor()
    try:
        cur.execute("UPDATE `customers` set `MobileNumber`='79104117361',`Email`='sasdemo@sasbap.demo.com' where `CID` <>"+str(cid))
        my.commit()
    except Exception as e:
        return make_response(jsonify({"ContactUpdate":"Some error occured while updating MySQL DB"}),418)
    return make_response(jsonify({"ContactUpdate":"All customers have been updated"}),200)
#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /SYNC_UPDT                                                                                                                                            #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/sync_updt', methods=['POST'])
def sync_updt():
    try:
        app_server = request.json['app_server']
        web_server = request.json['web_server']
        soa_server = request.json['soa_server']
        sync = request.json['sync']
        freq_in = request.json['freq_in']
        freq_out = request.json['freq_out']
        freq_sync = request.json['freq_sync']
        bool_tmp = dur.set('Settings',json.dumps({"app_server" : app_server,"web_server" : web_server,"soa_server" : soa_server,"sync" : sync,"freq_in" : freq_in,"freq_out" : freq_out,"freq_sync" : freq_sync}))
        bool_tmp = dur.set('LastSync',json.dumps({"LastRequestTime":strftime("%d.%m.%Y %H:%M:%S",gmtime()),"app_server":app_server,"web_server":web_server,"soa_server":soa_server,"sync":sync,"freq_in":freq_in,"freq_out":freq_out,"freq_sync":freq_sync}))
        return make_response(jsonify({'Ratatoskr':'request processed'}),201)
    except Exception:
        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415)

@app.route('/sync_updt', methods=['GET'])
def sync_updt2():
    return make_response(jsonify(json.loads(dur.get('Settings'))),200)

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
            bool_tmp = dur.set('LastOffer',request.data)
            channel = 'mobile'
            resptype = 'direct'
            device = 'in future releases'
                   
            if (priority == 1): 
                #respname = "Accepted"
                respname = "Like"
                respid = 1
            elif (visibility == 0 and priority == 0):
                #respname = "Denied"
                respname = "Unlike"
                respid = 2
            else:
                respname = "undefined"
                respid = None
            #.isoformat(sep='T')
            inputs = {"cid":cid,"channel": channel,"context" : context,"device" : device,"offerid" : offerid,"resptype" : resptype,"respname" : respname,"respid" : respid,"resptime" : datetime.datetime.now().isoformat(sep='T'),"resptimestr" : str(accepted_dttm),"param1" : None,"param2" : None,"param3" : None,"param4" : None,"param5" : None,"param6" : None,"param7" : None}
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
            inputs = {"cid":cid,"channel": channel,"context" : context,"device" : device,"offerid" : offerid,"resptype" : resptype,"respname" : respname,"respid" : respid,"resptime" : resptime,"resptimestr" : resptime,"param1" : param1,"param2" : param2,"param3" : param3,"param4" : param4,"param5" : param5,"param6" : param6,"param7" : param7}
            
        except Exception:
            return make_response(jsonify({'Ratatoskr':'error processing site'}),418)  
    try:
        result = call_rtdm.apply_async((rtdmpath,"responsehistoryevent",inputs),retry=True)    
        return make_response(jsonify({'Ratatoskr':str(result)}),201)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':e}),418)  


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
        bool_tmp = dur.set('LastLaunch',json.dumps({"LastRequestTime":strftime("%d.%m.%Y %H:%M:%S",gmtime()),"clientid":clientid,"login":login,"password":password,"scenario":scenario}))
        print json.loads(dur.get('LastLaunch'))
        print json.loads(dur.get('LastOffer')) 
        return make_response(jsonify({'Ratatoskr':'request processed'}),201)
    except Exception:

        return make_response(jsonify({'Ratatoskr':'input data is corrupted'}),415)


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /TRANSACTION GENERATOR                                                                                                                                        #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################

bool_tmp = dur.set('transgenpar',json.dumps(0))
@app.route('/transgenerate', methods=['GET','POST','OPTIONS'])
@crossdomain(origin='*',content = 'application/json',headers = 'Content-Type')
def transgenerate():
    try:
        param = request.json['param']
        if param == 'True': 
            dur.set('transgenpar',json.dumps(1))
            taskid=transgen.delay()
            return make_response(jsonify({'Ratatoskr':'Transactions generator is actve'}),200)
        else:
            dur.set('transgenpar',json.dumps(0))
            return make_response(jsonify({'Ratatoskr':'Transactions generator is inactve'}),200)
    except Exception as e:
        return make_response(jsonify({'Ratatoskr':e}),415)


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /ACTIVE_QUEUE                                                                                                                                     #
#                                                                                                                                                                                           #
########################################################################################################################################################


#Redis variables initialization. Uncomment if Redis database being cleared

#bool_tmp = dur.set('Client_list',json.dumps([]))
#bool_tmp = dur.set('Terminal',json.dumps([]))

if dur.get('Client_list') == None:
    bool_tmp = dur.set('Client_list',json.dumps([]))

if dur.get('Terminal') == None:
    bool_tmp = dur.set('Terminal',json.dumps([]))

bool_tmp = dur.set('client_cnt',json.dumps(1))
bool_tmp = dur.set('updated',json.dumps(0))
bool_tmp = dur.set('upd',json.dumps(0))



@app.route('/active_queue', methods=['POST','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def active_queue():  
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
    if json.loads(dur.get('Client_list')) == []:
        Client_profile = {'client_num':str(json.loads(dur.get('client_cnt'))),'time':strftime("%d.%m.%Y %H:%M:%S",gmtime()),'id':client_id,'name':client_fname,'last_name':client_lname,'middle_name':client_mname,'dob':client_dob,'status':client_status,'reason':client_reason,'location':client_location,"area":client_area}
        dur_tmp = json.loads(dur.get('Client_list'))
        dur_tmp.append(Client_profile)
        bool_tmp = dur.set('Client_list',json.dumps(dur_tmp))
        dur_tmp = json.loads(dur.get('client_cnt'))
        dur_tmp +=1
        bool_tmp = dur.set('client_cnt',json.dumps(dur_tmp))

    else:
        bool_tmp = dur.set('updated',json.dumps(0))
        dur_tmp = json.loads(dur.get('Client_list'))
        for obj in dur_tmp:
            if obj['id'] == client_id:
                obj['location'] = client_location
                obj['reason'] = client_reason
                obj['area'] = client_area
                obj['time'] = strftime("%d.%m.%Y %H:%M:%S",gmtime())
                dur.set('Client_list',json.dumps(dur_tmp))
                bool_tmp = dur.set('updated',json.dumps(1))
        if json.loads(dur.get('updated')) == 0:
            Client_profile = {'client_num':str(json.loads(dur.get('client_cnt'))),'time':strftime("%d.%m.%Y %H:%M:%S",gmtime()),'id':client_id,'name':client_fname,'last_name':client_lname,'middle_name':client_mname,'dob':client_dob,'status':client_status,'reason':client_reason,'location':client_location,"area":client_area}
            dur_tmp = json.loads(dur.get('Client_list'))
            dur_tmp.append(Client_profile)
            bool_tmp = dur.set('Client_list',json.dumps(dur_tmp))
            dur_tmp = json.loads(dur.get('client_cnt'))
            dur_tmp +=1
            bool_tmp = dur.set('client_cnt',json.dumps(dur_tmp))    
    return make_response(jsonify({'Ratatoskr':'good','TEST': json.loads(dur.get('Client_list'))}),200)



@app.route('/active_queue', methods=['GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def CList():
    currdate = strftime("%d.%m.%Y %H:%M:%S",gmtime())
    Newcommers = []
    Full = []
    opt = request.args.get('option')
    if (opt is not None):
        if (opt == "new"):
            dur_tmp = json.loads(dur.get('Client_list'))
            for obj in dur_tmp:
                if datetime.datetime.strptime(currdate,'%d.%m.%Y %H:%M:%S') - datetime.datetime.strptime(obj['time'],'%d.%m.%Y %H:%M:%S') < datetime.timedelta(0,10) and (obj['location'] == 'terminal' or obj['location'] == 'camera' or obj['location'] == 'ATM' or obj['location'] == 'The Store' or obj['location'] == 'The Bank'):
                    Newcommer_profile = {'client_num':obj['client_num'],'time':obj['time'],'id':obj['id'],'name':obj['name'],'last_name':obj['last_name'],'middle_name':obj['middle_name'],'dob':obj['dob'],'status':obj['status'],'reason':obj['reason'],'location':obj['location'],'area':obj['area'],'photo':get_client(obj['id'])[25].replace(" ","+")}
                    Newcommers.append(Newcommer_profile)
            return make_response(jsonify({'Ratatoskr':Newcommers}),200)
        if (opt == "full"):
            dur_tmp = json.loads(dur.get('Client_list'))
            for obj in dur_tmp:
                Full_profile = {'client_num':obj['client_num'],'time':obj['time'],'id':obj['id'],'name':obj['name'],'last_name':obj['last_name'],'middle_name':obj['middle_name'],'dob':obj['dob'],'status':obj['status'],'reason':obj['reason'],'location':obj['location'],'area':obj['area'],'photo':get_client(obj['id'])[25].replace(" ","+")}
                Full.append(Full_profile)
                #Full.append(obj['id'])
            return make_response(jsonify({'Ratatoskr':Full}),200)
        if (opt == "terminal"):
            return make_response(jsonify({'Ratatoskr':json.loads(dur.get('Terminal'))}),200)
    else:
        if json.loads(dur.get('Client_list')) != []:
            return make_response(jsonify({'Ratatoskr':json.loads(dur.get('Client_list'))}),200)
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
            if json.loads(dur.get('Terminal')) == []:
                dur_tmp = json.loads(dur.get('Terminal'))
                Terminal_profile = {'client_id':client_id,'client_image':client_image}
                dur_tmp.append(Terminal_profile)
                bool_tmp = dur.set('Terminal',json.dumps(dur_tmp))
            else:
                bool_tmp = dur.set('upd',json.dumps(0))
                dur_tmp = json.loads(dur.get('Terminal'))
                for obj in dur_tmp:
                    if obj['client_id'] == client_id:
                        obj['client_image'] = client_image
                        dur.set('Terminal',json.dumps(dur_tmp))
                        bool_tmp = dur.set('upd',json.dumps(1))
                if json.loads(dur.get('upd')) == 0:
                    Terminal_profile = {'client_id':client_id,'client_image':client_image}
                    dur_tmp.append(Terminal_profile)
                    dur.set('Terminal',json.dumps(dur_tmp))
            return make_response(jsonify({'Ratatoskr':'Success'}),200)
    else:
        try:
            cid = request.json['id']
        except:
            return make_response(jsonify({'Ratatoskr':'No correct id'}),415)
        dur_tmp = json.loads(dur.get('Client_list'))
        for i in reversed(range(len(dur_tmp))):
            if dur_tmp[i].get('id') == cid:
                dur_tmp.pop(i)
        bool_tmp = dur.set('Client_list',json.dumps(dur_tmp))
        return make_response(jsonify({'Ratatoskr':json.loads(dur.get('Client_list'))}),200)
            
            

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /ATM                                                                                                                                                     #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
bool_tmp = dur.set('atm_status',json.dumps(True))
@app.route('/atm_status', methods=['GET'])
@crossdomain(origin='*')
def get_atm_status():
    global atm_status
    
    change = request.args.get('change')
    
    if (change is not None):
        if (change == "true"):
            bool_tmp = dur.set('atm_status',json.dumps(True))
        else:
            bool_tmp = dur.set('atm_status',json.dumps(False))
    return make_response(jsonify({'status':json.loads(dur.get('atm_status'))}),200)


@app.route('/atm_status', methods=['POST'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def set_atm_status():
    try:
        TID= request.json["TID"]
        Status = request.json["Status"]
    except:
        return make_response(jsonify({'Ratatoskr':'TID is incorrect'}),400)
    conn = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB')
    cursor = conn.cursor()
    sql=(
        
        "UPDATE [TRANSData].[TERMINAL] SET TermStatus='"+Status+"' WHERE TermID="+str(TID)+""
        "COMMIT")
    cursor.execute(sql)     
    return make_response(jsonify({'Ratatoskr':'Terminal status has been updated'}),200)


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
        return make_response(jsonify({'Ratatoskr':e}),400)







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
    
    try:
        dns = "10.20.1.190"
        event = "scoringevent"
        rtdm_addr = "http://"+dns+"/RTDM/rest/runtime/decisions/"+event
        payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
        result = call_rtdm.apply_async((dns,"scoringevent",inputs),retry=True)  
        return make_response(jsonify({'Ratatoskr':'ok'}),201)
    except:
        return make_response(jsonify({'Ratatoskr':'error'}),418)
        


    

#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /LimitControl                                                                                                                                            #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/limit', methods=['POST','OPTIONS'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def limit():
    try:
        Limit = request.json["Limit"]
        CID = request.json["CID"]
        TID = request.json["TID"]
        Type = request.json["Type"]
    except:
        return make_response(jsonify({"Ratatoskr":'input values are corrupt'}),400)
    conn = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB')
    cursor = conn.cursor()
    cursor.execute('SELECT AccountBalance FROM [DataMart].[ACCOUNT] WHERE IndivID ='+str(CID))
    data = cursor.fetchone()
    if data == None:
        return make_response(jsonify({"Ratatoskr":'There is no client with specified id in database'}),204)
    curlimit = int(data[0])
    cursor.execute('SELECT TermStatus FROM [TRANSData].[TERMINAL] WHERE TermID ='+str(TID))
    data = cursor.fetchone()
    termstatus = data[0]
    cursor.execute("SELECT MAX(AccountID),MIN(AccountID) FROM [DataMart].[ACCOUNT] WHERE IndivID ="+str(CID)+" AND AccountType='card'")
    data = cursor.fetchone()
    maxacc = data[0]
    minacc = data[1]
    cursor.execute('SELECT CardID FROM [DataMart].[Card] WHERE IndivID ='+str(CID))
    data = cursor.fetchall()
    cardid = [int(i[0]) for i in data]
    if termstatus == "nocash":
        trans={'TransID':randint(1,10000),'CardID':choice(cardid),'AccountID':randint(minacc,maxacc),'TermID':TID,
'TransStatus':'error','TransDate':strftime("%d.%m.%Y %H:%M:%S",gmtime()),'TransSum':Limit,'TransCurrency':'rub','TransType':Type,
'TransInfo':"atmerror",'TransParam1':'','TransParam2':'','TransParam3':'','TransParam4':''}
        que_result = rabbitmq_add('trans_mq','t_mq',json.dumps(trans,ensure_ascii=False),'application/json','trans_mq')
        payload = {"name":"","surname":"","middlename":"","dob":"","id":int(CID),"status":"processing","reason":"Withdrawal","location":"ATM","area":"bank"}
        try:
            resultATM = call_service.apply_async(("active_queue",payload),retry=True) 
        except:
             return make_response(jsonify({"Ratatoskr":'Some problems with client queue update. Check if payload is correct'}),400)
        return make_response(jsonify({"Ratatoskr":'ATM has no money'}),202)
    elif termstatus == "work":
        if curlimit-Limit >= 0:
            trans={'TransID':randint(1,10000),'CardID':choice(cardid),'AccountID':randint(minacc,maxacc),'TermID':TID,
'TransStatus':'ok','TransDate':strftime("%d.%m.%Y %H:%M:%S",gmtime()),'TransSum':Limit,'TransCurrency':'rub','TransType':Type,
'TransInfo':"",'TransParam1':'','TransParam2':'','TransParam3':'','TransParam4':''}
            que_result = rabbitmq_add('trans_mq','t_mq',json.dumps(trans,ensure_ascii=False),'application/json','trans_mq')
            print trans
            return make_response(jsonify({"Ratatoskr":'Transaction has been generated'}),200)
        else:
            trans={'TransID':randint(1,10000),'CardID':choice(cardid),'AccountID':randint(minacc,maxacc),'TermID':TID,
'TransStatus':'refusal','TransDate':strftime("%d.%m.%Y %H:%M:%S",gmtime()),'TransSum':Limit,'TransCurrency':'rub','TransType':Type,
'TransInfo':"proddetlimit",'TransParam1':'','TransParam2':'','TransParam3':'','TransParam4':''}
            que_result = rabbitmq_add('trans_mq','t_mq',json.dumps(trans,ensure_ascii=False),'application/json','trans_mq')
            return make_response(jsonify({"Ratatoskr":'Limit is exceeded'}),201)
    else:
        return make_response(jsonify({"Ratatoskr":'ATM is out of servce'}),203)


@app.route('/limit', methods=['GET'])
@crossdomain(origin='*', content = 'application/json',headers = 'Content-Type')
def getlimit():
    try:
        cid = request.args.get('cid')
    except:
        return make_response(jsonify({"Ratatoskr":'Icorrect unput'}),400)
    conn = pymssql.connect(server = mssqlpath,user = 'rtdm',password = 'Orion123',database='CIDB')
    cursor = conn.cursor()
    cursor.execute('SELECT AccountBalance FROM [DataMart].[ACCOUNT] WHERE IndivID ='+str(cid))
    data = cursor.fetchone()
    if data != None:
        curlimit = int(data[0])   
    else:
        return make_response(jsonify({"Ratatoskr":'There is no account with specified client id in database'}),201) 
    return make_response(jsonify({"Ratatoskr":curlimit}),200) 
    


#############################################################################################################################################################################################
#                                                                                                                                                                                           #
#                         BLOCK OF /LUNA                                                                                                                                                    #
#                                                                                                                                                                                           #
#############################################################################################################################################################################################
@app.route('/luna', methods=['GET'])
@crossdomain(origin='*')
def result_luna():
    if dur.get('lunaresp') == None:
        dur.set('lunaresp','never used')
    if dur.get('lunaans') == None:
        dur.set('lunaans','never used')
    if dur.get('req_image') == None:
        dur.set('req_image','')
    if dur.get('rid') == None:
        dur.set('rid',0)
    return make_response(jsonify({'Ratatoskr':dur.get('lunaresp'),'Luna':dur.get('lunaans'), 'image':dur.get('req_image'), 'rid':json.loads(dur.get('rid'))}))
    
@app.route('/luna', methods=['OPTIONS'])
@crossdomain(origin='*',headers = 'Content-Type')
def send_options():
    return make_response(jsonify({'Ratatoskr':'PUT, GET'}))

@app.route('/luna', methods=['PUT'])
@crossdomain(origin='*',headers = 'Content-Type', content = 'application/json')
def call_luna():
    image = ''
    try:
        image = request.json["data"]
    except Exception:
        return make_response(jsonify({'Ratatoskr':'Missing attribute data (image)'}),422)
    if (image == ""):
        return make_response(jsonify({'Ratatoskr':'Empty attribute data (image)'}),422)
    bool_tmp = dur.set('req_image',image)
    #rid - applicant image , cid - client ID , bare - write to DB (True - no, False - yes)    
    try:
        rid = request.json["rid"]
        bool_tmp = dur.set('rid',json.dumps(rid))
    except Exception:
        bool_tmp = dur.set('rid',json.dumps(500000))
    if json.loads(dur.get('rid'))<500000:
        dur_tmp = json.loads(dur.get('rid'))
        dur_tmp += 500000
        bool_tmp = dur.set('rid',json.dumps(dur_tmp))
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

    url = "http://"+lunapath+":8083/5/templates"
    
    payload = {"image":image, "bare":bare}
    try:
        r = requests.post(url,json = payload)
        bool_tmp = dur.set('lunaans',r.json())
        status = str(r)
    except Exception:
        bool_tmp = dur.set('lunaresp','Luna service is unreachable or unavailable')
        bool_tmp = dur.set('lunaans','Luna service is unreachable or unavailable')
        return make_response(jsonify({'Ratatoskr':dur.get('lunaresp')}),  415)  

     
    if ((("200") in status)  and (match_flg == False)):
        bool_tmp = dur.set('lunaresp','Luna has processed the image')
        return make_response(jsonify({'Ratatoskr': dur.get('lunaresp'),'Luna':str(r.json()),'score':r.json()["score"]}),  200)

    elif ((("201") in status)  and (match_flg == False)):  
        bool_tmp = dur.set('lunaresp','Luna has processed and saved the image')
        bool_tmp = dur.set('rid',r.json()["id"])
        return make_response(jsonify({'Ratatoskr': dur.get('lunaresp'),'Luna':str(r.json()),'score':r.json()["score"],'rid':json.loads(dur.get('rid'))}),  201)

    elif ((("201") in status)  and (match_flg == True)): 
        if cid != '':
            try:
                candidates = str(get_client(cid)[26])
            except Exception:
               bool_tmp = dur.set('lunaresp','Client not found')
               return make_response(jsonify({'Ratatoskr': dur.get('lunaresp')}), 500)
        else:
            candidates = str(get_all_clients())[1:-1]
         

        bool_tmp = dur.set('rid',r.json()["id"])
        url_get = "http://"+lunapath+":8083/5/similar_templates?id="+str(json.loads(dur.get('rid')))+"&candidates="+candidates
        g = requests.get(url_get)
        
        try:
           v = []
           for item in g.json().iteritems():
               v.append(item) 
           score = v[0][1][0]["similarity"]
           photoid = v[0][1][0]["id"]
           clientid = get_cid_byphotoid(photoid)
           clientinfo = get_client(clientid)
        except Exception:
            bool_tmp = dur.set('lunaresp','Client photo not found in Luna. Check cid or photoid')
            return make_response(jsonify({'Ratatoskr': dur.get('lunaresp'),'url':url_get,'rid':json.loads(dur.get('rid')),'photoid':photoid}), 500) 

        bool_tmp = dur.set('lunaresp','Luna has saved and matched the image')
        name = clientinfo[1]
        surname = clientinfo[3]
        middlename = clientinfo[2]
        gender = clientinfo[6]
        mobile = clientinfo[5]
        dob = str(clientinfo[9])
        

        return make_response(jsonify({'Ratatoskr':dur.get('lunaresp'),'score':score, 'client':clientid, 
'name':name,'surname':surname, 'middlename':middlename, 'gender':gender, 'mobile':mobile, 'dob':dob,'Luna':g.text, 'url':url_get,'rid':json.loads(dur.get('rid'))}), 201) 

    elif ((("200") in status)  and (match_flg == True)): 
        bool_tmp = dur.set('lunaresp','That will not work. Maybe \'bare\' should be \'false\' or there is an ambiguous \'match\' option?')
        return make_response(jsonify({'Ratatoskr': dur.get('lunaresp')}), 422) 

    elif ("500" in status):
        bool_tmp = dur.set('lunaresp','Luna failed on upload')
        return make_response(jsonify({'Ratatoskr': dur.get('lunaresp')}), 451)       
    else:
        bool_tmp = dur.set('lunaresp','Ooops... something unexpected happened')
        return make_response(jsonify({'Ratatoskr': dur.get('lunaresp')+' Response code is '+status}), 418) 


#Error handler
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'Ratatoskr': 'Service not found'}), 404)

if __name__ == '__main__':
    app.run(host=server_ip,debug=True,threaded = True )
#threaded = True processes = 4




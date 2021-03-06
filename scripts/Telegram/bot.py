#!/var/beacon/clr/bin/python 
# coding: utf-8
import config
import telebot
import random
import re
import requests

from ctasks import rabbitmq_add,mysql_select,call_rtdm,mssql_select,call_service
from celery import Celery
from flask import Flask, jsonify, abort,make_response,request,json 

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

global blacklist 
blacklist =  {'durak','urod','skotina','suka','gad','urod','chmo','petux','gandon','gnida','pidar','pizduk','svoloch'}


bot = telebot.TeleBot(config.token)






code = 0000
rtdmpath = '10.20.1.190'


@bot.message_handler(commands=["start"])
def start_chat(message):
    global code
    reply_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard = True,one_time_keyboard = True)
    reply_markup.row('English')
    reply_markup.row('Русский')
    bot.send_message(message.chat.id,'Здравствуйте! Пожалуйста, выберите язык.')
    bot.send_message(message.chat.id,'Hello! Please, choose your language.',reply_markup = reply_markup)
    code = random.randint(1000,10000)



@bot.message_handler(content_types=["text"])
def send_messages(message):
    global tel
    global lang
    if message.text == 'English':
        lang = 'eng'
        bot.send_message(message.chat.id,'Please, enter mobile phone number. Mask: 79261112233')
    elif message.text == 'Русский':
        lang = 'rus'
        bot.send_message(message.chat.id,'Введите номер телефона. Пример: 79261112233')
        #bot.send_message(message.chat.id,code)
    elif message.text.isdigit():
        if re.match('7\d{10}$',message.text):
            tel = message.text
            if lang == 'eng':
                inputs = {"IndivID":0,"Channel":"","phones":tel,"mes":"Telegram secure code:"+str(code)+". Don't tell this code anyone","sender":"SAS Russia","param1":"",
"param2":"","param3":0,"param4":0}
            elif lang == 'rus':
                inputs = {"IndivID":0,"Channel":"","phones":tel,"mes":"Код безопасности:"+str(code)+". Не сообщайте данный код никому","sender":"SAS Russia","param1":"","param2":"","param3":0,"param4":0} 
            event = "smsevent"
            rtdm_addr = "http://"+rtdmpath+"/RTDM/rest/runtime/decisions/"+event
            payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
            r = requests.post(rtdm_addr,json = payload)
            if lang == 'eng':
                bot.send_message(message.chat.id,'Thank you. Enter a code you\'ll receive in SMS soon ')
            elif lang == 'rus':
                bot.send_message(message.chat.id,'Спасибо! Введите код, пришедший в СМС')
        elif re.match('\d{4}$',message.text):
            if str(message.text) == str(code):
                inputs = {"Mobile":tel,"Chat_id":int(message.chat.id),"Sender":"SAS Russia"}
                event = "telegram"
                rtdm_addr = "http://"+rtdmpath+"/RTDM/rest/runtime/decisions/"+event
                payload = {"clientTimeZone":"Europe/Moscow","version":1,"inputs":inputs}
                r = requests.post(rtdm_addr,json = payload)
                if lang == 'eng':
                    bot.send_message(message.chat.id,'Correct!')
                elif lang == 'rus':
                    bot.send_message(message.chat.id,'Верно!')
            else:
                if lang == 'eng':
                    bot.send_message(message.chat.id,'Incorrect')
                elif lang == 'rus':
                    bot.send_message(message.chat.id,'Неверно, повторите попытку.')
                bot.send_message(message.chat.id,code)
        else:
            if lang == 'eng':
                bot.send_message(message.chat.id,'What does number you enter mean?')
            elif lang == 'rus':
                bot.send_message(message.chat.id,'Что означает введенное Вами число?')
    elif any(word in message.text.lower() for word in blacklist):
        if lang == 'eng':
            bot.send_message(message.chat.id,'Easy,dude. You should be more polite' )
        elif lang == 'rus':
            bot.send_message(message.chat.id,'Полегче, дружище! Тебе не помешало бы быть более вежливым.')
    else:
        if lang == 'eng':
            bot.send_message(message.chat.id,'Sorry,I don\'t understand you')
        elif lang == 'rus':
            bot.send_message(message.chat.id,'Прошу прощения, я Вас не понимаю')
    

if __name__ == '__main__':
    bot.polling(none_stop = True)

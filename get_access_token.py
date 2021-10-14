from kiteconnect import KiteConnect
import datetime
from global_variables import api_key,api_secret,mongo_connection_string
import json
from datetime import datetime,date
from time import sleep
import os
from pymongo import MongoClient
import pandas as pd
from bot import send_telegram_message


def whats_in_file():
    f = open('access_token.json',)
    data = json.load(f)
    f.close()
    return data

def whats_in_db():
    client = MongoClient(mongo_connection_string)
    # get the database object
    db = client.AccessTokenManager
    collection = db['AccessTokens']
    data  = pd.DataFrame(list(collection.find().sort('login_time', -1  )))
    client.close()
    if len(data):
        return data.iloc[0].to_dict()
    return False

def get_access_token():
    # counter used to keep trak when to send telegram message
    counter = 1
    counter2 = 1
    while True:
        # data = whats_in_file()
        data = whats_in_db()
        if data:
            # managing access_token using json file later 'll be replaced by some DB
            # login_time = datetime.strptime(data['login_time'], '%Y-%m-%d %H:%M:%S')
            login_time = data['login_time']
            # check if last loggin is b4 8:35 am the access token is flushed btn 7:30-8:30 
            if login_time < datetime.now().replace(hour=8, minute=35):
                # create kite obj used to get login url
                kite = KiteConnect(api_key=api_key)
                # message every 90 second of loop
                if (counter % 90 == 0) or counter == 1:
                    print('Session expired need to login again link sent to telegram')
                    send_telegram_message(messages=["Generate access Token : \n  "+ kite.login_url()])
                sleep(1)
                counter +=1
            else:
                # if logged in today return the access token
                print(data['access_token'])
                return data['access_token']
        else:
            if (counter2 % 30 == 0) or counter2 == 1:
                print('access token not found')
                send_telegram_message(messages=["access token not found"])
            sleep(1)
            counter2 +=1






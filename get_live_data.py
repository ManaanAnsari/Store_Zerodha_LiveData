#!python
from pprint import pprint
from kiteconnect import KiteTicker
from instrument_dict import instruments_dict
from datetime import datetime,date
from datetime import time as time_func
import pytz
from pymongo import MongoClient
from global_variables import api_key,api_secret,mongo_connection_string
import pandas as pd
import time
from time import sleep
import os
from get_access_token import get_access_token
from apscheduler.scheduler import Scheduler
import requests 
from bot import send_telegram_message

'''
IMP Note:
 this file auto sleeps after market is closed 
 that means 'll have to login every morning without notification
 once logged in and market is open all crons 'll work and live data 'll be saved
'''

sched = Scheduler()
sched.start()

# The global variable of this file that 'll be set and reset everyday
kws = None
access_token = None
client = None
db = None
         

# when ticks(live data) are recived via websocket
def on_ticks(ws, ticks):
    ''' ticks is inthe form of list of dicts each dict represent a single company '''
    # disconnect if market is closed (no need to use now dissconnecting it with the help of cron)
    if not check_if_market_open():
        # ws.close()
        disconnect_ticker()
    else:
        # make_1min_candel(ticks)
        # if market open then save data
        for single_comapny in ticks:
            to_save = {}
            to_save['last_price'] = single_comapny['last_price']
            if 'volume' in single_comapny.keys():
                to_save['volume'] = single_comapny['volume']
            else:
                to_save['volume'] = 0
            to_save['timestamp'] = single_comapny['timestamp']
            # to_save['timestamp'] = datetime.now()
            company_name = instruments_dict[single_comapny['instrument_token']]
            collection = db[company_name]
            collection.insert_one(to_save)
            print(company_name+' saved')


# this finction is triggered when websocket is connected
def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe(list(instruments_dict.keys()))
    # quote mode gives data of ohlc too (full mode is also available)
    # MODE_LTP ,MODE_QUOTE ,MODE_FULL
    ws.set_mode(ws.MODE_FULL, list(instruments_dict.keys()))

def on_error(ws, code, reason):
    print('here',code,reason)
    if reason != 'connection was closed uncleanly (None)':
        send_telegram_message(messages=[reason])
    # if not kws.is_connected():
    #     if check_if_market_open():
    #         print('reconnectinf')
    #         connect_ticker()


# -------------------------------------- main function that handels above functionality

# main function that handels connections and all callbacks
def connect_ticker():
    print('connecting ... ticker..')
    global kws,access_token,client,db
    if client is None:
        # connect to database (using atlas)
        client = MongoClient(mongo_connection_string)
        db = client.Zerodha_LiveData
        # clear the DB
        fresh_start()
    # if access_token is not yet set
    if access_token is None:
        print('getting access token')
        access_token_reminder()
        # access_token = get_access_token()
    if kws is None:
        # craete main websocket object 
        kws = KiteTicker(api_key, access_token)
        # Assign the callbacks.
        kws.on_ticks = on_ticks
        kws.on_connect = on_connect
        kws.on_error = on_error
        # kws.on_close = on_close
    kws.connect()


def disconnect_ticker():
    # On connection close stop the main loop
    global kws,access_token,client,db
    if kws is not None:
        print('DISCONNECTING ...ticker..')
        # reset all variables for next day 
        client.close()
        client=None
        db = None
        kws.close()
        kws.stop()
        access_token = None
        kws = None


# different function for access token that 'll remind me in every 30 seconds after 8:40 to login
def access_token_reminder():
    # this function mainly sets accedd_token
    global access_token
    if access_token is None:
        access_token = get_access_token()


def fresh_start():
    '''
        this function is written to save space and delete live data 
        it goes through all the company name and deletes its collection
        todo: to avoid unnecessary delete make a check if todays data present then dont delete(i.e only delete when starting a new day) 
    '''
    for key,value in instruments_dict.items():
        # get collection to drop
        collection = db[value]
        # get latest data present in collection 
        temp_df = pd.DataFrame(list(collection.find().sort('timestamp', -1  )))
        if len(temp_df):
            latest_data = temp_df[:1]
        else:
            continue
        # check if data stored is older(not today's)
        if len(latest_data) and (latest_data['timestamp'][0].date() < date.today()):
            # delete the collection
            collection.drop()


# to check if market is still open this allows us to connect without cron
def check_if_market_open():
    d = datetime.now()
    if (d.isoweekday() in range(1, 6)) and ((d.time() >= time_func(9,10)) and (d.time() < time_func(15,31))):
        # if market open
        return True
    else:
        # if market close
        return False

# web node(root) automatically sleeps after 30 mins of inactivity
# this fuction is used with a 25 mins cron that wont let node sleep while fetching live data
# as it checks if market is open it 'll allow to sleep after 3:30  
def wakeup_node():
    if check_if_market_open():
        # make get request to root url
        URL = "https://birdwatcherbot.herokuapp.com/"
        r = requests.get(url = URL)
        print('wakeup node call')
    else:
        print(' market closed no wakeup call needed')

# schedule run of accesstoken reminder 
print('scheduling access_token_reminder')
sched.add_cron_job(access_token_reminder, day_of_week='mon-fri', hour=8,minute=45)
# scheduled node wakeup calls
print('scheduling wakeup_node')
sched.add_interval_job(wakeup_node, minutes=25)

'''
note : Connection and disconnection is not managed by cron for now 
     its managed by check_if_market_open function
'''

# connect_ticker()
# keep on running 
while sched.running:
    if check_if_market_open():
        if kws is None:
            print('market open but not connected 1st time')
            connect_ticker()
        if not kws.is_connected():
            print('market open but not connected')
            connect_ticker()
        print('sleepin 1sec')
        sleep(1)


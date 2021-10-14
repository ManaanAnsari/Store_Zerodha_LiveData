from flask import Flask, request
from kiteconnect import KiteConnect
import datetime
from global_variables import api_key,api_secret,mongo_connection_string
import json
from datetime import datetime
from pymongo import MongoClient

# App
app = Flask(__name__)

# Templates
index_template = """
    <h1>login from telegram</h1>"""

login_successful_template = """
    <h2 style="color: green">Success Updated</h2>"""

login_unsuccessful_template = """
    <h2 style="color: red">Unsucessfull attempt</h2>"""

login_expired_template = """
    <h2 style="color: red">Expired request token check logs</h2>"""

def save_accesstoken(access_token):
    client = MongoClient(mongo_connection_string)
    # get the database object
    db = client.AccessTokenManager
    collection = db['AccessTokens']
    collection.insert_one({
        'access_token':access_token,
        'login_time':datetime.now()
    })
    client.close()
    return True


@app.route("/")
def index():
    return index_template

@app.route("/login")
def login():
    # get request token from url
    request_token = request.args.get("request_token")
    # if request token exist
    if request_token:
        # create main kite object
        kite = KiteConnect(api_key=api_key)
        # to get access_token generate session
        try:
            # if error occured it 'll probably be a invalid request token error
            data = kite.generate_session(request_token, api_secret=api_secret)
        except Exception as e:
            # show the error
            return login_expired_template
        if save_accesstoken(data['access_token']):
            return login_successful_template
        else:
            return login_unsuccessful_template    
    else:
        return login_unsuccessful_template

if __name__ == '__main__':
    app.run(threaded=True, port=5000)

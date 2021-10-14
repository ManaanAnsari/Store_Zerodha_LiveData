###Highlights
fetch live data using websocket from zerodha's kite connect API
and store it in mongodb 

### How to use?

signup for [kiteconnect](https://kite.trade/docs/connect/v3/)

`pip install requirements.txt`

***set your conf vars in*** `global_variables.py`

`python app.py` to run flask app (used to generate access token)

`python get_live_data.py` to connect to websocket 


### Deployment
deploy it on heroku using given Prockfile

#### Note
for this to work change login redirect url in your kite app to your flask URL 
as login redirect url needs to be https if you are using this on your localhost use service like ngrok to tunnel 


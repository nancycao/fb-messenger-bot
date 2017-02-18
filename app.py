import os
import sys
import json

import requests
from flask import Flask, request
#from utils import db

START = False
AGE = False
STATE = False

app = Flask(__name__)

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

# process received messages
@app.route('/', methods=['POST'])
def webhook():
    # endpoint for processing incoming messaging events
    global START
    global AGE
    global STATE

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                log("MSG_EVENT:")
                log(messaging_event)

                if messaging_event.get("message"):  # someone sent us a message
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    message_text = messaging_event["message"]["text"]  # the message's text
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    if not START:
                        send_start(sender_id) # VOLUNTEER OR CLIENT?
                        START = True
                        log("START")
                    elif not AGE:
                        # save mesage_text as AGE
                        AGE = True
                        log("AGE")
                        send_message(sender_id, "(OPTIONAL - for your legal advisor to better understand your case)")
                        send_message(sender_id, "Enter in the initials of your state (eg: NY or PA) OR enter SKIP")

                    elif not STATE:
                        STATE = True
                        log("STATE")
                        send_message(sender_id, "We will connect you to your volunteer legal advisor shortly.")

                    '''

                    if( db.findMatchingId( sender_id ) != None ):
                        new_recipient_id = findMatchingId( sender_id )
                        send_message( new_recipient_id, message_text )
                    else:
                        send_message( sender_id, "Are you a lawyer or client?")

                    '''
                    # respond

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    sender_id = messaging_event["sender"]["id"]

                    action = messaging_event["postback"]["payload"]
                    log("ACTION: " + action)

                    if action == "VOLUNTEER":
                        send_message(sender_id, "You are a volunteer")
                    elif action == "CLIENT":
                        send_categories(sender_id)
                    elif action == "IMMIGRATION_LAW" or action == "CITIZENSHIP" or action == "VISA":
                        if action == "IMMIGRATION_LAW":
                            pass
                            # save immigration law as category
                        elif action == "CITIZENSHIP":
                            pass
                        elif action == "VISA":
                            pass
                        send_message(sender_id, "(OPTIONAL - for your legal advisor to better understand your case)")
                        send_message(sender_id, "Enter in your age OR enter SKIP")


    return "ok", 200

# BOTH: VOLUNTEER OR CLIENT?
def send_start(recipient_id):
    #log("sending message to {recipient}: {text}".format(recipient=recipient_id), text="Hello, I'm Trevor. Would you like to volunteer your legal services or ask a legal question?")
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
         "message":{
            "attachment":{
              "type":"template",
              "payload":{
                "template_type":"button",
                "text":"Hello, I'm Trevor. Would you like to volunteer your legal services or ask a legal question?",
                "buttons":[
                  {
                    "type":"postback",
                    "title":"Volunteer",
                    "payload":"VOLUNTEER"
                  },
                  {
                    "type":"postback",
                    "title":"Ask Question",
                    "payload":"CLIENT"
                  }
                ]
              }
            }
        }
    })
    log(data)
    print data
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

# CLIENT: 4 CATEGORIES
def send_categories(recipient_id):
    #log("sending message to {recipient}: {text}".format(recipient=recipient_id), text="Hello, I'm Trevor. Would you like to volunteer your legal services or ask a legal question?")
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
         "message":{
            "attachment":{
              "type":"template",
              "payload":{
                "template_type":"button",
                "text":"Choose a category that best suits your question:",
                "buttons":[
                  {
                    "type":"postback",
                    "title":"Immigration Law",
                    "payload":"IMMIGRATION_LAW"
                  },
                  {
                    "type":"postback",
                    "title":"Citizenship",
                    "payload":"CITIZENSHIP"
                  },
                  {
                    "type":"postback",
                    "title":"VISA",
                    "payload":"VISA"
                  }
                ]
              }
            }
        }
    })
    log(data)
    print data
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

# GENERAL: message
def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()

if __name__ == '__main__':
    app.run(debug=True)

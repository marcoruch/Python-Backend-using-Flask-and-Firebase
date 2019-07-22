import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, session, request, redirect, render_template, url_for
import pyrebase
import requests
import json
import os
from lib import FirebaseConfig 
from lib import FirebaseAuth
import pprint

config = FirebaseConfig.getConfig()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Use the application default credentials
firebase = pyrebase.initialize_app(config)
firebase_admin.initialize_app(credentials.Certificate("./serviceAccountKey.json"))

auth = firebase.auth()
db = firestore.client()

###############################################################################################

# START ROUTE '/login' METHOD=[POST] #
@app.route('/login', methods=["POST"])
def login():
    message = ""
    try:
        # Try returning user-token from current session
        return json.dumps(session["usr"])
    except KeyError:
        # If there is no user-token in current session validate login
        email = request.form["login_email"]
        password = request.form["login_password"]
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            user = auth.refresh(user['refreshToken'])
            session['user_token'] = user_id = user['idToken']
            session['usr'] = user_id
            pprint.pprint("User logged in...:  "+ user['userId'])
            return json.dumps(user)
        except:
            message = "Incorrect Credentials!"
            return json.dumps(message)
            
# END ROUTE #            

###############################################################################################

# START ROUTES '/alerts' METHOD=[GET, POST] #
@app.route('/alerts', methods=["GET", "POST"])
def alerts():
    # START STANDARD AUTHORIZATION FOR ROUTES #
    authorizationResult = FirebaseAuth.authorizeUser(request,session);
    if authorizationResult.authorized == False:
        message = "Unauthorized.. no token."
        return json.dumps(message)
    # END STANDARD AUTHORIZATION FOR ROUTES #

    # POST REQUEST
    if request.method == 'POST':
        try:
            alertPrice = request.form["alertPrice"]
            currentPrice = request.form["currentPrice"]
            itemName = request.form["itemName"]
            itemUrl = request.form["itemUrl"]
            userHandle = authorizationResult.user_id
            document_id = userHandle+"_"+itemName
            db.collection(u'alerts').document(document_id).set({
                "alertPrice": alertPrice,
                "currentPrice": currentPrice,
                "itemName": itemName,
                "itemUrl": itemUrl,
                "userHandle": userHandle,
            })
            # CHECK IF EXISTS AND RETURN IT
            doc = db.collection(u'alerts').document(document_id).get()
            docData = { "documentId": (document_id), "documentData": doc.to_dict()}
            pprint.pprint(docData)
            return json.dumps(docData)
        except Exception as e: 
            pprint.pprint(e)
            message = "Something went wrong..."
            return json.dumps(message)

    # GET REQUEST            
    elif request.method == 'GET':
        try:
            docs = db.collection(u'alerts').where('userHandle', u'==', authorizationResult.user_id).stream()

            users_alerts_resolved = []
            for doc in docs:
                users_alerts_resolved.append({"documentId" : doc.id, "documentData": doc.to_dict()})
            pprint.pprint("User reading /alerts")
            pprint.pprint(users_alerts_resolved)
            return json.dumps(users_alerts_resolved)
        except Exception as e: 
            pprint.pprint(e)
            message = "Something went wrong..."
            return json.dumps(message)

# END ROUTE #

###############################################################################################

# RUN APP #
if __name__ == '__main__':
    app.run()
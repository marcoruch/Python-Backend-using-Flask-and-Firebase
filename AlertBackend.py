import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth as firebaseAuth
from firebase_admin import firestore
from flask import Flask, session, request, redirect, render_template, url_for
import pyrebase
import requests
import json
import os
from lib import FirebaseConfig 
import pprint

config = FirebaseConfig.getConfig()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Use the application default credentials
default_app = firebase_admin.initialize_app(credentials.Certificate("./serviceAccountKey.json"))
db = firestore.client()


# pyrebase
firebase = pyrebase.initialize_app(config)
pyrebaseAuth = firebase.auth()

###########################


# FB User Result
class FBAuthorizationResult:
    """A simple Authorization class"""
    def __init__(self, user_token, user_id, authorized):
        self.user_tokenr = user_token
        self.user_id = user_id
        self.authorized = authorized
        
# Standard check
# HEADER: User-Token ===  FirebaseAuthorization Token  (ID Token) 
# HEADER: User-Id === 28 Digits Long UserHandle | User-Id  (User-Identifier on Database)
def authorizeUser(request):
    user_token = request.headers['User-Token']
    user_id = request.headers['User-Id']
    try:
        # throws if invalid
        firebaseAuth.verify_id_token(user_token)
        pprint.pprint("User was authorized.... " + user_id)
        return FBAuthorizationResult(user_token, user_id, True)
    except Exception as e: 
        pprint.pprint(e)
        pprint.pprint("User could not be authorized.... " + user_id)
        return FBAuthorizationResult(user_token, user_id, False)

###############################################################################################

# START ROUTE '/login' METHOD=[POST] #
@app.route('/login', methods=["POST"])
def login():
    message = ""
    email = request.form["login_email"]
    password = request.form["login_password"]
    try:
        user = pyrebaseAuth.sign_in_with_email_and_password(email, password)
        user = pyrebaseAuth.refresh(user['refreshToken'])
        pprint.pprint("User logged in...:  "+ user['userId'])
        return json.dumps(user), 200
    except:
        message = "Incorrect Credentials!"
        return json.dumps(message), 404
            
# END ROUTE #         

###############################################################################################

# START ROUTE '/login' METHOD=[POST] #
@app.route('/register', methods=["POST"])
def register():
    message = ""
    email = request.form["register_email"]
    password = request.form["register_password"]
    try:
        user = pyrebaseAuth.create_user_with_email_and_password(email, password)
        user = pyrebaseAuth.refresh(user['refreshToken'])
        pprint.pprint("User logged in...:  "+ user['userId'])
        return json.dumps(user), 200
    except Exception as e: 
        pprint.pprint(e)
        message = "Could not register!"
        return json.dumps(message), 404
            
# END ROUTE #         

###############################################################################################

# START ROUTES '/alerts' METHOD=[GET, POST] #
@app.route('/alerts', methods=["GET", "POST"])
def alerts():
    # START STANDARD AUTHORIZATION FOR ROUTES #
    authorizationResult = authorizeUser(request);
    if authorizationResult.authorized == False:
        message = "Unauthorized.. no token."
        return json.dumps(message), 404
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
            return json.dumps(docData), 200
        except Exception as e: 
            pprint.pprint(e)
            message = "Something went wrong..."
            return json.dumps(message), 404

    # GET REQUEST            
    elif request.method == 'GET':
        try:
            docs = db.collection(u'alerts').where('userHandle', u'==', authorizationResult.user_id).stream()

            users_alerts_resolved = []
            for doc in docs:
                users_alerts_resolved.append({"documentId" : doc.id, "documentData": doc.to_dict()})
            pprint.pprint("User reading /alerts")
            pprint.pprint(users_alerts_resolved)
            return json.dumps(users_alerts_resolved), 200
        except Exception as e: 
            pprint.pprint(e)
            message = "Something went wrong..."
            return json.dumps(message), 404

# END ROUTE #

###############################################################################################

# RUN APP #
if __name__ == '__main__':
    app.run()
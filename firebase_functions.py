import firebase_admin
from firebase_admin import auth
from firebase_admin import credentials
from firebase_admin import messaging

import hashlib
import json
import os

from dotenv import load_dotenv
load_dotenv()


if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

def do_auth(token):
    decoded_token = auth.verify_id_token(token, clock_skew_seconds=20)
    email = decoded_token['email']

    print("Authenticated user: " + email)

    return decoded_token


def send_message(tokens, data=None, notification=None):
    message = messaging.MulticastMessage(
        data=data,
        notification=notification,
        tokens=tokens,
    )

    response = messaging.send_multicast(message)
    print('Successfully sent message:', response)

def generate_local_api_key(id_token, user_email):
    salt = os.getenv('APP_SECRET')
    combined_string = id_token + user_email + salt
    hashed_string = hashlib.sha256(combined_string.encode()).hexdigest()
    return hashed_string

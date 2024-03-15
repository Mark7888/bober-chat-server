from flask import Flask, render_template, request, Response

from firebase_functions import do_auth, send_message, generate_local_api_key
from message_sender import database_manager, message_storage, get_message_error, send_text_message
from database_manager import UserManager

import json

app = Flask(__name__)

# Initialize storage manager objects
user_storage = UserManager(database_manager)


# This is the server health check endpoint
@app.route('/health')
def index():
    return "ok"

# This is the endpoint that the client will use to authenticate with the server
@app.route('/authenticate', methods=['POST'])
def authenticate():
    messaging_token = request.json['messagingToken']
    auth_token = request.json['authToken']

    # Authenticate the user
    user_data = do_auth(auth_token)

    # Generate a local API key
    local_api_key = generate_local_api_key(auth_token, user_data['email'])

    # Save the user to the storage
    user_storage.add_user(user_data, messaging_token, local_api_key)

    # send the local api key to the client
    send_message(messaging_token, data={"auth_ack": "true", "api_key": local_api_key})

    return Response(status=200)


# This is the endpoint that the client will use to send a message to another user
@app.route('/send_message', methods=['POST'])
def send_message_to_user():
    api_key = request.json['apiKey']
    recipient_email = request.json['recipientEmail']
    messageType = request.json['messageType']
    messageData = request.json['messageData']

    # Authenticate the user
    user_data = user_storage.get_user_by_api_key(api_key)
    if user_data is None:
        return Response(status=401)

    # Get the recipient user data
    recipient = user_storage.get_user_by_email(recipient_email)

    if recipient is None:
        return get_message_error(404, "Recipient not found")

    recipient_messaging_tokens = user_storage.get_messaging_tokens(recipient["user_id"])

    if messageType == "text":
        return send_text_message(user_data, recipient, recipient_messaging_tokens, messageData)

    return get_message_error(418, "Message type not supported")


# This is the endpoint that the client will use to get the chats sent to them
@app.route('/get_chats', methods=['GET'])
def get_chats():
    api_key = request.args['apiKey']

    # Authenticate the user
    user_data = user_storage.get_user_by_api_key(api_key)
    if user_data is None:
        return Response(status=401)

    # Get the messages
    chats = message_storage.get_chats(user_data["user_id"])

    return json.dumps(chats), 200, {'Content-Type': 'application/json'}


# This is the endpoint that the client will use to get the message with a specific user
@app.route('/get_messages', methods=['GET'])
def get_messages():
    api_key = request.args['apiKey']
    recipient_email = request.args['recipientEmail']

    # Authenticate the user
    user_data = user_storage.get_user_by_api_key(api_key)
    if user_data is None:
        return Response(status=401)

    # Get the recipient user data
    recipient = user_storage.get_user_by_email(recipient_email)

    if recipient is None:
        return get_message_error(404, "Recipient not found")

    # Get the messages
    messages = message_storage.get_messages(user_data["user_id"], recipient["user_id"])

    return json.dumps(messages), 200, {'Content-Type': 'application/json'}

@app.route('/get_user', methods=['GET'])
def get_user():
    api_key = request.args['apiKey']
    userEmail = request.args['userEmail']

    # Authenticate the user
    user_data = user_storage.get_user_by_api_key(api_key)
    if user_data is None:
        return Response(status=401)

    targetUserData = user_storage.get_user_by_email(userEmail)

    data = {}
    data['name'] = targetUserData['name']
    data['email'] = targetUserData['email']
    data['picture'] = targetUserData['picture']

    return json.dumps(data), 200, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8088, debug=True)

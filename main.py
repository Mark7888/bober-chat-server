from flask import Flask, render_template, request, Response
from flask_sock import Sock

from firebase_functions import do_auth, send_message, generate_local_api_key
from message_sender import get_message_error, send_text_message
from storage_manager import UserStorage, MessageStorage

app = Flask(__name__)
sock = Sock(app)

# Initialize storage manager objects
user_storage = UserStorage()


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

    if messageType == "text":
        return send_text_message(user_data, recipient, messageData)

    return get_message_error(418, "Message type not supported")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8088, debug=True)

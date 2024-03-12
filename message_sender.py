from flask import Response

from firebase_functions import send_message
from storage_manager import MessageStorage, generate_message_id

import time

message_storage = MessageStorage()


def get_message_error(code, message):
    data = {
        "error": "true",
        "code": code,
        "message": message
    }
    return Response(status=code, content_type="application/json", response=data)


# This function sends a text message to the recipient
def send_text_message(user_data, recipient, message_data):
    data = {
        "messageType": "text",
        "message": message_data,
        "senderName": user_data['name'],
        "senderEmail" : user_data['email'],
        "senderPicture": user_data['picture'],
        "id": generate_message_id(user_data['user_id'], recipient['user_id'])
    }

    # Send the message to the recipient
    send_message(recipient['messaging_token'], data=data)

    # Save the message to the storage
    message_time = round(time.time() * 1000)
    message_storage.add_message(user_data["user_id"], recipient["user_id"], "text", message_data, message_time)

    return Response(status=200)


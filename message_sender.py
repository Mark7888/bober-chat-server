from flask import Response

from firebase_functions import send_message
from storage_manager import MessageStorage


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
        "message_type": "text",
        "message": message_data,
        "sender_name": user_data['name'],
        "sender_email" : user_data['email'],
        "sender_picture": user_data['picture']
    }

    # Send the message to the recipient
    send_message(recipient['messaging_token'], data=data)

    message_storage.add_message(user_data, recipient, "text", message_data)

    return Response(status=200)


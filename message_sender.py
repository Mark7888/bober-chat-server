from flask import Response

from firebase_functions import send_message
from database_manager import DatabaseManager, MessageStorage

from datetime import datetime


def get_message_error(code, message):
    data = {
        "error": "true",
        "code": code,
        "message": message
    }
    return Response(status=code, content_type="application/json", response=data)


# This function sends a text message to the recipient
def send_firebase_message(user_data, recipient, recipient_messaging_tokens, message_data, message_type):
    database_manager = DatabaseManager()
    message_storage = MessageStorage(database_manager)
    
    # Save the message to the storage
    message_time = datetime.now()
    message_storage.add_message(user_data["user_id"], recipient["user_id"], message_type, message_data, message_time)

    if len(recipient_messaging_tokens) == 0:
        return get_message_error(404, "Recipient has no messaging tokens")
    
    data = {
        "messageType": message_type,
        "message": message_data,
        "senderName": user_data['name'],
        "senderEmail" : user_data['email'],
        "senderPicture": user_data['picture']
    }

    # Send the message to the recipient
    send_message(recipient_messaging_tokens, data=data)

    return Response(status=200)

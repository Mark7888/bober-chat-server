import json
from datetime import datetime

from database_manager import DatabaseManager, UserManager, MessageStorage

db_manager = DatabaseManager()
user_manager = UserManager(db_manager)
message_storage = MessageStorage(db_manager)

with open("data/users.json", "r", encoding="utf-8") as file:
    users = json.load(file)["users"]

for user_id in users:
    u = {
        "uid": user_id,
        "email": users[user_id]["email"],
        "name": users[user_id]["name"],
        "picture": users[user_id]["picture"]
    }
    user_manager.add_user(u, None, None)

with open("data/messages.json", "r", encoding="utf-8") as file:
    messages = json.load(file)

for message in messages:
    sender = message["sender_id"]
    recipient = message["recipient_id"]
    message_type = message["message_type"]
    message_data = message["message"]
    message_time = message["time"]

    # get datetime from millisecond timestamp
    message_time = message_time / 1000.0
    message_time = datetime.fromtimestamp(message_time)

    message_storage.add_message(sender, recipient, message_type, message_data, message_time)

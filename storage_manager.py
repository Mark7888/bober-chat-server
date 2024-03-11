import json
import os
import time
import hashlib

USER_STORAGE_FILE = "data/users.json"
MESSAGE_STORAGE_FILE = "data/messages.json"


class UserStorage:
    def __init__(self):
        self.users = {}
        self.api_keys = {}

    def add_user(self, user, messaging_token, api_key):
        self.load()

        self.users[user["uid"]] = self.get_user_dict(user["name"], user["picture"], user["uid"], user["email"], messaging_token)
        self.api_keys[api_key] = user["uid"]

        self.save()

    def get_user_dict(self, name, picture, user_id, email, messaging_token):
        return {
            "name": name,
            "picture": picture,
            "user_id": user_id,
            "email": email,
            "messaging_token": messaging_token
        }

    def get_user(self, user_id):
        self.load()

        return self.users[user_id]

    def get_user_by_email(self, email):
        self.load()

        for user in self.users.values():
            if user["email"] == email:
                return user

        return None

    def get_user_by_api_key(self, api_key):
        self.load()

        return self.users[self.api_keys[api_key]]


    def load(self):
        if not os.path.exists(USER_STORAGE_FILE):
            self.users = {}
            self.api_keys = {}
            return

        with open(USER_STORAGE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            self.users = data["users"]
            self.api_keys = data["api_keys"]

    def save(self):
        with open(USER_STORAGE_FILE, "w", encoding="utf-8") as file:
            data = {
                "users": self.users,
                "api_keys": self.api_keys
            }
            json.dump(data, file, indent=2)


class MessageStorage:
    def __init__(self):
        self.messages = []

    def add_message(self, sender_id, recipient_id, message_type, message_data, message_time):
        self.load()

        message = self.get_message_dict(sender_id, recipient_id, message_type, message_data, message_time)
        self.messages.append(message)

        self.save()

    def get_message_dict(self, sender_id, recipient_id, message_type, message_data, message_time):
        id = generate_message_id(sender_id, recipient_id)

        return {
            "id": id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "message_type": message_type,
            "message": message_data,
            "time": message_time
        }

    def load(self):
        if not os.path.exists(MESSAGE_STORAGE_FILE):
            print("No message storage file found")
            self.messages = []
            return

        with open(MESSAGE_STORAGE_FILE, "r", encoding="utf-8") as file:
            self.messages = json.load(file)

    def save(self):
        with open(MESSAGE_STORAGE_FILE, "w", encoding="utf-8") as file:
            json.dump(self.messages, file, indent=2)


    def get_chats(self, user_id, limit=100):
        self.load()

        chats = {}

        for message in self.messages:
            if message["sender_id"] == user_id or message["recipient_id"] == user_id:
                if message["sender_id"] == user_id:
                    partner_id = message["recipient_id"]
                else:
                    partner_id = message["sender_id"]


                if partner_id in chats and message["time"] <= chats[partner_id]["last_message_time"]:
                    continue


                chat = {}

                partner = UserStorage().get_user(partner_id)
                chat["partner_name"] = partner["name"]
                chat["partner_email"] = partner["email"]
                chat["partner_picture"] = partner["picture"]
                chat["last_message_time"] = message["time"]
                # chat["last_message"] = message["message"]

                chats[partner_id] = chat

        chats = dict(sorted(chats.items(), key=lambda item: item[1]['last_message_time'], reverse=True))

        return list(chats.values())[:min(limit, len(chats))]


    def get_messages(self, user_id, recipient_id, limit=100):
        self.load()

        messages = []
        for message in self.messages:
            if message["sender_id"] == user_id and message["recipient_id"] == recipient_id:
                message["is_sent"] = True
                messages.append(message)
            elif message["sender_id"] == recipient_id and message["recipient_id"] == user_id:
                message["is_sent"] = False
                messages.append(message)

        #sort by time descending
        messages.sort(key=lambda x: x["time"], reverse=True)

        # cut messages length by limit
        messages = messages[:min(limit, len(messages))]

        #sort by time ascending
        messages.sort(key=lambda x: x["time"])

        return messages

def generate_message_id(sender_id, recipient_id):
    combined_string = str(time.time()) + sender_id + recipient_id
    hashed_string = hashlib.sha256(combined_string.encode()).hexdigest()
    return hashed_string

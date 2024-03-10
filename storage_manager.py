import json
import os

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
        with open(USER_STORAGE_FILE, "r") as file:
            data = json.load(file)
            self.users = data["users"]
            self.api_keys = data["api_keys"]
    
    def save(self):
        with open(USER_STORAGE_FILE, "w") as file:
            data = {
                "users": self.users,
                "api_keys": self.api_keys
            }
            json.dump(data, file, indent=2)


class MessageStorage:
    def __init__(self):
        self.messages = []

    def add_message(self, sender, recipient, message_type, message_data):
        self.load()

        message = self.get_message_dict(sender["uid"], recipient["uid"], message_type, message_data)
        self.messages.append(message)

        self.save()

    def get_message_dict(self, sender_id, recipient_id, message_type, message_data):
        return {
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "message_type": message_type,
            "message": message_data
        }

    def load(self):
        with open(MESSAGE_STORAGE_FILE, "r") as file:
            self.messages = json.load(file)
    
    def save(self):
        with open(MESSAGE_STORAGE_FILE, "w") as file:
            json.dump(self.messages, file, indent=2)

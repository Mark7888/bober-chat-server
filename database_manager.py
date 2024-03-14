from os import getenv
from datetime import datetime
from dateutil.relativedelta import relativedelta

from mysql.connector import connect as dbconnect

from dotenv import load_dotenv
load_dotenv()




MYSQL_HOST = getenv("MYSQL_HOST")
MYSQL_USER = getenv("MYSQL_USER")
MYSQL_PASSWORD = getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = getenv("MYSQL_DATABASE")

class DatabaseManager:
    def __init__(self):
        self.connection = dbconnect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        self.cursor = self.connection.cursor()

        self.create_tables()

    def create_tables(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Users (UserId VARCHAR(255) PRIMARY KEY, Email VARCHAR(255) UNIQUE, Name VARCHAR(255), PictureUrl VARCHAR(255));")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS ApiKeys (ApiKey VARCHAR(255) PRIMARY KEY, UserId VARCHAR(255), Expiration DATETIME, FOREIGN KEY (UserId) REFERENCES Users(UserId));")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS MessagingTokens (MessagingToken VARCHAR(255) PRIMARY KEY, UserId VARCHAR(255), Expiration DATETIME, FOREIGN KEY (UserId) REFERENCES Users(UserId));")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Messages (MessageId INT AUTO_INCREMENT PRIMARY KEY, SenderId VARCHAR(255), RecipientId VARCHAR(255), MessageType VARCHAR(255), Message TEXT, Timestamp DATETIME, FOREIGN KEY (SenderId) REFERENCES Users(UserId), FOREIGN KEY (RecipientId) REFERENCES Users(UserId));")
        self.connection.commit()

    def get_connection(self):
        return self.connection

    def get_cursor(self):
        return self.cursor


db_manager = DatabaseManager()

class UserManager:
    def __init__(self, connection, cursor):
        self.connection = connection
        self.cursor = cursor

    def generate_user_dict(self, name, picture, user_id, email, messaging_token):
         return {
             "name": name,
             "picture": picture,
             "user_id": user_id,
             "email": email,
             "messaging_token": messaging_token
         }

    def add_user(self, user, messaging_token, api_key):
        now = datetime.now()
        expiration = now + relativedelta(days=1)
        expiration_string = expiration.strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute("INSERT INTO Users (UserId, Email, Name, PictureUrl) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE Name = VALUES(Name), PictureUrl = VALUES(PictureUrl), Email = VALUES(Email)", (user["uid"], user["name"], user["picture"], user["email"]))
        self.cursor.execute("INSERT INTO ApiKeys (ApiKey, UserId, Expiration) VALUES (%s, %s, %s)", (api_key, user["uid"], expiration_string))
        self.cursor.execute("INSERT INTO MessagingTokens (MessagingToken, UserId, Expiration) VALUES (%s, %s, %s)", (messaging_token, user["uid"], expiration_string))

        self.connection.commit()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM Users WHERE UserId=%s", (user_id,))
        user_data = self.cursor.fetchone()
        print(user_data)

    def get_user_by_api_key(self, api_key):
        self.cursor.execute("SELECT * FROM ApiKeys WHERE ApiKey=%s", (api_key,))
        api_key_data = self.cursor.fetchone()

        # check if not expired
        # strftime("%Y-%m-%d %H:%M:%S")
        print(api_key_data)
        if api_key_data and datetime.strptime(api_key_data[2], "%Y-%m-%d %H:%M:%S") > datetime.now():
            self.cursor.execute("SELECT * FROM Users WHERE UserId=%s", (api_key_data[1],))
            user_data = self.cursor.fetchone()
            print(user_data)

    def get_user_by_email(self, email):
        self.cursor.execute("SELECT * FROM Users WHERE Email=%s", (email,))
        user_data = self.cursor.fetchone()
        print(user_data)

    def get_messaging_tokens(self, user_id):
        self.cursor.execute("SELECT * FROM MessagingTokens WHERE UserId=%s", (user_id,))
        messaging_tokens = self.cursor.fetchall()
        print(messaging_tokens)


user_manager = UserManager(db_manager.get_connection(), db_manager.get_cursor())
user_manager.get_user("id123")
user_manager.get_user_by_api_key("apikey2")
user_manager.get_user_by_email("email@")
user_manager.get_messaging_tokens("id123")

"""
{
  "id": "0",
  "sender_id": "aJcJdmnzpUW8qFRpqwoGRybCA902",
  "recipient_id": "aJcJdmnzpUW8qFRpqwoGRybCA902",
  "message_type": "text",
  "message": "Hello",
  "time": 1710167361369
},
"""

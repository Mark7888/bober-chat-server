from os import getenv
from datetime import datetime
from dateutil.relativedelta import relativedelta
from base64 import b64encode, b64decode

from mysql.connector import connect as dbconnect

from dotenv import load_dotenv
load_dotenv()


MYSQL_HOST = getenv("MYSQL_HOST")
MYSQL_PORT = getenv("MYSQL_PORT")
MYSQL_USER = getenv("MYSQL_USER")
MYSQL_PASSWORD = getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = getenv("MYSQL_DATABASE")

class DatabaseManager:
    def __init__(self):
        self.connection = dbconnect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        self.cursor = self.connection.cursor()

        self.create_tables()

    def create_tables(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Users (UserId VARCHAR(255) PRIMARY KEY, Email VARCHAR(255) UNIQUE, Name VARCHAR(255), PictureUrl VARCHAR(255)) ENGINE=InnoDB;")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS ApiKeys (ApiKey VARCHAR(255) PRIMARY KEY, UserId VARCHAR(255), Expiration DATETIME(3), FOREIGN KEY (UserId) REFERENCES Users(UserId)) ENGINE=InnoDB;")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS MessagingTokens (MessagingToken VARCHAR(255) PRIMARY KEY, UserId VARCHAR(255), Expiration DATETIME(3), FOREIGN KEY (UserId) REFERENCES Users(UserId)) ENGINE=InnoDB;")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Messages (MessageId INT AUTO_INCREMENT PRIMARY KEY, SenderId VARCHAR(255), RecipientId VARCHAR(255), MessageType VARCHAR(255), Message TEXT, Timestamp DATETIME(3), FOREIGN KEY (SenderId) REFERENCES Users(UserId), FOREIGN KEY (RecipientId) REFERENCES Users(UserId)) ENGINE=InnoDB;")
        self.connection.commit()

    def get_connection(self):
        return self.connection

    def get_cursor(self):
        return self.cursor


class UserManager:
    def __init__(self, db_manager):
        self.connection = db_manager.get_connection()
        self.cursor = db_manager.get_cursor()


    def generate_user_dict(self, user_id, email, name, picture):
         return {
             "name": name,
             "picture": picture,
             "user_id": user_id,
             "email": email
         }

    def add_user(self, user, messaging_token, api_key):
        now = datetime.now()
        expiration = now + relativedelta(days=1)
        expiration_string = expiration.strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute("INSERT INTO Users (UserId, Email, Name, PictureUrl) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE Name = VALUES(Name), PictureUrl = VALUES(PictureUrl), Email = VALUES(Email)", (user["uid"], user["email"], user["name"], user["picture"]))
        
        if api_key:
            self.cursor.execute("INSERT IGNORE INTO ApiKeys (ApiKey, UserId, Expiration) VALUES (%s, %s, %s)", (api_key, user["uid"], expiration_string))
        if messaging_token:
            self.cursor.execute("INSERT IGNORE INTO MessagingTokens (MessagingToken, UserId, Expiration) VALUES (%s, %s, %s)", (messaging_token, user["uid"], expiration_string))

        self.connection.commit()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM Users WHERE UserId=%s", (user_id,))
        user_data = self.cursor.fetchone()

        if user_data:
            return self.generate_user_dict(user_data[0], user_data[1], user_data[2], user_data[3])

    def get_user_by_api_key(self, api_key):
        now = datetime.now()
        now_string = now.strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("SELECT * FROM ApiKeys WHERE ApiKey=%s AND Expiration>=%s", (api_key, now_string,))
        api_key_data = self.cursor.fetchone()

        if not api_key_data:
            return
        
        self.cursor.execute("SELECT * FROM Users WHERE UserId=%s", (api_key_data[1],))
        user_data = self.cursor.fetchone()
        
        if user_data:
            return self.generate_user_dict(user_data[0], user_data[1], user_data[2], user_data[3])

    def get_user_by_email(self, email):
        self.cursor.execute("SELECT * FROM Users WHERE Email=%s", (email,))
        user_data = self.cursor.fetchone()
        
        if user_data:
            return self.generate_user_dict(user_data[0], user_data[1], user_data[2], user_data[3])

    def get_messaging_tokens(self, user_id):
        self.cursor.execute("SELECT * FROM MessagingTokens WHERE UserId=%s", (user_id,))
        messaging_tokens = self.cursor.fetchall()

        return [messaging_token[0] for messaging_token in messaging_tokens]

    def clear_expired_tokens(self):
        now = datetime.now()
        now_string = now.strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("DELETE FROM ApiKeys WHERE Expiration<%s", (now_string,))
        self.cursor.execute("DELETE FROM MessagingTokens WHERE Expiration<%s", (now_string,))
        self.connection.commit()


class MessageStorage:
    def __init__(self, db_manager):
        self.connection = db_manager.get_connection()
        self.cursor = db_manager.get_cursor()


    def add_message(self, sender_id, recipient_id, message_type, message_data, message_time):
        message_time_string = message_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        message_base64 = b64encode(message_data.encode()).decode()

        self.cursor.execute("INSERT INTO Messages (SenderId, RecipientId, MessageType, Message, Timestamp) VALUES (%s, %s, %s, %s, %s)", (sender_id, recipient_id, message_type, message_base64, message_time_string))
        self.connection.commit()


    def get_chats(self, user_id, limit=100):
        query = f"""
            SELECT 
                CASE 
                    WHEN m.SenderId = '{user_id}' THEN recipient.Name 
                    ELSE sender.Name 
                END AS partner_name,
                CASE 
                    WHEN m.SenderId = '{user_id}' THEN recipient.Email 
                    ELSE sender.Email 
                END AS partner_email,
                CASE 
                    WHEN m.SenderId = '{user_id}' THEN recipient.PictureUrl 
                    ELSE sender.PictureUrl 
                END AS partner_picture,
                MAX(m.Timestamp) AS last_message_time
            FROM 
                Messages m
            JOIN 
                Users sender ON m.SenderId = sender.UserId
            JOIN 
                Users recipient ON m.RecipientId = recipient.UserId
            WHERE 
                m.SenderId = '{user_id}' OR m.RecipientId = '{user_id}'
            GROUP BY 
                partner_name, partner_email, partner_picture
            ORDER BY 
                last_message_time DESC
            LIMIT {limit}
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        chats = []

        for row in rows:
            chat = {
                "partner_name": row[0],
                "partner_email": row[1],
                "partner_picture": row[2],
                "last_message_time": int(row[3].timestamp() * 1000)
            }
            chats.append(chat)

        return chats
    
    def get_messages(self, user_id, recipient_id, limit=100):
        query = f"""
            SELECT 
                MessageId, SenderId, RecipientId, MessageType, Message, Timestamp
            FROM 
                Messages
            WHERE 
                (SenderId = '{user_id}' AND RecipientId = '{recipient_id}') 
                OR 
                (SenderId = '{recipient_id}' AND RecipientId = '{user_id}')
            ORDER BY 
                Timestamp DESC
            LIMIT {limit}
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        messages = []
        for row in rows:
            is_sent = True if row[1] == user_id else False
            message = {
                "id": row[0],
                "sender_id": row[1],
                "recipient_id": row[2],
                "message_type": row[3],
                "message": b64decode(row[4]).decode(),
                "time": int(row[5].timestamp() * 1000),
                "is_sent": is_sent
            }
            messages.append(message)

        # Sort messages by time descending
        messages.sort(key=lambda x: x["time"], reverse=True)

        return messages

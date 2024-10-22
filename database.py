import os
import psycopg2

class Database:
    def __init__(self):
        info = {
            "user": os.getenv("PG_USER"),
            "password": os.getenv("PG_PASSWORD"),
            "database": os.getenv("PG_DATABASE"),
            "host": os.getenv("PG_HOST"),
            "port": os.getenv("PG_PORT")
        }
        if info["user"] is None or info["password"] is None or info["database"] is None or info["host"] is None or info["port"] is None:
            print("Missing environment variables for database connection. Please include PG_USER, PG_PASSWORD, PG_DATABASE, PG_HOST, and PG_PORT.")
        self.connection = psycopg2.connect(**info)
        self.cursor = self.connection.cursor()
    
    def __del__(self):
        self.cursor.close()
        self.connection.close()

    def find_user(self, discord_id):
        self.cursor.execute("SELECT * FROM users WHERE discord_id = %s", (discord_id,))
        return self.cursor.fetchone()
    
    def find_user_by_username(self, username):
        self.cursor.execute("SELECT * FROM users WHERE lc_username = %s", (username,))
        return self.cursor.fetchone()
    
    def get_all_users(self):
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()
    
    def add_user(self, discord_id, username):
        self.cursor.execute("INSERT INTO users (discord_id, lc_username) VALUES (%s, %s)", (discord_id, username))
        self.connection.commit()

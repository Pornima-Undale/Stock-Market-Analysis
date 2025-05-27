# database_manager.py
import mysql.connector
from mysql.connector import Error
import json
import socket
from datetime import datetime


class DatabaseManager:
    _instance = None

    @classmethod
    def get_instance(cls, host="localhost", user="root", password="Pornima#Undale28", database="STOCKMARKET_PROJECT"):
        """Singleton pattern to ensure only one database connection exists"""
        if cls._instance is None:
            cls._instance = DatabaseManager(host, user, password, database)
        return cls._instance

    def __init__(self, host, user, password, database):
        """Initialize connection - should typically only be called through get_instance()"""
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Establish a database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )

            if self.connection.is_connected():
                print("✅ Database Connection Established")
                self.cursor = self.connection.cursor(dictionary=True)
                return True
            return False
        except Error as e:
            print(f"❌ Connection Error: {e}")
            self.connection = None
            self.cursor = None
            return False

    def ensure_connection(self):
        """Ensure database connection is active"""
        try:
            if self.connection is None or not self.connection.is_connected():
                print("Database connection lost, reconnecting...")
                return self.connect()
            return True
        except Error as e:
            print(f"Failed to reconnect: {e}")
            return False

    def execute_query(self, query, params=None, commit=False):
        """Execute a database query with automatic reconnection"""
        try:
            if not self.ensure_connection():
                return False, "Database connection failed"

            self.cursor.execute(query, params or ())

            if commit:
                self.connection.commit()

            return True, None
        except Error as e:
            print(f"❌ Query error: {e}")
            return False, str(e)

    def fetchone(self):
        """Fetch one result after executing a query"""
        if self.cursor:
            return self.cursor.fetchone()
        return None

    def fetchall(self):
        """Fetch all results after executing a query"""
        if self.cursor:
            return self.cursor.fetchall()
        return []

    def close(self):
        """Close the database connection"""
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'connection') and self.connection and self.connection.is_connected():
                self.connection.close()
                print("Database connection closed")
        except Error as e:
            print(f"❌ Error closing connection: {e}")
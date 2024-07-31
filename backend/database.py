import sqlite3
from sqlite3 import Error
import os

DB_FILE = "user_database.db"

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except Error as e:
        print(e)
    return conn

def create_table(conn):
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      email TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL,
                      role TEXT NOT NULL)''')
    except Error as e:
        print(e)

def init_db():
    conn = create_connection()
    if conn is not None:
        create_table(conn)
        conn.close()
    else:
        print("Error! Cannot create the database connection.")

init_db()
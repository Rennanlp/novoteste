# database.py
import sqlite3

DATABASE_PATH = 'tasks.db'

def create_table():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            task TEXT NOT NULL,
            data TEXT NOT NULL,
            observation TEXT,
            qtd TEXT
        )
    ''')

    conn.commit()
    conn.close()

def insert_data(username, task, data, observation, qtd):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO tasks (username, task, data, observation, qtd)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, task, data, observation, qtd))

    conn.commit()
    conn.close()


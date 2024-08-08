import sqlite3

conn = sqlite3.connect('database1.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY,
        titulo TEXT NOT NULL,
        url TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS trello (
        id INTEGER PRIMARY KEY,
        nome TEXT NOT NULL,
        link TEXT NOT NULL,
        responsavel TEXT NOT NULL,
        CD TEXT
    )
''')

conn.commit()
conn.close()

import sqlite3

DB_NAME = "scheduling.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            schedule BLOB,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')

    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))

    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username=?', (username,))
    user = cursor.fetchone()

    conn.close()
    return user

def update_schedule(username, schedule):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('REPLACE INTO schedules (username, schedule) VALUES (?, ?)', (username, schedule))

    conn.commit()
    conn.close()

def get_schedule(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT schedule FROM schedules WHERE username=?', (username,))
    schedule = cursor.fetchone()

    conn.close()
    return schedule

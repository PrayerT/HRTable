import sqlite3
import os
import hashlib

DB_FILE = 'schedule.db'

def init_database():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 创建用户表
        cursor.execute('''CREATE TABLE users
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           username TEXT UNIQUE NOT NULL,
                           password TEXT NOT NULL);''')

        # 创建排班表
        cursor.execute('''CREATE TABLE schedule
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           user_id INTEGER NOT NULL,
                           week_day INTEGER NOT NULL,
                           employee_name TEXT NOT NULL,
                           FOREIGN KEY (user_id) REFERENCES users (id));''')

        conn.commit()
        conn.close()

def connect_database():
    return sqlite3.connect(DB_FILE)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user(username, password):
    conn = connect_database()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
    result = cursor.fetchone()

    conn.close()

    return result is not None

def update_schedule(user_id, week_day, employees):
    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM schedule WHERE user_id = ? AND week_day = ?", (user_id, week_day))

    for employee_name in employees:
        cursor.execute("INSERT INTO schedule (user_id, week_day, employee_name) VALUES (?, ?, ?)", (user_id, week_day, employee_name))
        print(f"Saving employee {employee_name} for user {user_id} on week_day {week_day}")  # 添加 log 输出

    conn.commit()
    conn.close()

def get_schedule(user_id, week_day):
    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("SELECT employee_name FROM schedule WHERE user_id = ? AND week_day = ?", (user_id, week_day))
    result = cursor.fetchall()

    conn.close()

    return [row[0] for row in result]

def isRegistered():
    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    result = cursor.fetchone()
    user_count = result[0]

    conn.close()

    return user_count > 0

if __name__ == '__main__':
    init_database()

from flask import Flask, request, jsonify
import os
import sqlite3
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Корректный путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'users.db')

# Инициализация базы данных
def init_db():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER, multiplier INTEGER, rank INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS purchased_upgrades (user_id INTEGER, level INTEGER)''')
        conn.commit()
        conn.close()
        print(f"База данных инициализирована: {DB_PATH}")
    except sqlite3.OperationalError as e:
        print(f"Ошибка базы данных: {e}")
        raise

init_db()

@app.route('/update_score', methods=['POST'])
def update_score():
    data = request.json
    user_id = data['user_id']
    username = data.get('username', 'Unknown')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance, multiplier FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if user:
        balance, multiplier = user
        new_balance = balance + multiplier
        c.execute("UPDATE users SET balance = ?, username = ? WHERE user_id = ?", (new_balance, username, user_id))
    else:
        c.execute("INSERT INTO users (user_id, username, balance, multiplier, rank) VALUES (?, ?, ?, ?, ?)", (user_id, username, 1, 1, 0))
    conn.commit()
    update_ranks()
    conn.close()
    return jsonify({'status': 'success', 'balance': new_balance if user else 1})

@app.route('/get_balance', methods=['GET'])
def get_balance():
    user_id = request.args.get('user_id')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance, multiplier, username FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({'balance': user[0], 'multiplier': user[1], 'username': user[2]})
    return jsonify({'balance': 0, 'multiplier': 1, 'username': 'Unknown'})

@app.route('/get_top_users', methods=['GET'])
def get_top_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10")
    top_users = c.fetchall()
    conn.close()
    return jsonify([{'username': user[0], 'balance': user[1]} for user in top_users])

@app.route('/get_properties', methods=['GET'])
def get_properties():
    with open(os.path.join(BASE_DIR, '..', 'propirties.js'), 'r') as f:
        js_content = f.read()
    return jsonify({'properties': js_content})

def update_ranks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, balance FROM users ORDER BY balance DESC")
    users = c.fetchall()
    for i, (user_id, _) in enumerate(users):
        c.execute("UPDATE users SET rank = ? WHERE user_id = ?", (i + 1, user_id))
    conn.commit()
    conn.close()

@app.route('/start')
def start():
    return app.send_static_file('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
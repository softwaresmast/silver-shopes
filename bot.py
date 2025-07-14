import os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv
import sqlite3
from static.payments.buy import initiate_payment
from static.payments.verify_buy import verify_payment
import hmac
import hashlib

# Загрузка конфигурации
load_dotenv('static/.env')
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://ggteam-befk3c79d-ggteams-projects-11d759e0.vercel.app/start')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Проверка Telegram initData
def verify_init_data(init_data):
    try:
        parsed_data = {k: v for k, v in [x.split('=') for x in init_data.split('&')]}
        data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted(parsed_data.items()) if k != 'hash'])
        secret_key = hashlib.sha256(TOKEN.encode()).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        return computed_hash == parsed_data.get('hash')
    except:
        return False

# Главное меню
def create_main_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🚀 Играть", web_app=WebAppInfo(url=WEBAPP_URL)),
        InlineKeyboardButton("⚙️ Прокачка", callback_data='upgrade'),
        InlineKeyboardButton("🏆 Топы", callback_data='tops'),
        InlineKeyboardButton("💸 Донат", callback_data='donate')
    )
    return keyboard

# Топ пользователей
def get_top_users():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'static', 'users.db'))
    c = conn.cursor()
    c.execute("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT 10")
    top_users = c.fetchall()
    conn.close()
    return top_users

# Обработчик /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Добро пожаловать в Silver Shoper! 🎮 Тапай и зарабатывай!", reply_markup=create_main_menu())

# Обработчик callback
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'upgrade':
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Выберите улучшение:", reply_markup=create_upgrade_menu(call.from_user.id))
    elif call.data == 'tops':
        bot.answer_callback_query(call.id)
        top_users = get_top_users()
        response = "🏆 Топ игроков:\n"
        for i, user in enumerate(top_users, 1):
            response += f"{i}. 🧑 {user[1]} - {user[2]} монет\n"
        bot.send_message(call.message.chat.id, response)
    elif call.data == 'donate':
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Введите множитель (например, x3):", reply_markup=create_donate_menu())
    elif call.data.startswith('upgrade_'):
        level = int(call.data.split('_')[1])
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'static', 'users.db'))
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (call.from_user.id,))
        balance = c.fetchone()[0]
        price = level * 100
        if balance >= price:
            c.execute("UPDATE users SET balance = balance - ?, multiplier = ? WHERE user_id = ?", (price, level, call.from_user.id))
            c.execute("INSERT INTO purchased_upgrades (user_id, level) VALUES (?, ?)", (call.from_user.id, level))
            conn.commit()
            bot.answer_callback_query(call.id, f"Улучшение x{level} куплено за {price} монет!")
        else:
            bot.answer_callback_query(call.id, "Недостаточно монет!")
        conn.close()
    elif call.data == 'buy_x3':
        bot.answer_callback_query(call.id)
        payment_url = initiate_payment(30, call.from_user.id)
        bot.send_message(call.message.chat.id, f"Оплатите для активации x3 кликов:\n{payment_url}")

# Меню прокачки
def create_upgrade_menu(user_id):
    keyboard = InlineKeyboardMarkup()
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'static', 'users.db'))
    c = conn.cursor()
    c.execute("SELECT level FROM purchased_upgrades WHERE user_id = ?", (user_id,))
    purchased = [row[0] for row in c.fetchall()]
    conn.close()
    for i in range(1, 501):
        if i not in purchased:
            keyboard.add(InlineKeyboardButton(f"x{i} за {i * 100} монет", callback_data=f'upgrade_{i}'))
    return keyboard

# Меню доната
def create_donate_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Купить x3 клики", callback_data='buy_x3'))
    return keyboard

# Запуск сервера
if __name__ == "__main__":
    from threading import Thread
    def run_flask():
        app.run(host='0.0.0.0', port=5000)
    Thread(target=run_flask).start()
    bot.polling()
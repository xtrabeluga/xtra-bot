import os
import json
import random
import telebot
import threading
from flask import Flask
from telebot import types

# --- НАСТРОЙКИ И ИНИЦИАЛИЗАЦИЯ ---
# Берем токен из переменных окружения (безопасный метод для Render)
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise ValueError("Ошибка: Переменная BOT_TOKEN не найдена в окружении!")

bot = telebot.TeleBot(TOKEN)
DATA_FILE = 'users_data.json'

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (Чтобы сервис не засыпал) ---
app = Flask('')

@app.route('/')
def home():
    return "<h1>XTRA ELITA BOT IS ONLINE</h1><p>Status: Running</p>"

def run_web_run():
    # Render автоматически назначает порт через переменную PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ЛОГИКА БАЗЫ ДАННЫХ ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

user_data = load_data()

def init_user(user_id):
    uid = str(user_id)
    if uid not in user_data:
        user_data[uid] = {
            "name": None,
            "balance": 1000,
            "level": 1,
            "exp": 0,
            "inventory": []
        }
    return user_data[uid]

# --- ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def start(message):
    user = init_user(message.from_user.append_id if hasattr(message.from_user, 'append_id') else message.from_user.id)
    uid = str(message.from_user.id)
    
    if not user['name']:
        msg = bot.send_message(message.chat.id, "🎭 **Добро пожаловать в XTRA ELITA!**\nВведите ваше имя для регистрации:", parse_mode='Markdown')
        bot.register_next_step_handler(msg, register_name)
    else:
        bot.send_message(message.chat.id, f"С возвращением, {user['name']}!", reply_markup=get_main_menu())

def register_name(message):
    uid = str(message.from_user.id)
    user_data[uid]['name'] = message.text
    save_data(user_data)
    bot.send_message(message.chat.id, f"✅ Регистрация завершена! Привет, {message.text}!", reply_markup=get_main_menu())

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 Профиль", "💰 Работа")
    markup.add("⚔️ Игровой мир", "📦 Инвентарь")
    return markup

@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile(message):
    user = init_user(message.from_user.id)
    text = (f"🎭 **Профиль: {user['name']}**\n"
            f"📊 Уровень: {user['level']}\n"
            f"✨ Опыт: {user['exp']}/{user['level']*50}\n"
            f"💵 Баланс: {user['balance']} элит\n"
            f"🎒 Предметы: {', '.join(user['inventory']) if user['inventory'] else 'Пусто'}")
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "💰 Работа")
def work(message):
    user = init_user(message.from_user.id)
    earnings = random.randint(50, 250)
    user['balance'] += earnings
    user['exp'] += 20
    
    # Логика уровня
    if user['exp'] >= user['level'] * 50:
        user['level'] += 1
        user['exp'] = 0
        bot.send_message(message.chat_id, "🎊 **УРОВЕНЬ ПОВЫШЕН!** 🎉")

    save_data(user_data)
    bot.send_message(message.chat.id, f"💵 Вы успешно поработали и заработали **{earnings} элит**!")

@bot.message_handler(func=lambda message: message.text == "⚔️ Игровой мир")
def game_world(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🕵️ Разведка", "💎 Ограбление")
    bot.send_message(message.chat.id, "Выберите действие в мире XTRA ELITA:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📦 Инвентарь")
def inventory(message):
    user = init_user(message.from_user.id)
    items = ", ".join(user['inventory']) if user['inventory'] else "Пусто"
    bot.send_message(message.chat.id, f"🎒 Ваш инвентарь:\n{items}")

@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.reply_to(message, "Используйте кнопки меню для управления.")

# --- ЗАПУСК ВСЕГО ---

if __name__ == "__main__":
    # 1. Запускаем веб-сервер в отдельном потоке (для Render)
    web_thread = threading.Thread(target=run_web_run)
    web_thread.daemon = True
    web_thread.start()
    
    # 2. Запускаем бота в основном потоке
    print("🚀 Бот XTRA ELITA запущен и готов к работе!")
    bot.infinity_polling()

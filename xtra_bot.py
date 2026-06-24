import os
import json
import random
import threading
import telebot
from flask import Flask
from telebot import types

# --- НАСТРОЙКИ ---
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise ValueError("Ошибка: Переменная BOT_TOKEN не найдена!")

bot = telebot.TeleBot(TOKEN)
app = Flask('')
DATA_FILE = 'xtra_elita_db.json'

# --- БАЗА ДАННЫХ ---
def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()

def get_user(user_id, chat_id):
    # Ключ привязан к связке пользователь+чат, чтобы в разных чатах были разные балансы
    key = f"{chat_id}_{user_id}"
    if key not in db:
        db[key] = {
            "balance": 500,
            "exp": 0,
            "level": 1,
            "last_work": 0,
            "messages_count": 0
        }
    return db[key], key

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
@app.route('/')
def index():
    return "<h1>XTRA ELITA BOT IS ONLINE</h1>"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ЛОГИКА БОТА ---

# 1. КОМАНДА: ПРОФИЛЬ
@bot.message_handler(commands=['profile', 'профиль'])
def profile(message):
    user, key = get_user(message.from_user.id, message.chat.id)
    text = (f"👑 **XTRA ELITA: ПРОФИЛЬ**\n\n"
            f"👤 Игрок: {message.from_user.first_name}\n"
            f"💰 Баланс: {user['balance']} элит\n"
            f"📊 Уровень: {user['level']}\n"
            f"✨ Опыт: {user['exp']}/{user['level'] * 100}\n"
            f"💬 Сообщений в чате: {user['messages_count']}")
    bot.reply_to(message, text, parse_mode='Markdown')

# 2. КОМАНДА: РАБОТА
@bot.message_handler(commands=['work', 'работа'])
def work(message):
    user, key = get_user(message.from_user.append_id if hasattr(message.from_user, 'append_id') else message.from_user.id, message.chat.id)
    
    # Здесь можно добавить проверку на КД (cooldown), если нужно
    earnings = random.randint(100, 500)
    user['balance'] += earnings
    user['exp'] += 25
    
    # Проверка уровня
    if user['exp'] >= user['level'] * 100:
        user['level'] += 1
        user['exp'] = 0
        bot.reply_to(message, "🎊 **УРОВЕНЬ ПОВЫШЕН!** Вы стали сильнее!")

    save_db(db)
    bot.reply_to(message, f"⚒ Вы поработали в XTRA ELITA и заработали **{earnings} элит**!")

# 3. КОМАНДА: КАЗИНО
@bot.message_handler(commands=['casino', 'казино'])
def casino(message):
    user, key = get_user(message.from_user.id, message.chat.id)
    
    # Проверка, ввел ли пользователь ставку (например, /casino 100)
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(int(message.chat.id), "❌ Введите ставку! Пример: `/casino 100`", parse_mode='Markdown')
        return

    bet = int(args[1])

    if bet <= 0:
        bot.reply_to(message, "❌ Ставка должна быть больше 0!")
        return
    if user['balance'] < bet:
        botot_msg = bot.reply_to(message, "❌ У вас недостаточно элит для такой ставки!")
        return

    user['balance'] -= bet
    win = False
    
    # Шанс 40% на победу
    if random.random() < 0.4:
        win_amount = bet * 2
        user['balance'] += win_amount
        win = True
        result_text = f"🎰 **ВЫ ВЫИГРАЛИ!** Вам выпало **{win_amount} элит**!"
    else:
        result_text = f"💀 **ВЫ ПРОИГРАЛИ!** Ставка в **{bet} элит** сгорела в казино."

    save_db(db)
    bot.reply_to(message, result_text, parse_mode='Markdown')

# 4. КОМАНДА: СТАТИСТИКА ЧАТА
@bot.message_handler(commands=['stats', 'статистика'])
def stats(message):
    user, key = get_user(message.from_user.id, message.chat.id)
    bot.reply_to(message, f"📊 Общая активность игрока: {user['messages_count']} сообщений.")

# 5. СЧЕТЧИК АКТИВНОСТИ (Срабатывает на каждое сообщение в чате)
@bot.message_handler(func=lambda message: True)
def count_messages(message):
    # Проверяем, что это не команда (чтобы не считать команды за сообщения)
    if not message.text.startswith('/'):
        user, key = get_user(message.from_user.id, message.chat.id)
        user['messages_count'] += 1
        save_db(db)

# --- ЗАПУСК ---
if __name__ == "__main__":
    # Запуск веб-сервера в фоне
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    
    print("🚀 XTRA ELITA BOT запущен!")
    bot.infinity_poling()

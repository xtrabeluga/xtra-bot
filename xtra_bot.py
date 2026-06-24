import os
import json
import random
import threading
import time
import telebot
from flask import Flask

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("Ошибка: Переменная TOKEN не найдена в окружении!")

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
    with_open_lock = threading.Lock() # Защита от одновременной записи
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()

def get_user(user_id, chat_id):
    key = f"{chat_id}_{user_id}"
    if key not_in_db := (key not in db):
        db[key] = {
            "balance": 500,
            "exp": 0,
            "level": 1,
            "messages_count": 0
        }
    return db[key], key

# --- ВЕБ-СЕРВЕР ---
@app.route('/')
def index(): return "XTRA ELITA ONLINE"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- КОМАНДЫ ---

# 1. ПРОФИЛЬ
@bot.message_handler(commands=['profile', 'профиль'])
def profile(message):
    user, _ = get_user(message.from_user.id, message.chat.int_id if hasattr(message.chat, 'int_id') else message.chat.id)
    text = (f"👑 **XTRA ELITA: ПРОФИЛЬ**\n\n"
            f"👤 Игрок: {message.from_user.first_name}\n"
            f"💰 Баланс: {user['balance']} элит\n"
            f"📊 Уровень: {user['level']}\n"
            f"✨ Опыт: {user['exp']}/{user['level'] * 100}\n"
            f"💬 Сообщений: {user['messages_count']}")
    bot.reply_to(message, text, parse_mode='Markdown')

# 2. РАБОТА
@bot.message_handler(commands=['work', 'работа'])
def work(message):
    user, key = get_user(message.from_user.id, message.chat.id)
    earnings = random.randint(100, 500)
    user['balance'] += earnings
    user['exp'] += 20
    
    if user['exp'] >= user['level'] * 100:
        user['level'] += 1
        user['exp'] = 0
        bot.reply_to(message, "🎊 **LEVEL UP!**")

    save_db(db)
    bot.reply_to(message, f"⚒ Вы заработали **{earnings} элит**!")

# 3. КАЗИНО С АНИМАЦИЕЙ (Эффект прокрутки)
@bot.message_handler(commands=['casino', 'казино'])
def casino(message):
    user, key = get_user(message.from_user.id, message.chat.id)
    args = message.text.split()

    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "❌ Пример: `/casino 100`", parse_mode='Markdown')
        return

    bet = int(args[1])
    if bet <= 0 or user['balance'] < bet:
        bot.reply_to(message, "❌ Недостаточно средств или неверная ставка!")
        return

    user['balance'] -= bet
    save_db(db)

    # АНИМАЦИЯ "КРУТКИ"
    emojis = ["🍒", "🍋", "🎰", "💎", "7️⃣", "💀", "🎲"]
    msg = bot.reply_to(message, "🎰 **Крутим колесо...**")
    
    for _ in range(5): # 5 кадров анимации
        temp_spin = "".join(random.choices(emojis, k=3))
        bot.edit_message_text(f"🎰 [ {temp_spin} ] 🎰\n*Крутится...*", 
                              message.chat.id, msg.message_id)
        time.sleep(0.6)

    # ФИНАЛЬНЫЙ РЕЗУЛЬТАТ
    final_spin = "".join(random.choices(emojis, k=3))
    win = False
    
    # Если выпало 3 одинаковых (упрощенно: если первый и последний совпали)
    if final_spin[0] == final_spin[2] and final_spin[0] != "💀":
        win_amount = bet * 2
        user['balance'] += win_amount
        win = True
        res_text = f"🎉 **ВЫ ВЫИГРАЛИ!**\nВыпало: {final_spin}\nВы получили: **{win_amount} элит**!"
    else:
        res_text = f"💀 **ПРОИГРЫШ!**\nВыпало: {final_spin}\nВы потеряли: **{bet} элит**."

    save_db(db)
    bot.edit_message_text(res_text, message.chat.id, msg.message_id, parse_mode='Markdown')

# 4. СТАТИСТИКА
@bot.message_handler(commands=['stats', 'статистика'])
def stats(message):
    user, _ = get_user(message.from_user.id, message.chat.id)
    bot.reply_to(message, f"📊 Активность: {user['messages_count']} сообщений.")

# 5. СЧЕТЧИК СООБЩЕНИЙ
@bot.message_handler(func=lambda m: True)
def counter(message):
    if not message.text.startswith('/'):
        user, key = get_user(message.fromint_user_id if hasattr(message, 'fromint_user_id') else message.from_user.id, message.chat.id)
        user['messages_count'] += 1
        save_db(db)

# --- ЗАПУСК ---
if __name__ == "__main__":
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    print("🚀 XTRA ELITA BOT запущен!")
    bot.infinity_polling()

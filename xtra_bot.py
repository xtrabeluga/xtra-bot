import telebot
import time
import json
import os
import random
from threading import Lock

# ===================== CONFIG =====================
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "xtra_data.json"
lock = Lock()

# ===================== LOAD DATA =====================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with lock:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

data = load_data()

# ===================== UTIL =====================
def get_user(user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "balance": 0,
            "last_daily": 0,
            "last_farm": 0,
            "wins": 0,
            "games": 0
        }
        save_data(data)
    return data[uid]

def save():
    save_data(data)

def format_money(x):
    return f"{x:,}".replace(",", " ")

# ===================== START =====================
@bot.message_handler(commands=['start'])
def start(message):
    u = get_user(message.from_user.id)

    bot.send_message(message.chat.id, f"""
🔥 XTRA ELITA 🔥

💰 Баланс: {format_money(u['balance'])} XTRA

Команды:
/farm — фарм XTRA
/daily — награда
/roulette <ставка> — казино
/profile — профиль
/top — топ
""")

# ===================== FARM =====================
@bot.message_handler(commands=['farm'])
def farm(message):
    u = get_user(message.from_user.id)
    now = time.time()

    if now - u["last_farm"] < 15:
        wait = int(15 - (now - u["last_farm"]))
        bot.send_message(message.chat.id, f"⏳ Подожди {wait} сек")
        return

    reward = random.randint(50, 5000)

    u["balance"] += reward
    u["last_farm"] = now

    save()

    bot.send_message(
        message.chat.id,
        f"⚡ Ты нафармил {format_money(reward)} XTRA"
    )

# ===================== DAILY =====================
@bot.message_handler(commands=['daily'])
def daily(message):
    u = get_user(message.from_user.id)
    now = int(time.time())

    if now - u["last_daily"] < 86400:
        bot.send_message(message.chat.id, "⏳ Уже забрал daily")
        return

    u["balance"] += 1000
    u["last_daily"] = now
    save()

    bot.send_message(message.chat.id, "🎁 +1000 XTRA")

# ===================== ROULETTE (UPDATED BET) =====================
@bot.message_handler(commands=['roulette'])
def roulette(message):
    u = get_user(message.from_user.id)

    try:
        parts = message.text.split()
        bet = int(parts[1]) if len(parts) > 1 else 100
    except:
        bet = 100

    if bet <= 0:
        bot.send_message(message.chat.id, "❌ ставка должна быть больше 0")
        return

    if u["balance"] < bet:
        bot.send_message(message.chat.id, "❌ нет баланса")
        return

    u["balance"] -= bet
    u["games"] += 1

    msg = bot.send_message(message.chat.id, "🎰 Крутим рулетку...")

    for i in range(4):
        bot.edit_message_text("🎰 вращение " + "⚡"*i, message.chat.id, msg.message_id)
        time.sleep(0.5)

    win = random.random() < 0.35  # 35% шанс
    multiplier = random.randint(2, 1000000)

    if win:
        win_amount = bet * multiplier
        u["balance"] += win_amount
        u["wins"] += 1

        text = f"""
🎉 ВЫИГРЫШ!

💰 Ставка: {format_money(bet)}
🔥 x{multiplier}
💎 +{format_money(win_amount)} XTRA
"""
    else:
        text = f"💀 ПРОИГРЫШ\n💸 -{format_money(bet)} XTRA"

    save()
    bot.edit_message_text(text, message.chat.id, msg.message_id)

# ===================== PROFILE =====================
@bot.message_handler(commands=['profile'])
def profile(message):
    u = get_user(message.from_user.id)

    bot.send_message(message.chat.id, f"""
👤 PROFILE XTRA ELITA

💰 Баланс: {format_money(u['balance'])}
🎮 Игры: {u['games']}
🏆 Победы: {u['wins']}
⚡ Фарм: 15 сек

{'👑 VIP' if u['balance'] > 50000 else '👤 PLAYER'}
""")

# ===================== TOP =====================
@bot.message_handler(commands=['top'])
def top(message):
    sorted_users = sorted(data.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]

    text = "🏆 TOP XTRA ELITA\n\n"

    for i, (uid, u) in enumerate(sorted_users):
        text += f"{i+1}. {uid} — {format_money(u['balance'])}\n"

    bot.send_message(message.chat.id, text)

# ===================== RUN =====================
print("XTRA ELITA RUNNING...")
bot.infinity_polling(skip_pending=True)

import os
import json
import time
import random
from flask import Flask, request
import telebot

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}" if RENDER_URL else None

DATA_FILE = "data.json"
ADMIN_USERNAME = "xtra_beluga"

# ================= DATA =================
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "last_xp": {}, "daily": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

data = load_data()

# ================= UTIL =================
def get_user(user):
    uid = str(user.id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "balance": 0,
            "xp": 0,
            "level": 1,
            "crystals": 0,
            "inventory": {"bronze": 0, "elite": 0, "xtra": 0}
        }
    return data["users"][uid]

def level_from_xp(xp):
    lvl = 1
    while xp >= lvl * lvl * 100:
        lvl += 1
    return lvl

def is_admin(user):
    return user.username == ADMIN_USERNAME

def name(user):
    return user.username or user.first_name

# ================= KEYBOARD =================
def main_kb(user):
    kb = telebot.types.InlineKeyboardMarkup()

    kb.row(
        telebot.types.InlineKeyboardButton("💼 Work", callback_data="work"),
        telebot.types.InlineKeyboardButton("🎰 Casino", callback_data="casino")
    )

    kb.row(
        telebot.types.InlineKeyboardButton("🎁 Cases", callback_data="cases"),
        telebot.types.InlineKeyboardButton("🎒 Inventory", callback_data="inventory")
    )

    kb.row(
        telebot.types.InlineKeyboardButton("👤 Profile", callback_data="profile"),
        telebot.types.InlineKeyboardButton("🏆 Top", callback_data="top")
    )

    if is_admin(user):
        kb.row(telebot.types.InlineKeyboardButton("⚙ Admin", callback_data="admin"))

    return kb

# ================= XP =================
def give_xp(user):
    uid = str(user.id)
    now = time.time()

    if now - data["last_xp"].get(uid, 0) < 30:
        return

    if random.random() > 0.3:
        return

    u = get_user(user)
    u["xp"] += random.randint(1, 3)
    u["level"] = level_from_xp(u["xp"])
    data["last_xp"][uid] = now

# ================= START =================
@bot.message_handler(commands=["start"])
def start(message):
    u = get_user(message.from_user)
    save_data(data)

    bot.send_message(
        message.chat.id,
        f"⚡ XTRA ELITA PRO\n\n👤 {name(message.from_user)}\n💰 {u['balance']}\n⭐ {u['xp']}\n🏆 Lv {u['level']}",
        reply_markup=main_kb(message.from_user)
    )

# ================= COMMANDS =================
@bot.message_handler(commands=["balance"])
def balance(m):
    u = get_user(m.from_user)
    bot.send_message(m.chat.id, f"💰 {u['balance']}")

@bot.message_handler(commands=["xp"])
def xp(m):
    u = get_user(m.from_user)
    bot.send_message(m.chat.id, f"⭐ {u['xp']}")

@bot.message_handler(commands=["level"])
def level(m):
    u = get_user(m.from_user)
    bot.send_message(m.chat.id, f"🏆 {u['level']}")

@bot.message_handler(commands=["inventory"])
def inventory(m):
    u = get_user(m.from_user)
    inv = u["inventory"]

    bot.send_message(m.chat.id,
        f"🎒 INVENTORY\n"
        f"🥉 Bronze: {inv['bronze']}\n"
        f"💎 Elite: {inv['elite']}\n"
        f"⚡ XTRA: {inv['xtra']}"
    )

@bot.message_handler(commands=["help"])
def help_cmd(m):
    bot.send_message(m.chat.id,
        "/balance\n/xp\n/level\n/inventory\n/daily\n/work\n/casino"
    )

@bot.message_handler(commands=["daily"])
def daily(m):
    uid = str(m.from_user.id)
    now = time.time()

    if now - data["daily"].get(uid, 0) < 86400:
        bot.send_message(m.chat.id, "⏳ already claimed")
        return

    u = get_user(m.from_user)
    reward = random.randint(50, 200)
    u["balance"] += reward

    data["daily"][uid] = now
    bot.send_message(m.chat.id, f"🎁 +{reward}")

# ================= CALLBACKS =================
@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    u = get_user(call.from_user)

    if call.data == "work":
        gain = random.randint(10, 150)
        u["balance"] += gain
        bot.answer_callback_query(call.id, f"+{gain}")

    elif call.data == "casino":
        if u["balance"] < 50:
            bot.answer_callback_query(call.id, "No money")
            return

        u["balance"] -= 50

        if random.random() < 0.4:
            win = 150
            u["balance"] += win
            bot.answer_callback_query(call.id, f"WIN +{win}")
        else:
            bot.answer_callback_query(call.id, "LOSE")

    elif call.data == "cases":
        bot.send_message(call.message.chat.id,
            "🎁 CASES\n🥉 /open_bronze\n💎 /open_elite\n⚡ /open_xtra"
        )

    elif call.data == "inventory":
        inv = u["inventory"]
        bot.send_message(call.message.chat.id,
            f"🎒 INVENTORY\n🥉 {inv['bronze']}\n💎 {inv['elite']}\n⚡ {inv['xtra']}"
        )

    elif call.data == "profile":
        bot.send_message(call.message.chat.id,
            f"👤 {name(call.from_user)}\n💰 {u['balance']}\n⭐ {u['xp']}\n🏆 {u['level']}"
        )

    elif call.data == "top":
        top = sorted(data["users"].items(), key=lambda x: x[1]["balance"], reverse=True)[:5]
        txt = "🏆 TOP\n"
        for i,(uid,d) in enumerate(top):
            txt += f"{i+1}. {d['balance']}\n"
        bot.send_message(call.message.chat.id, txt)

    elif call.data == "admin" and is_admin(call.from_user):
        bot.send_message(call.message.chat.id, "⚙ ADMIN OK")

    save_data(data)

# ================= WEBHOOK =================
@app.route(WEBHOOK_PATH, methods=["POST"])
def hook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK"

@app.route("/")
def home():
    return "BOT OK"

# ================= RUN =================
if __name__ == "__main__":
    if WEBHOOK_URL:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(WEBHOOK_URL)

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

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
        return {"users": {}, "last_xp": {}}
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
            "crystals": 0,
            "messages": 0,
            "level": 1,
            "cases": 0
        }
    return data["users"][uid]
def level_from_xp(xp):
    level = 1
    while xp >= level * level * 100:
        level += 1
    return level
def username(user):
    return user.username or user.first_name
def is_admin(user):
    return user.username == ADMIN_USERNAME
# ================= KEYBOARDS =================
def main_kb():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(
        telebot.types.InlineKeyboardButton("💼 Работа", callback_data="work"),
        telebot.types.InlineKeyboardButton("🎰 Казино", callback_data="casino")
    )
    kb.row(
        telebot.types.InlineKeyboardButton("🎁 Кейсы", callback_data="cases"),
        telebot.types.InlineKeyboardButton("🛒 Магазин", callback_data="shop")
    )
    kb.row(
        telebot.types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        telebot.types.InlineKeyboardButton("🏆 Топ", callback_data="top")
    )
    if is_admin:
        kb.row(telebot.types.InlineKeyboardButton("⚙️ Админ", callback_data="admin"))
    return kb
def admin_kb():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(
        telebot.types.InlineKeyboardButton("+1000💰", callback_data="adm_money"),
        telebot.types.InlineKeyboardButton("+500⭐", callback_data="adm_xp")
    )
    kb.row(
        telebot.types.InlineKeyboardButton("🌀 Chaos", callback_data="adm_chaos"),
        telebot.types.InlineKeyboardButton("🤡 Troll", callback_data="adm_troll")
    )
    return kb
# ================= XP SYSTEM =================
def give_xp(user, amount):
    uid = str(user.id)
    now = time.time()
    last = data["last_xp"].get(uid, 0)
    if now - last < 30:
        return
    if random.random() > 0.3:
        return
    data["last_xp"][uid] = now
    u = get_user(user)
    u["xp"] += amount
    u["level"] = level_from_xp(u["xp"])
# ================= COMMANDS =================
@bot.message_handler(commands=["start"])
def start(message):
    u = get_user(message.from_user)
    save_data(data)
    bot.send_message(
        message.chat.id,
        f"⚡ XTRA ELITA PRO\n\n👤 {username(message.from_user)}\n💰 Баланс: {u['balance']}\n⭐ XP: {u['xp']}\n🏆 Level: {u['level']}",
        reply_markup=main_kb()
    )
# ================= MESSAGE XP =================
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    u = get_user(message.from_user)
    u["messages"] += 1
    if len(message.text or "") > 20:
        give_xp(message.from_user, random.randint(1, 3))
    save_data(data)
# ================= CALLBACKS =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user = call.from_user
    u = get_user(user)
    # WORK
    if call.data == "work":
        r = random.random()
        if r < 0.5:
            gain = random.randint(10, 20)
        elif r < 0.8:
            gain = random.randint(20, 40)
        elif r < 0.95:
            gain = random.randint(40, 60)
        else:
            gain = random.randint(100, 150)
        u["balance"] += gain
        bot.answer_callback_query(call.id, f"+{gain}💰")
    # CASINO
    elif call.data == "casino":
        if u["balance"] < 50:
            bot.answer_callback_query(call.id, "Нет денег")
            return
        bet = 50
        u["balance"] -= bet
        if random.random() < 0.4:
            win = 150
            u["balance"] += win
            give_xp(user, 2)
            bot.answer_callback_query(call.id, f"WIN +{win}")
        else:
            bot.answer_callback_query(call.id, "LOSE")
    # PROFILE
    elif call.data == "profile":
        bot.edit_message_text(
            f"👤 PROFILE\n\n"
            f"User: {username(user)}\n"
            f"💰 {u['balance']}\n"
            f"⭐ {u['xp']}\n"
            f"🏆 Level {u['level']}\n"
            f"💎 Crystals {u['crystals']}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_kb()
        )
    # TOP
    elif call.data == "top":
        top = sorted(data["users"].items(), key=lambda x: x[1]["balance"], reverse=True)[:5]
        text = "🏆 TOP PLAYERS\n\n"
        for i, (uid, d) in enumerate(top):
            text += f"{i+1}. 💰 {d['balance']}\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_kb())
    # ADMIN
    elif call.data == "admin" and is_admin(user):
        bot.edit_message_text("⚙️ ADMIN PANEL", call.message.chat.id, call.message.message_id, reply_markup=admin_kb())
    # ADMIN ACTIONS
    elif call.data == "adm_money" and is_admin(user):
        u["balance"] += 1000
        bot.answer_callback_query(call.id, "+1000")
    elif call.data == "adm_xp" and is_admin(user):
        u["xp"] += 500
        u["level"] = level_from_xp(u["xp"])
        bot.answer_callback_query(call.id, "+500 XP")
    elif call.data == "adm_chaos" and is_admin(user):
        for uid in data["users"]:
            data["users"][uid]["balance"] = random.randint(0, 10000)
        bot.answer_callback_query(call.id, "CHAOS DONE")
    elif call.data == "adm_troll" and is_admin(user):
        bot.send_message(call.message.chat.id, "🤡 Troll Mode activated")
    save_data(data)
# ================= FLASK WEBHOOK =================
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200
@app.route("/")
def index():
    return "XTRA ELITA BOT RUNNING"
# ================= START =================
if __name__ == "__main__":
    if WEBHOOK_URL:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
``

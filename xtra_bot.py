import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import time
import random

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ================= UI =================

def panel(title, text):
    return (
        "━━━━━━━━━━━━━━\n"
        f"🔥 {title} 🔥\n"
        "━━━━━━━━━━━━━━\n"
        f"{text}\n"
        "━━━━━━━━━━━━━━"
    )

# ================= DATA =================

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "users": {},
        "xp": {},
        "messages": {},
        "daily": {},
        "cooldowns": {}
    }

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

users = data["users"]
xp = data["xp"]
messages = data["messages"]
daily = data["daily"]
cd = data["cooldowns"]

# ================= SETTINGS =================

WORK_CD = 60
CASINO_CD = 60

# ================= HELPERS =================

def autosave():
    save_data()

def level(uid):
    xp.setdefault(uid, 0)
    return xp[uid] // 100

def add_xp(uid, amount):
    xp.setdefault(uid, 0)
    xp[uid] += amount
    autosave()

def add_money(uid, amount):
    users.setdefault(uid, 0)
    users[uid] += amount
    autosave()

def check_cd(uid, action, cd_time):
    now = time.time()
    cd.setdefault(uid, {})
    last = cd[uid].get(action, 0)

    if now - last < cd_time:
        return False, int(cd_time - (now - last))

    cd[uid][action] = now
    autosave()
    return True, 0

# ================= KEYBOARDS =================

def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🎮 Игры", callback_data="games"),
        InlineKeyboardButton("🛒 Магазин", callback_data="shop")
    )
    kb.add(
        InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        InlineKeyboardButton("🏆 Топы", callback_data="tops")
    )
    return kb

def games_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("💼 Работа", callback_data="work"),
        InlineKeyboardButton("🎰 Казино", callback_data="casino")
    )
    return kb

def shop_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🥉 Bronze 50", callback_data="buy_bronze"),
        InlineKeyboardButton("🥈 Elite 100", callback_data="buy_elite")
    )
    kb.add(
        InlineKeyboardButton("💎 XTRA 200", callback_data="buy_xtra")
    )
    return kb

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)

    users.setdefault(uid, 0)
    xp.setdefault(uid, 0)
    messages.setdefault(uid, 0)

    bot.send_message(
        message.chat.id,
        panel(
            "XTRA | ELITA",
            "🎮 Добро пожаловать в игру!\nВыбери меню ниже 👇"
        ),
        reply_markup=main_menu()
    )

# ================= PROFILE =================

def profile_text(uid, name):
    return panel(
        "ПРОФИЛЬ ИГРОКА",
        f"👤 {name}\n"
        f"⭐ Level: {level(uid)}\n"
        f"📈 XP: {xp[uid]}\n"
        f"💰 Coins: {users[uid]}\n"
        f"💬 Messages: {messages[uid]}"
    )

# ================= CALLBACK =================

@bot.callback_query_handler(func=lambda call: True)
def call_handler(call):
    uid = str(call.from_user.id)

    users.setdefault(uid, 0)
    xp.setdefault(uid, 0)
    messages.setdefault(uid, 0)

    # PROFILE
    if call.data == "profile":
        bot.edit_message_text(
            profile_text(uid, call.from_user.first_name),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu()
        )

    # TOPS
    if call.data == "tops":
        top_bal = sorted(users.items(), key=lambda x: x[1], reverse=True)[:5]
        top_msg = sorted(messages.items(), key=lambda x: x[1], reverse=True)[:5]

        text = "🏆 ТОПЫ:\n\n💰 Баланс:\n"
        for i, (u, v) in enumerate(top_bal, 1):
            text += f"{i}. {u} — {v}\n"

        text += "\n💬 Сообщения:\n"
        for i, (u, v) in enumerate(top_msg, 1):
            text += f"{i}. {u} — {v}\n"

        bot.send_message(call.message.chat.id, panel("ТОП", text))

    # MENU
    if call.data == "games":
        bot.send_message(call.message.chat.id, "🎮 Игры:", reply_markup=games_menu())

    if call.data == "shop":
        bot.send_message(call.message.chat.id, "🛒 Магазин:", reply_markup=shop_menu())

    # WORK
    if call.data == "work":
        ok, wait = check_cd(uid, "work", WORK_CD)
        if not ok:
            return bot.answer_callback_query(call.id, f"⏳ {wait} сек")

        jobs = [("⛏ Шахтёр", 50), ("💻 Программист", 120), ("🚕 Таксист", 60)]
        job, reward = random.choice(jobs)

        add_money(uid, reward)
        add_xp(uid, 20)

        bot.send_message(call.message.chat.id,
            panel("РАБОТА", f"{job}\n💰 +{reward}"))

    # CASINO
    if call.data == "casino":
        ok, wait = check_cd(uid, "casino", CASINO_CD)
        if not ok:
            return bot.answer_callback_query(call.id, f"⏳ {wait} сек")

        if users[uid] < 50:
            return bot.send_message(call.message.chat.id,
                panel("CASINO", "❌ нужно 50"))

        users[uid] -= 50

        a = random.randint(1, 5)
        b = random.randint(1, 5)

        if a == b:
            users[uid] += 150
            result = "🎉 WIN +150"
        else:
            result = "💀 LOSE"

        add_xp(uid, 10)

        bot.send_message(call.message.chat.id,
            panel("CASINO", f"{a} | {b}\n{result}"))

    # SHOP BUY
    if call.data.startswith("buy_"):
        case = call.data.split("_")[1]

        prices = {"bronze": 50, "elite": 100, "xtra": 200}

        if users[uid] < prices[case]:
            return bot.send_message(call.message.chat.id,
                panel("SHOP", "❌ нет денег"))

        users[uid] -= prices[case]
        autosave()

        bot.send_message(call.message.chat.id,
            panel("ПОКУПКА", f"{case.upper()} куплен"))
            
# ================= XP + MESSAGE SYSTEM =================

@bot.message_handler(func=lambda m: True)
def chat_xp(message):
    uid = str(message.from_user.id)

    users.setdefault(uid, 0)
    xp.setdefault(uid, 0)
    messages.setdefault(uid, 0)

    # count messages
    messages[uid] += 1

    # XP ONLY from chat
    xp[uid] += 1

    autosave()

# ================= RUN =================

print("🔥 XTRA | ELITA CLEAN BOT RUNNING...")
bot.infinity_polling(skip_pending=True)

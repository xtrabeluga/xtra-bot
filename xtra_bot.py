import telebot
import time
import json
import random
import os

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ================= ADMIN =================
ADMIN_USERNAME = "xtra_beluga"


def is_admin(user):
    return user.username == ADMIN_USERNAME


# ================= SAFE DATA =================
def default_data():
    return {
        "users": {},
        "xp": {},
        "messages": {},
        "cases": {},
        "last_xp": {}
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        return default_data()

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return default_data()


def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except:
        pass


data = load_data()


# ================= LEVELS =================
LEVEL_NAMES = [
    "Новичок", "Игрок", "Опытный",
    "Профи", "Элитный", "Легенда", "БОГ XTRA"
]


def get_level(xp):
    lvl = xp // 100
    return LEVEL_NAMES[min(lvl, len(LEVEL_NAMES) - 1)], lvl


# ================= STYLE =================
def panel(title, text):
    return f"""🔥 {title} 🔥

{text}

━━━━━━━━━━━━━━━
⚡ XTRA | ELITA
"""


# ================= USER =================
def get_user(user):
    uid = str(user.id)

    if uid not in data["users"]:
        data["users"][uid] = 100
        data["xp"][uid] = 0
        data["messages"][uid] = 0
        data["cases"][uid] = []
        data["last_xp"][uid] = 0

    return uid


def name(user):
    return f"@{user.username}" if user.username else user.first_name


# ================= XP ANTI-SPAM =================
@bot.message_handler(func=lambda m: True)
def xp_system(message):
    if not message.from_user:
        return

    uid = get_user(message.from_user)

    now = time.time()
    last = data["last_xp"].get(uid, 0)

    if now - last < 10:
        return

    data["xp"][uid] += 1
    data["messages"][uid] += 1
    data["last_xp"][uid] = now

    save_data()


# ================= CASE OPEN (NO FREEZE VERSION) =================
def open_case_result(chat_id, message_id, case, uid):
    rewards = {
        "bronze": (50, 120),
        "elite": (100, 250),
        "xtra": (200, 500)
    }

    reward = random.randint(*rewards.get(case, (50, 100)))

    data["users"][uid] += reward
    data["xp"][uid] += 10
    save_data()

    bot.edit_message_text(
        f"🎉 Кейс открыт!\n💰 +{reward} монет",
        chat_id,
        message_id
    )


def open_case_animation(chat_id, case, uid):
    msg = bot.send_message(chat_id, "🎁 Открытие кейса...")

    frames = [
        "🎁 ▓░░░░░░░░ 10%",
        "🎁 ▓▓▓░░░░░░ 30%",
        "🎁 ▓▓▓▓▓░░░░ 60%",
        "🎁 ▓▓▓▓▓▓▓░░ 90%",
        "💥 ЛОТЕРЕЯ ЗАПУЩЕНА..."
    ]

    for f in frames:
        try:
            bot.edit_message_text(f, chat_id, msg.message_id)
            time.sleep(0.5)
        except:
            pass

    open_case_result(chat_id, msg.message_id, case, uid)


# ================= MAIN MENU =================
def main_menu(user):
    kb = telebot.types.InlineKeyboardMarkup()

    kb.add(
        telebot.types.InlineKeyboardButton("🎮 Игры", callback_data="games"),
        telebot.types.InlineKeyboardButton("🛒 Магазин", callback_data="shop")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        telebot.types.InlineKeyboardButton("🏆 Топы", callback_data="tops")
    )

    if is_admin(user):
        kb.add(telebot.types.InlineKeyboardButton("👑 ADMIN", callback_data="admin"))

    return kb


def games_menu():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(
        telebot.types.InlineKeyboardButton("💼 Работа", callback_data="work"),
        telebot.types.InlineKeyboardButton("🎰 Казино", callback_data="casino")
    )
    kb.add(telebot.types.InlineKeyboardButton("⬅ Назад", callback_data="back"))
    return kb


def shop_menu():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(
        telebot.types.InlineKeyboardButton("🥉 Bronze", callback_data="buy_bronze"),
        telebot.types.InlineKeyboardButton("🥈 Elite", callback_data="buy_elite"),
    )
    kb.add(
        telebot.types.InlineKeyboardButton("💎 XTRA", callback_data="buy_xtra")
    )
    kb.add(telebot.types.InlineKeyboardButton("⬅ Назад", callback_data="back"))
    return kb


def admin_panel():
    kb = telebot.types.InlineKeyboardMarkup()

    kb.add(
        telebot.types.InlineKeyboardButton("💰 +1000", callback_data="adm_money"),
        telebot.types.InlineKeyboardButton("⭐ +500 XP", callback_data="adm_xp")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("💀 RANDOM CHAOS", callback_data="adm_chaos"),
        telebot.types.InlineKeyboardButton("😂 TROLL MODE", callback_data="adm_troll")
    )
    kb.add(telebot.types.InlineKeyboardButton("⬅ назад", callback_data="back"))

    return kb


# ================= START =================
@bot.message_handler(commands=["start"])
def start(message):
    get_user(message.from_user)

    bot.send_message(
        message.chat.id,
        panel("XTRA | ELITA", "Добро пожаловать в PRO систему"),
        reply_markup=main_menu(message.from_user)
    )


# ================= OPEN CASE =================
@bot.message_handler(commands=["open_case"])
def open_case(message):
    uid = get_user(message.from_user)

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /open_case bronze|elite|xtra")
        return

    case = args[1]

    if case not in data["cases"][uid]:
        bot.reply_to(message, "❌ кейса нет")
        return

    data["cases"][uid].remove(case)
    save_data()

    open_case_animation(message.chat.id, case, uid)


# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    uid = get_user(call.from_user)

    if call.data == "back":
        bot.edit_message_text(panel("XTRA | ELITA", "Главное меню"),
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=main_menu(call.from_user))

    elif call.data == "profile":
        xp = data["xp"][uid]
        coins = data["users"][uid]
        msgs = data["messages"][uid]

        lvl_name, lvl = get_level(xp)

        text = f"""
👤 {name(call.from_user)}

💰 Баланс: {coins}
⭐ XP: {xp}
📊 Уровень: {lvl} ({lvl_name})
💬 Сообщений: {msgs}
"""

        bot.edit_message_text(panel("ПРОФИЛЬ", text),
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=main_menu(call.from_user))

    elif call.data == "admin":
        if not is_admin(call.from_user):
            bot.answer_callback_query(call.id, "⛔ нет доступа")
            return

        bot.edit_message_text(panel("👑 ADMIN PANEL", "добро пожаловать босс 😈"),
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=admin_panel())

    elif call.data == "adm_money":
        if is_admin(call.from_user):
            data["users"][uid] += 1000
            save_data()
            bot.answer_callback_query(call.id, "+1000 💰")

    elif call.data == "adm_xp":
        if is_admin(call.from_user):
            data["xp"][uid] += 500
            save_data()
            bot.answer_callback_query(call.id, "+500 XP")

    elif call.data == "adm_chaos":
        if is_admin(call.from_user):
            data["users"][uid] = random.randint(0, 9999)
            save_data()
            bot.answer_callback_query(call.id, "💀 chaos")

    elif call.data == "adm_troll":
        if is_admin(call.from_user):
            bot.answer_callback_query(call.id, "😂 ты теперь легенда")

    elif call.data == "work":
        reward = random.randint(40, 150)
        data["users"][uid] += reward
        data["xp"][uid] += 20
        save_data()
        bot.answer_callback_query(call.id, f"+{reward}")

    elif call.data == "casino":
        bet = 50

        if data["users"][uid] < bet:
            bot.answer_callback_query(call.id, "❌ нет денег")
            return

        data["users"][uid] -= bet

        if random.randint(1, 100) <= 45:
            win = 150
            data["users"][uid] += win
            data["xp"][uid] += 10
            bot.answer_callback_query(call.id, f"+{win} 🎉")
        else:
            bot.answer_callback_query(call.id, "💀 lose")

        save_data()


# ================= RUN =================
print("🔥 PRO XTRA BOT STARTED")
bot.infinity_polling(skip_pending=True)

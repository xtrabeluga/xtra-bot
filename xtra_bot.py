import telebot
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
        "daily": {},
        "clans": {},
        "user_clan": {},
        "farm_cd": {},
        "cooldowns": {}
    }

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

users = data["users"]
daily_cd = data["daily"]
clans = data["clans"]
user_clan = data["user_clan"]
farm_cd = data["farm_cd"]
cooldowns = data["cooldowns"]

# ================= SETTINGS =================

WORK_CD = 60
CASINO_CD = 60

# ================= HELPERS =================

def autosave():
    save_data()

def check_cd(uid, action, cd):
    now = time.time()
    cooldowns.setdefault(uid, {})
    last = cooldowns[uid].get(action, 0)

    if now - last < cd:
        return False, int(cd - (now - last))

    cooldowns[uid][action] = now
    autosave()
    return True, 0

def add_money(uid, amount):
    users.setdefault(uid, 0)
    users[uid] += amount
    autosave()

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        panel("XTRA | ELITA",
        "💰 /balance — баланс\n"
        "🎁 /daily — награда\n"
        "💼 /work — работа\n"
        "🎰 /casino — казино\n"
        "📦 /shop — кейсы\n"
        "🎮 /open_case\n\n"
        "🏆 Кланы\n⚡ Фарм монет\n🔥 Играй и зарабатывай"))

# ================= BALANCE =================

@bot.message_handler(commands=['balance'])
def balance(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    bot.send_message(message.chat.id,
        panel("ПРОФИЛЬ ИГРОКА",
        f"👤 {message.from_user.first_name}\n"
        f"💰 Баланс: {users[uid]} Coins"))

# ================= DAILY =================

@bot.message_handler(commands=['daily'])
def daily(message):
    uid = str(message.from_user.id)
    now = time.time()

    if uid in daily_cd and now - daily_cd[uid] < 86400:
        left = 86400 - (now - daily_cd[uid])
        return bot.send_message(message.chat.id,
            panel("DAILY REWARD",
            f"⏳ Уже забрал\nОсталось: {int(left//3600)} часов"))

    add_money(uid, 70)
    daily_cd[uid] = now
    autosave()

    bot.send_message(message.chat.id,
        panel("DAILY",
        "🎁 +70 Coins"))

# ================= WORK =================

@bot.message_handler(commands=['work'])
def work(message):
    uid = str(message.from_user.id)

    ok, wait = check_cd(uid, "work", WORK_CD)
    if not ok:
        return bot.send_message(message.chat.id,
            panel("WORK",
            f"⏳ Подожди {wait} сек"))

    jobs = [
        ("⛏ Шахтёр", 50),
        ("🚕 Таксист", 60),
        ("💻 Программист", 120),
        ("🚴 Курьер", 40),
        ("🔫 Бандит", 150)
    ]

    job, reward = random.choice(jobs)
    add_money(uid, reward)

    bot.send_message(message.chat.id,
        panel("РАБОТА",
        f"{job}\n💰 +{reward} Coins"))

# ================= CASINO =================

@bot.message_handler(commands=['casino'])
def casino(message):
    uid = str(message.from_user.id)

    ok, wait = check_cd(uid, "casino", CASINO_CD)
    if not ok:
        return bot.send_message(message.chat.id,
            panel("CASINO",
            f"⏳ {wait} сек"))

    if users.get(uid, 0) < 50:
        return bot.send_message(message.chat.id,
            panel("CASINO",
            "❌ Нужно 50 Coins"))

    users[uid] -= 50

    a = random.randint(1, 5)
    b = random.randint(1, 5)

    if a == b:
        users[uid] += 150
        result = "🎉 ВЫИГРАЛ +150"
    else:
        result = "💀 ПРОИГРАЛ"

    autosave()

    bot.send_message(message.chat.id,
        panel("CASINO",
        f"{a} | {b}\n{result}"))

# ================= SHOP =================

@bot.message_handler(commands=['shop'])
def shop(message):
    bot.send_message(message.chat.id,
        panel("МАГАЗИН КЕЙСОВ",
        "🥉 bronze — 50\n"
        "🥈 elite — 100\n"
        "💎 xtra — 200\n\n"
        "👉 /buy <name>"))

@bot.message_handler(commands=['buy'])
def buy(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    args = message.text.split()
    if len(args) < 2:
        return

    case = args[1]

    prices = {
        "bronze": 50,
        "elite": 100,
        "xtra": 200
    }

    if case not in prices:
        return

    if users[uid] < prices[case]:
        return bot.send_message(message.chat.id,
            panel("МАГАЗИН", "❌ Недостаточно монет"))

    users[uid] -= prices[case]
    autosave()

    bot.send_message(message.chat.id,
        panel("ПОКУПКА",
        f"{case.upper()} куплен!\n👉 /open_case {case}"))

# ================= OPEN CASE =================

@bot.message_handler(commands=['open_case'])
def open_case(message):
    uid = str(message.from_user.id)

    args = message.text.split()
    if len(args) < 2:
        return

    case = args[1]

    rewards = {
        "bronze": (20, 150),
        "elite": (80, 300),
        "xtra": (150, 700)
    }

    if case not in rewards:
        return

    reward = random.randint(*rewards[case])
    add_money(uid, reward)

    bot.send_message(message.chat.id,
        panel("ОТКРЫТИЕ КЕЙСА",
        f"📦 {case.upper()}\n💰 +{reward} Coins"))

# ================= FARM =================

@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def farm(message):
    uid = str(message.from_user.id)

    now = time.time()
    if uid in farm_cd and now - farm_cd[uid] < 14400:
        return

    farm_cd[uid] = now
    add_money(uid, 2)

# ================= RUN =================

print("🔥 XTRA | ELITA RUNNING...")
bot.infinity_polling(skip_pending=True)

import telebot
import os
import json
import time
import random

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ---------------- UI ----------------
BORDER = "━━━━━━━━━━━━━━"

def panel(title, text):
    return f"{BORDER}\n{title}\n{BORDER}\n{text}\n{BORDER}"

# ---------------- DATA ----------------

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
daily_cooldown = data["daily"]
clans = data["clans"]
user_clan = data["user_clan"]
farm_cd = data["farm_cd"]
cooldowns = data["cooldowns"]

def autosave():
    save_data()

# ---------------- HELPERS ----------------

def check_cd(uid, action, cd):
    now = time.time()

    cooldowns.setdefault(uid, {})

    last = cooldowns[uid].get(action, 0)

    if now - last < cd:
        return False, int(cd - (now - last))

    cooldowns[uid][action] = now
    autosave()
    return True, 0

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        panel("🔥 XTRA | ELITA",
              "/balance\n/daily\n/work\n/casino\n/case\n/shop\n\n🏆 Clans + Economy"))

# ---------------- BALANCE ----------------

@bot.message_handler(commands=['balance'])
def balance(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    bot.send_message(message.chat.id,
        panel("💰 BALANCE",
              f"👤 {message.from_user.first_name}\n💰 {users[uid]} Coins"))

# ---------------- DAILY ----------------

@bot.message_handler(commands=['daily'])
def daily(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    now = time.time()
    cooldown = 86400

    if uid in daily_cooldown and now - daily_cooldown[uid] < cooldown:
        left = cooldown - (now - daily_cooldown[uid])
        return bot.send_message(message.chat.id,
            panel("⏳ DAILY", f"Жди {int(left//3600)}ч"))

    users[uid] += 70
    daily_cooldown[uid] = now
    autosave()

    bot.send_message(message.chat.id,
        panel("🎁 DAILY", "+70 Coins"))

# ---------------- WORK ----------------

@bot.message_handler(commands=['work'])
def work(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    ok, wait = check_cd(uid, "work", 1800)

    if not ok:
        return bot.send_message(message.chat.id,
            panel("⏳ WORK", f"{wait//60} мин"))

    jobs = [
        ("шахтёр ⛏", 50),
        ("курьер 🚴", 40),
        ("программист 💻", 120),
        ("таксист 🚕", 60),
        ("бандит 🔫", 150)
    ]

    job, reward = random.choice(jobs)

    users[uid] += reward
    autosave()

    bot.send_message(message.chat.id,
        panel("💼 WORK", f"{job}\n+{reward} Coins"))

# ---------------- FARM ----------------

@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def farm(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    now = time.time()
    cooldown = 14400

    if uid in farm_cd and now - farm_cd[uid] < cooldown:
        return

    farm_cd[uid] = now
    users[uid] += 2
    autosave()

# ---------------- CASINO ----------------

@bot.message_handler(commands=['casino'])
def casino(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    ok, wait = check_cd(uid, "casino", 3600)

    if not ok:
        return bot.send_message(message.chat.id,
            panel("🎰 CASINO", f"{wait//60} мин"))

    if users[uid] < 50:
        return bot.send_message(message.chat.id,
            panel("❌ CASINO", "Нужно 50 Coins"))

    users[uid] -= 50

    a = random.randint(1, 5)
    b = random.randint(1, 5)

    if a == b:
        users[uid] += 150
        result = "🎉 WIN +150"
    else:
        result = "💀 LOSE"

    autosave()

    bot.send_message(message.chat.id,
        panel("🎰 CASINO", f"{a} | {b}\n{result}"))

# ---------------- CASE ----------------

@bot.message_handler(commands=['case'])
def case(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    ok, wait = check_cd(uid, "case", 7200)

    if not ok:
        return bot.send_message(message.chat.id,
            panel("📦 CASE", f"{wait//60} мин"))

    if users[uid] < 100:
        return bot.send_message(message.chat.id,
            panel("❌ CASE", "Нужно 100 Coins"))

    users[uid] -= 100

    reward = random.choice([0, 50, 100, 200, 500])
    users[uid] += reward

    autosave()

    bot.send_message(message.chat.id,
        panel("📦 CASE", f"+{reward} Coins"))

# ---------------- SHOP ----------------

@bot.message_handler(commands=['shop'])
def shop(message):
    bot.send_message(message.chat.id,
        panel("🛒 SHOP",
              "bronze / 50\nelite / 100\nxtra / 200"))

# ---------------- BUY ----------------

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
            panel("❌ SHOP", "Нет денег"))

    users[uid] -= prices[case]

    rewards = {
        "bronze": (20, 150),
        "elite": (80, 300),
        "xtra": (150, 700)
    }

    reward = random.randint(*rewards[case])
    users[uid] += reward

    autosave()

    bot.send_message(message.chat.id,
        panel("📦 OPENED",
              f"{case.upper()} +{reward}"))

# ---------------- CLANS ----------------

@bot.message_handler(commands=['create_clan'])
def create_clan(message):
    uid = str(message.from_user.id)
    name = message.text.replace("/create_clan", "").strip()

    if not name:
        return bot.send_message(message.chat.id,
            panel("❌ CLAN", "Напиши имя"))

    if name in clans:
        return bot.send_message(message.chat.id,
            panel("❌ CLAN", "Уже существует"))

    clans[name] = {"leader": uid, "members": [uid]}
    user_clan[uid] = name
    autosave()

    bot.send_message(message.chat.id,
        panel("🏆 CLAN", f"{name} создан"))

@bot.message_handler(commands=['join_clan'])
def join_clan(message):
    uid = str(message.from_user.id)
    name = message.text.replace("/join_clan", "").strip()

    if name not in clans:
        return bot.send_message(message.chat.id,
            panel("❌ CLAN", "Нет клана"))

    clans[name]["members"].append(uid)
    user_clan[uid] = name
    autosave()

    bot.send_message(message.chat.id,
        panel("🏆 CLAN", f"Ты в {name}"))

@bot.message_handler(commands=['my_clan'])
def my_clan(message):
    uid = str(message.from_user.id)

    if uid not in user_clan:
        return bot.send_message(message.chat.id,
            panel("❌ CLAN", "Нет клана"))

    name = user_clan[uid]

    bot.send_message(message.chat.id,
        panel("🏆 CLAN",
              f"{name}\n👥 {len(clans[name]['members'])} игроков"))

# ---------------- RUN ----------------

print("XTRA BOT RUNNING...")
bot.infinity_polling(skip_pending=True)

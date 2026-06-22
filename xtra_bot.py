import telebot
import os
import json
import time
import random

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ---------------- DATA ----------------

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "users": {},
        "daily": {},
        "clans": {},
        "user_clan": {}
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()
users = data["users"]
daily_cooldown = data["daily"]
clans = data["clans"]
user_clan = data["user_clan"]

def autosave():
    save_data({
        "users": users,
        "daily": daily_cooldown,
        "clans": clans,
        "user_clan": user_clan
    })

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
"""
🤖 XTRA | ELITA BOT

/start — старт
/help — команды
/balance — баланс
/daily — награда
/work — работа
/top — топ
/casino — казино
/case — кейсы
/create_clan NAME
/join_clan NAME
/my_clan
""")

# ---------------- HELP ----------------

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id,
"""
📌 Команды:

/balance
/daily
/work
/top
/casino
/case
/create_clan
/join_clan
/my_clan
""")

# ---------------- BALANCE ----------------

@bot.message_handler(commands=['balance'])
def balance(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)
    autosave()

    bot.send_message(message.chat.id, f"💰 Баланс: {users[uid]} Coins")

# ---------------- DAILY ----------------

@bot.message_handler(commands=['daily'])
def daily(message):
    uid = str(message.from_user.id)
    now = time.time()
    cooldown = 24 * 60 * 60

    users.setdefault(uid, 0)

    if uid in daily_cooldown:
        if now - daily_cooldown[uid] < cooldown:
            left = cooldown - (now - daily_cooldown[uid])
            h = int(left // 3600)
            m = int((left % 3600) // 60)

            return bot.send_message(message.chat.id,
                f"⏳ Жди {h}ч {m}м")

    reward = 100
    users[uid] += reward
    daily_cooldown[uid] = now
    autosave()

    bot.send_message(message.chat.id,
        f"🎁 +{reward} Coins!")

# ---------------- WORK + FARM ----------------

@bot.message_handler(commands=['work'])
def work(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    jobs = [
        ("шахтёр ⛏", 50),
        ("курьер 🚴", 40),
        ("программист 💻", 120),
        ("бандит 🔫", 150),
        ("таксист 🚕", 60)
    ]

    job, reward = random.choice(jobs)
    users[uid] += reward
    autosave()

    bot.send_message(message.chat.id,
        f"💼 {job}\n+{reward} Coins")

# 💬 FARM ZA SOOBSHENIYA
@bot.message_handler(func=lambda m: True)
def farm(message):
    uid = str(message.from_user.id)

    if message.text.startswith("/"):
        return

    users.setdefault(uid, 0)
    users[uid] += 2
    autosave()

# ---------------- TOP ----------------

@bot.message_handler(commands=['top'])
def top(message):
    if not users:
        return bot.send_message(message.chat.id, "Пусто")

    top_users = sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]

    text = "🏆 TOP:\n\n"
    for i, (uid, bal) in enumerate(top_users, 1):
        text += f"{i}. {uid} — {bal}\n"

    bot.send_message(message.chat.id, text)

# ---------------- CASINO ----------------

@bot.message_handler(commands=['casino'])
def casino(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    bet = 50
    if users[uid] < bet:
        return bot.send_message(message.chat.id, "❌ Нужно 50")

    win_num = random.randint(1, 5)
    guess = random.randint(1, 5)

    if win_num == guess:
        users[uid] += 150
        res = "WIN +150"
    else:
        users[uid] -= bet
        res = "LOSE -50"

    autosave()

    bot.send_message(message.chat.id,
        f"🎰 {win_num} | {guess}\n{res}")

# ---------------- CASES ----------------

@bot.message_handler(commands=['case'])
def case(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    if users[uid] < 50:
        return bot.send_message(message.chat.id, "❌ Нужно 50")

    users[uid] -= 50

    rewards = [0, 50, 100, 200, 500]
    reward = random.choice(rewards)

    users[uid] += reward
    autosave()

    bot.send_message(message.chat.id,
        f"🎁 Выпало +{reward}")

# ---------------- CLANS ----------------

@bot.message_handler(commands=['create_clan'])
def create_clan(message):
    uid = str(message.from_user.id)
    name = message.text.replace("/create_clan", "").strip()

    if not name:
        return bot.send_message(message.chat.id, "Напиши имя")

    if name in clans:
        return bot.send_message(message.chat.id, "❌ Уже есть")

    clans[name] = {"leader": uid, "members": [uid]}
    user_clan[uid] = name
    autosave()

    bot.send_message(message.chat.id, f"🏆 Клан {name} создан")

@bot.message_handler(commands=['join_clan'])
def join_clan(message):
    uid = str(message.from_user.id)
    name = message.text.replace("/join_clan", "").strip()

    if name not in clans:
        return bot.send_message(message.chat.id, "❌ Нет клана")

    clans[name]["members"].append(uid)
    user_clan[uid] = name
    autosave()

    bot.send_message(message.chat.id, f"✅ Ты в {name}")

@bot.message_handler(commands=['my_clan'])
def my_clan(message):
    uid = str(message.from_user.id)

    if uid not in user_clan:
        return bot.send_message(message.chat.id, "Ты без клана")

    name = user_clan[uid]
    count = len(clans[name]["members"])

    bot.send_message(message.chat.id,
        f"🏆 {name}\n👥 {count} игроков")

# ---------------- RUN ----------------

bot.infinity_polling(skip_pending=True)

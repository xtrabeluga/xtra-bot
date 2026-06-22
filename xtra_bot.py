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
        "user_clan": {},
        "farm_cd": {}
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

users = data["users"]
daily_cooldown = data["daily"]
clans = data["clans"]
user_clan = data["user_clan"]
farm_cd = data["farm_cd"]

def autosave():
    save_data({
        "users": users,
        "daily": daily_cooldown,
        "clans": clans,
        "user_clan": user_clan,
        "farm_cd": farm_cd
    })

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
"""
🔥 XTRA | ELITA BOT

💰 Экономика:
/daily — награда каждые 24h
/work — работа
/casino — казино
/case — кейсы
/balance — баланс

👥 Социальное:
/top — рейтинг игроков
/create_clan — создать клан
/join_clan — вступить
/my_clan — твой клан

⚡ Активность = деньги!
""")

# ---------------- BALANCE ----------------

@bot.message_handler(commands=['balance'])
def balance(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    bot.send_message(message.chat.id,
        f"💰 Баланс: {users[uid]} Coins")

# ---------------- DAILY ----------------

@bot.message_handler(commands=['daily'])
def daily(message):
    uid = str(message.from_user.id)
    now = time.time()

    users.setdefault(uid, 0)

    cooldown = 24 * 60 * 60

    if uid in daily_cooldown:
        left = cooldown - (now - daily_cooldown[uid])
        if left > 0:
            h = int(left // 3600)
            m = int((left % 3600) // 60)

            return bot.send_message(message.chat.id,
                f"⏳ Уже забрал daily\nПопробуй через {h}ч {m}м")

    users[uid] += 100
    daily_cooldown[uid] = now
    autosave()

    bot.send_message(message.chat.id,
        "🎁 +100 Coins (daily)")

# ---------------- WORK ----------------

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

# ---------------- FARM (FIXED + ANTI-SPAM) ----------------

@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def farm(message):
    uid = str(message.from_user.id)
    now = time.time()

    users.setdefault(uid, 0)

    cooldown = 4 * 60 * 60  # 4 часа

    if uid in farm_cd and now - farm_cd[uid] < cooldown:
        return

    farm_cd[uid] = now

    users[uid] += 2
    autosave()

# ---------------- TOP (CLEAN + NAMES) ----------------

@bot.message_handler(commands=['top'])
def top(message):
    if not users:
        return bot.send_message(message.chat.id, "Пока нет игроков")

    sorted_users = sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]

    text = "🏆 TOP XTRA PLAYERS\n\n"

    for i, (uid, bal) in enumerate(sorted_users, 1):
        try:
            user = bot.get_chat(uid)
            name = user.first_name
        except:
            name = f"User {uid}"

        text += f"{i}. {name} — {bal} 💰\n"

    bot.send_message(message.chat.id, text)

# ---------------- CASINO ----------------

@bot.message_handler(commands=['casino'])
def casino(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    if users[uid] < 50:
        return bot.send_message(message.chat.id, "❌ Нужно 50 Coins")

    win = random.randint(1, 5)
    guess = random.randint(1, 5)

    if win == guess:
        users[uid] += 150
        result = "🎰 WIN +150"
    else:
        users[uid] -= 50
        result = "💀 LOSE -50"

    autosave()

    bot.send_message(message.chat.id,
        f"🎰 {win} | {guess}\n{result}")

# ---------------- CASES ----------------

@bot.message_handler(commands=['case'])
def case(message):
    uid = str(message.from_user.id)
    users.setdefault(uid, 0)

    if users[uid] < 50:
        return bot.send_message(message.chat.id, "❌ Нужно 50 Coins")

    users[uid] -= 50

    reward = random.choice([0, 50, 100, 200, 500])
    users[uid] += reward

    autosave()

    bot.send_message(message.chat.id,
        f"🎁 Кейc\n+{reward} Coins")

# ---------------- CLANS ----------------

@bot.message_handler(commands=['create_clan'])
def create_clan(message):
    uid = str(message.from_user.id)
    name = message.text.replace("/create_clan", "").strip()

    if not name:
        return bot.send_message(message.chat.id, "Напиши: /create_clan NAME")

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
        return bot.send_message(message.chat.id, "❌ Ты без клана")

    name = user_clan[uid]

    bot.send_message(message.chat.id,
        f"🏆 Клан: {name}\n👥 {len(clans[name]['members'])} игроков")

# ---------------- RUN ----------------

bot.infinity_polling(skip_pending=True)

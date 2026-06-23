import os
import time
import json
import random
import telebot
from flask import Flask, request

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
RENDER_URL = os.getenv("RENDER_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FILE = "data.json"
ADMIN = "xtra_beluga"

# ================= LOAD =================
def load():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "last": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load()

# ================= UTILS =================
def uid(user):
    return str(user.id)

def is_admin(user):
    return user.username == ADMIN

def level(xp):
    return xp // 120 + 1

def cooldown(user_id, key, sec):
    now = time.time()
    last = data["last"].get(f"{user_id}_{key}", 0)
    if now - last < sec:
        return False
    data["last"][f"{user_id}_{key}"] = now
    return True

# ================= USER =================
def get_user(user):
    u = uid(user)

    if u not in data["users"]:
        data["users"][u] = {
            "name": user.username or user.first_name,
            "balance": 0,
            "xp": 0,
            "items": {"bronze": 0, "elite": 0, "xtra": 0}
        }

    return data["users"][u]

# ================= ECONOMY =================
def work():
    return random.randint(30, 250)

def casino(bal):
    if bal < 50:
        return None
    return random.randint(80, 300) if random.random() < 0.45 else -50

def daily():
    return random.randint(200, 500)

def case_reward(case):
    if case == "bronze":
        return random.randint(10, 120)
    if case == "elite":
        return random.randint(80, 350)
    if case == "xtra":
        return random.randint(250, 900)
    return 0

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    u = get_user(m.from_user)

    bot.send_message(m.chat.id,
        f"💎 XTRA ELITA ULTRA BOT\n\n"
        f"👤 {u['name']}\n"
        f"💰 Баланс: {u['balance']}\n"
        f"⭐ XP: {u['xp']}\n"
        f"🏆 Level: {level(u['xp'])}\n\n"
        f"📜 /help"
    )

# ================= HELP =================
@bot.message_handler(commands=["help"])
def help_cmd(m):
    bot.send_message(m.chat.id,
        "📜 XTRA ELITA КОМАНДЫ\n\n"
        "💰 /balance /work /daily /casino\n"
        "💸 /transfer id сумма\n"
        "🏆 /top /profile\n"
        "🎁 /open bronze|elite|xtra\n"
        "🎒 /inventory\n"
        "🧑‍⚖️ /admin"
    )

# ================= BALANCE =================
@bot.message_handler(commands=["balance"])
def balance(m):
    u = get_user(m.from_user)
    bot.send_message(m.chat.id, f"💰 {u['balance']}")

# ================= WORK =================
@bot.message_handler(commands=["work"])
def work_cmd(m):
    u = get_user(m.from_user)

    if not cooldown(uid(m.from_user), "work", 30):
        bot.send_message(m.chat.id, "⏳ подожди 30 секунд")
        return

    gain = work()
    u["balance"] += gain
    u["xp"] += 5

    save()
    bot.send_message(m.chat.id, f"💼 +{gain}")

# ================= CASINO =================
@bot.message_handler(commands=["casino"])
def casino_cmd(m):
    u = get_user(m.from_user)

    if not cooldown(uid(m.from_user), "casino", 20):
        bot.send_message(m.chat.id, "⏳ подожди")
        return

    res = casino(u["balance"])
    if res is None:
        bot.send_message(m.chat.id, "❌ мало денег")
        return

    u["balance"] += res
    u["xp"] += 3

    save()
    bot.send_message(m.chat.id, f"🎰 {res}")

# ================= DAILY =================
@bot.message_handler(commands=["daily"])
def daily_cmd(m):
    u = get_user(m.from_user)

    if not cooldown(uid(m.from_user), "daily", 86400):
        bot.send_message(m.chat.id, "⏳ уже забрал daily")
        return

    u["balance"] += daily()
    u["xp"] += 20

    save()
    bot.send_message(m.chat.id, "🎁 daily получен")

# ================= PROFILE =================
@bot.message_handler(commands=["profile"])
def profile(m):
    u = get_user(m.from_user)

    bot.send_message(m.chat.id,
        f"📜 ПРОФИЛЬ\n\n"
        f"👤 {u['name']}\n"
        f"💰 {u['balance']}\n"
        f"⭐ XP: {u['xp']}\n"
        f"🏆 Level: {level(u['xp'])}"
    )

# ================= INVENTORY =================
@bot.message_handler(commands=["inventory"])
def inv(m):
    u = get_user(m.from_user)

    bot.send_message(m.chat.id,
        f"🎒 ИНВЕНТАРЬ\n"
        f"🥉 Bronze: {u['items']['bronze']}\n"
        f"💎 Elite: {u['items']['elite']}\n"
        f"⚡ XTRA: {u['items']['xtra']}"
    )

# ================= CASES =================
@bot.message_handler(commands=["open"])
def open_case(m):
    args = m.text.split()

    if len(args) != 2:
        bot.send_message(m.chat.id, "open bronze|elite|xtra")
        return

    u = get_user(m.from_user)
    case = args[1]

    reward = case_reward(case)

    if case in u["items"]:
        u["items"][case] += 1

    u["balance"] += reward
    u["xp"] += 10

    save()
    bot.send_message(m.chat.id, f"🎁 {case}: +{reward}")

# ================= TOP =================
@bot.message_handler(commands=["top"])
def top(m):
    users = list(data["users"].values())
    users.sort(key=lambda x: x["balance"], reverse=True)

    text = "🏆 XTRA ELITA TOP\n\n"

    for i, u in enumerate(users[:10], 1):
        text += f"{i}. {u['name']} — {u['balance']}💰\n"

    bot.send_message(m.chat.id, text)

# ================= TRANSFER =================
@bot.message_handler(commands=["transfer"])
def transfer(m):
    args = m.text.split()

    if len(args) != 3:
        bot.send_message(m.chat.id, "/transfer id сумма")
        return

    to = args[1]
    amount = int(args[2])

    u = get_user(m.from_user)

    if u["balance"] < amount:
        bot.send_message(m.chat.id, "❌ нет денег")
        return

    if to not in data["users"]:
        bot.send_message(m.chat.id, "❌ игрок не найден")
        return

    u["balance"] -= amount
    data["users"][to]["balance"] += amount

    save()
    bot.send_message(m.chat.id, "💸 переведено")

# ================= ADMIN =================
@bot.message_handler(commands=["admin"])
def admin(m):
    if not is_admin(m.from_user):
        return

    bot.send_message(m.chat.id,
        "🧑‍⚖️ XTRA ELITA ADMIN\n"
        "/giveall /chaos"
    )

@bot.message_handler(commands=["giveall"])
def giveall(m):
    if not is_admin(m.from_user):
        return

    for u in data["users"].values():
        u["balance"] += 1000

    save()
    bot.send_message(m.chat.id, "🔥 всем +1000")

@bot.message_handler(commands=["chaos"])
def chaos(m):
    if not is_admin(m.from_user):
        return

    for u in data["users"].values():
        u["balance"] = random.randint(0, 10000)

    save()
    bot.send_message(m.chat.id, "🔥 CHAOS MODE")

# ================= WEBHOOK =================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK"

@app.route("/")
def home():
    return "XTRA ELITA ULTRA BOT RUNNING"

# ================= RUN =================
if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)

    bot.set_webhook(f"{RENDER_URL}/{TOKEN}")

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

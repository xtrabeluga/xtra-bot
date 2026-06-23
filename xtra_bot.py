import os
import time
import json
import random
import telebot
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
RENDER_URL = os.getenv("RENDER_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FILE = "data.json"

# ================= DATA =================
def load():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "last_daily": {}, "last_work": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load()

# ================= USER =================
def get_user(user):
    uid = str(user.id)

    if uid not in data["users"]:
        data["users"][uid] = {
            "name": user.username or user.first_name,
            "balance": 0,
            "xp": 0,
            "inventory": {"bronze": 0, "elite": 0, "xtra": 0}
        }

    return data["users"][uid]

def level(xp):
    return xp // 100 + 1

# ================= ECONOMY =================
def work():
    return random.randint(10, 200)

def casino(bal):
    if bal < 50:
        return None

    win = random.random() < 0.45
    if win:
        return random.randint(50, 300)
    else:
        return -50

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    u = get_user(m.from_user)

    bot.send_message(m.chat.id,
        f"💎 XTRA ECONOMY BOT\n\n"
        f"👤 {u['name']}\n"
        f"💰 Баланс: {u['balance']}\n"
        f"⭐ XP: {u['xp']}\n"
        f"🏆 Level: {level(u['xp'])}"
    )

# ================= BALANCE =================
@bot.message_handler(commands=["balance"])
def balance(m):
    u = get_user(m.from_user)
    bot.send_message(m.chat.id, f"💰 Баланс: {u['balance']}")

# ================= WORK =================
@bot.message_handler(commands=["work"])
def cmd_work(m):
    u = get_user(m.from_user)
    gain = work()

    u["balance"] += gain
    u["xp"] += 5

    save()
    bot.send_message(m.chat.id, f"💼 Ты заработал +{gain} 💰")

# ================= CASINO =================
@bot.message_handler(commands=["casino"])
def cmd_casino(m):
    u = get_user(m.from_user)

    res = casino(u["balance"])
    if res is None:
        bot.send_message(m.chat.id, "❌ Нужно минимум 50💰")
        return

    u["balance"] += res

    save()
    bot.send_message(m.chat.id, f"🎰 Результат: {res}")

# ================= DAILY =================
@bot.message_handler(commands=["daily"])
def daily(m):
    u = get_user(m.from_user)

    uid = str(m.from_user.id)
    last = data["last_daily"].get(uid, 0)

    if time.time() - last < 86400:
        bot.send_message(m.chat.id, "⏳ Уже забрал daily")
        return

    u["balance"] += 250
    u["xp"] += 20
    data["last_daily"][uid] = time.time()

    save()
    bot.send_message(m.chat.id, "🎁 Daily +250💰")

# ================= INVENTORY =================
@bot.message_handler(commands=["inventory"])
def inv(m):
    u = get_user(m.from_user)
    i = u["inventory"]

    bot.send_message(m.chat.id,
        f"🎒 Инвентарь:\n"
        f"🥉 Bronze: {i['bronze']}\n"
        f"💎 Elite: {i['elite']}\n"
        f"⚡ XTRA: {i['xtra']}"
    )

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

# ================= TOP =================
@bot.message_handler(commands=["top"])
def top(m):
    users = list(data["users"].values())
    users.sort(key=lambda x: x["balance"], reverse=True)

    text = "🏆 ТОП ИГРОКОВ\n\n"
    for i, u in enumerate(users[:10], 1):
        text += f"{i}. {u['name']} — {u['balance']}💰\n"

    bot.send_message(m.chat.id, text)

# ================= TRANSFER =================
@bot.message_handler(commands=["transfer"])
def transfer(m):
    args = m.text.split()

    if len(args) != 3:
        bot.send_message(m.chat.id, "Используй: /transfer id сумма")
        return

    to_id = args[1]
    amount = int(args[2])

    u = get_user(m.from_user)

    if u["balance"] < amount:
        bot.send_message(m.chat.id, "❌ нет денег")
        return

    if to_id not in data["users"]:
        bot.send_message(m.chat.id, "❌ игрок не найден")
        return

    u["balance"] -= amount
    data["users"][to_id]["balance"] += amount

    save()
    bot.send_message(m.chat.id, f"💸 переведено {amount}")

# ================= CASES =================
@bot.message_handler(commands=["open"])
def open_case(m):
    args = m.text.split()

    if len(args) != 2:
        bot.send_message(m.chat.id, "open bronze / elite / xtra")
        return

    case = args[1]
    u = get_user(m.from_user)

    if case == "bronze":
        reward = random.randint(10, 100)
        u["inventory"]["bronze"] += 1

    elif case == "elite":
        reward = random.randint(50, 300)
        u["inventory"]["elite"] += 1

    elif case == "xtra":
        reward = random.randint(200, 800)
        u["inventory"]["xtra"] += 1
    else:
        reward = 0

    u["balance"] += reward
    save()

    bot.send_message(m.chat.id, f"🎁 {case}: +{reward}")

# ================= WEBHOOK =================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK"

@app.route("/")
def home():
    return "XTRA ECONOMY BOT RUNNING"

# ================= RUN =================
if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)

    bot.set_webhook(f"{RENDER_URL}/{TOKEN}")

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

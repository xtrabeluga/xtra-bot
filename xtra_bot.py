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

# ================= LOAD =================
def load():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}}

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
            "hugs": 0,
            "kisses": 0,
            "slaps": 0,
            "roasts": 0,
            "loves": 0,
            "messages": 0,

            # 💍 MARriage
            "marriage": {
                "partner": "",
                "pending": ""
            },

            # 👪 FAMILY SYSTEM
            "family": {
                "spouse": "",
                "children": [],
                "family_id": "",
                "balance": 0
            }
        }

    return data["users"][uid]

def sender(m):
    return m.from_user.username or m.from_user.first_name

# ================= ANIMATION =================
def animate(chat_id, text_final):
    msg = bot.send_message(chat_id, "⏳ ...")
    time.sleep(0.3)
    bot.edit_message_text("⏳ ..", chat_id, msg.message_id)
    time.sleep(0.3)
    bot.edit_message_text("⏳ .", chat_id, msg.message_id)
    time.sleep(0.3)
    bot.edit_message_text(text_final, chat_id, msg.message_id)

# ================= RP =================
def action(m, key, templates):
    u = get_user(m.from_user)
    u[key] += 1
    u["messages"] += 1

    target = m.text.split()[1] if len(m.text.split()) > 1 else "кого-то"
    text = random.choice(templates).format(a=sender(m), b=target)

    save()
    animate(m.chat.id, text)

# ================= TEMPLATES =================
hugs = ["🤗 {a} обнял {b}", "🤍 {a} прижал {b}"]
kisses = ["💋 {a} поцеловал {b}", "💖 {a} нежно коснулся {b}"]
slaps = ["👋 {a} ударил {b}", "💥 {a} дал пощёчину {b}"]
roasts = ["🔥 {a} уничтожил {b}", "🤡 {a} подколол {b}"]

# ================= COMMANDS =================
@bot.message_handler(commands=["start"])
def start(m):
    u = get_user(m.from_user)

    bot.send_message(m.chat.id,
        f"💎 XTRA ELITA RP BOT\n\n"
        f"👤 {u['name']}\n"
        f"💬 сообщений: {u['messages']}\n\n"
        f"📜 /help"
    )

@bot.message_handler(commands=["help"])
def help_cmd(m):
    bot.send_message(m.chat.id,
        "📜 XTRA ELITA RP\n\n"
        "/hug @user\n/kiss @user\n/slap @user\n/roast @user\n/love @user\n/profile\n/stats\n\n"
        "💍 /marry @user\n💔 /divorce\n👶 /child name\n🏠 /family"
    )

# ================= RP ACTIONS =================
@bot.message_handler(commands=["hug"])
def hug(m): action(m, "hugs", hugs)

@bot.message_handler(commands=["kiss"])
def kiss(m): action(m, "kisses", kisses)

@bot.message_handler(commands=["slap"])
def slap(m): action(m, "slaps", slaps)

@bot.message_handler(commands=["roast"])
def roast(m): action(m, "roasts", roasts)

@bot.message_handler(commands=["love"])
def love(m):
    u = get_user(m.from_user)
    u["loves"] += 1
    u["messages"] += 1

    target = m.text.split()[1] if len(m.text.split()) > 1 else "кого-то"
    p = random.randint(0, 100)

    if p > 80:
        text = "💘 ИДЕАЛЬНАЯ ПАРА"
    elif p > 50:
        text = "💖 есть шанс"
    else:
        text = "💔 не судьба"

    save()
    animate(m.chat.id, f"{sender(m)} ❤️ {target}\n{text}\n{p}%")

# ================= 💍 MARRIAGE =================
@bot.message_handler(commands=["marry"])
def marry(m):
    u = get_user(m.from_user)
    target = m.text.split(maxsplit=1)

    if len(target) < 2:
        return bot.send_message(m.chat.id, "Используй /marry @user")

    u["marriage"]["pending"] = target[1]

    save()
    bot.send_message(m.chat.id,
        f"💍 {sender(m)} сделал предложение {target[1]}\n"
        f"👉 /accept"
    )

@bot.message_handler(commands=["accept"])
def accept(m):
    u = get_user(m.from_user)

    if not u["marriage"]["pending"]:
        return bot.send_message(m.chat.id, "❌ нет предложения")

    partner = u["marriage"]["pending"]
    family_id = str(random.randint(10000, 99999))

    u["marriage"]["partner"] = partner
    u["marriage"]["pending"] = ""

    u["family"]["spouse"] = partner
    u["family"]["family_id"] = family_id

    save()

    bot.send_message(m.chat.id,
        f"💍 БРАК ЗАКЛЮЧЁН!\n"
        f"❤️ {sender(m)} + {partner}\n"
        f"🏠 Family ID: {family_id}"
    )

@bot.message_handler(commands=["divorce"])
def divorce(m):
    u = get_user(m.from_user)

    u["marriage"]["partner"] = ""
    u["family"] = {
        "spouse": "",
        "children": [],
        "family_id": "",
        "balance": 0
    }

    save()
    bot.send_message(m.chat.id, "💔 семья распалась")

@bot.message_handler(commands=["child"])
def child(m):
    u = get_user(m.from_user)
    name = m.text.split(maxsplit=1)

    if len(name) < 2:
        return bot.send_message(m.chat.id, "Используй /child имя")

    u["family"]["children"].append(name[1])
    save()

    bot.send_message(m.chat.id, f"👶 родился ребёнок: {name[1]}")

@bot.message_handler(commands=["family"])
def family(m):
    u = get_user(m.from_user)

    bot.send_message(m.chat.id,
        f"🏠 FAMILY XTRA ELITA\n\n"
        f"💍 Партнёр: {u['family']['spouse']}\n"
        f"👶 Дети: {', '.join(u['family']['children']) or 'нет'}\n"
        f"🏠 ID: {u['family']['family_id']}\n"
        f"💰 Баланс: {u['family']['balance']}"
    )

# ================= PROFILE =================
@bot.message_handler(commands=["profile"])
def profile(m):
    u = get_user(m.from_user)

    total = u["hugs"] + u["kisses"] + u["slaps"] + u["roasts"] + u["loves"]

    bot.send_message(m.chat.id,
        f"👤 XTRA ELITA ПРОФИЛЬ\n\n"
        f"Имя: {u['name']}\n"
        f"💬 сообщений: {u['messages']}\n"
        f"📊 активность: {total}"
    )

# ================= STATS =================
@bot.message_handler(commands=["stats"])
def stats(m):
    users = list(data["users"].values())
    users.sort(key=lambda x: x["messages"], reverse=True)

    text = "📊 TOP XTRA ELITA\n\n"

    for i, u in enumerate(users[:5], 1):
        text += f"{i}. {u['name']} — {u['messages']}\n"

    bot.send_message(m.chat.id, text)

# ================= TRACK =================
@bot.message_handler(func=lambda m: True)
def track(m):
    u = get_user(m.from_user)
    u["messages"] += 1
    save()

# ================= WEBHOOK =================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK"

@app.route("/")
def home():
    return "XTRA ELITA BOT RUNNING"

# ================= RUN =================
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(f"{RENDER_URL}/{TOKEN}")

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

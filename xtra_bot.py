import os
import time
import json
import logging
import re
import telebot
from flask import Flask, request

# ================= LOG =================
logging.basicConfig(level=logging.INFO)

# ================= ENV =================
TOKEN = os.getenv("TOKEN")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")
PORT = int(os.getenv("PORT", 10000))

if not TOKEN:
    raise Exception("TOKEN not set")

# ================= REDIS =================
try:
    import redis
    REDIS_URL = os.getenv("REDIS_URL")
    r = redis.from_url(REDIS_URL) if REDIS_URL else None
except:
    r = None

# ================= DB =================
DB_FILE = "db.json"

def load_db():
    if os.path.exists(DB_FILE):
        return json.load(open(DB_FILE, "r", encoding="utf-8"))
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

db = load_db()

# ================= USER SYSTEM =================
def get_user(uid):
    uid = str(uid)

    if r:
        try:
            data = r.get(uid)
            if not data:
                return {}
            if isinstance(data, bytes):
                data = data.decode()
            return json.loads(data)
        except:
            return {}

    return db.get(uid, {})

def set_user(uid, data):
    uid = str(uid)

    if r:
        try:
            r.set(uid, json.dumps(data))
        except:
            pass
    else:
        db[uid] = data
        save_db(db)

# ================= BOT =================
bot = telebot.TeleBot(TOKEN, threaded=True, skip_pending=True)
app = Flask(__name__)

# ================= ANTI SPAM =================
spam = {}

def anti_spam(uid):
    now = time.time()
    if uid in spam and now - spam[uid] < 2:
        return False
    spam[uid] = now
    return True

# ================= XP SYSTEM =================
def add_xp(uid, amount=10):
    user = get_user(uid)
    user.setdefault("xp", 0)
    user.setdefault("lvl", 1)

    user["xp"] += amount

    if user["xp"] >= user["lvl"] * 100:
        user["xp"] = 0
        user["lvl"] += 1

    set_user(uid, user)

# ================= SAFE =================
def safe(fn):
    def wrapper(m):
        try:
            if not m or not m.from_user:
                return
            if not anti_spam(m.from_user.id):
                return
            add_xp(m.from_user.id)
            return fn(m)
        except Exception as e:
            logging.error(e)
    return wrapper

# ================= UI =================
def panel(title, text):
    return f"""
━━━━━━━━━━━━━━
🔥 {title}
━━━━━━━━━━━━━━
{text}
━━━━━━━━━━━━━━
"""

# ================= PROFILE =================
@bot.message_handler(commands=['start'])
@safe
def start(m):
    uid = str(m.from_user.id)
    user = get_user(uid)

    user.setdefault("money", 1000)
    user.setdefault("xp", 0)
    user.setdefault("lvl", 1)
    user.setdefault("inventory", [])
    user.setdefault("married", False)

    set_user(uid, user)

    bot.send_message(m.chat.id, panel("XTRA ELITA RP", "Добро пожаловать в RP мир!\n/help"))

# ================= HELP =================
@bot.message_handler(commands=['help'])
@safe
def help_cmd(m):
    bot.send_message(m.chat.id, panel("КОМАНДЫ",
"""
💰 /balance
⭐ /xp
👤 /profile
💍 /marry /divorce
🎒 /inventory
💸 /daily

💬 RP чат:
обнять @user
ударить @user
поцеловать @user
украсть @user
"""))

# ================= BALANCE =================
@bot.message_handler(commands=['balance'])
@safe
def balance(m):
    user = get_user(m.from_user.id)
    user.setdefault("money", 1000)
    set_user(m.from_user.id, user)
    bot.send_message(m.chat.id, f"💰 Баланс: {user['money']}")

# ================= XP =================
@bot.message_handler(commands=['xp'])
@safe
def xp(m):
    user = get_user(m.from_user.id)
    bot.send_message(m.chat.id, f"⭐ XP: {user.get('xp',0)} | LVL: {user.get('lvl',1)}")

# ================= PROFILE =================
@bot.message_handler(commands=['profile'])
@safe
def profile(m):
    user = get_user(m.from_user.id)
    bot.send_message(m.chat.id, panel("ПРОФИЛЬ",
        f"""
💰 Деньги: {user.get('money',1000)}
⭐ XP: {user.get('xp',0)}
📊 LVL: {user.get('lvl',1)}
💍 Брак: {'Да' if user.get('married') else 'Нет'}
🎒 Инвентарь: {len(user.get('inventory',[]))}
"""))

# ================= FAMILY =================
@bot.message_handler(commands=['marry'])
@safe
def marry(m):
    user = get_user(m.from_user.id)
    user["married"] = True
    set_user(m.from_user.id, user)
    bot.send_message(m.chat.id, "💍 Вы поженились!")

@bot.message_handler(commands=['divorce'])
@safe
def divorce(m):
    user = get_user(m.from_user.id)
    user["married"] = False
    set_user(m.from_user.id, user)
    bot.send_message(m.chat.id, "💔 Развод оформлен")

# ================= DAILY =================
@bot.message_handler(commands=['daily'])
@safe
def daily(m):
    user = get_user(m.from_user.id)
    user.setdefault("money", 1000)
    user["money"] += 200
    set_user(m.from_user.id, user)
    bot.send_message(m.chat.id, "🎁 +200 монет!")

# ================= INVENTORY =================
@bot.message_handler(commands=['inventory'])
@safe
def inv(m):
    user = get_user(m.from_user.id)
    inv = user.get("inventory", [])
    bot.send_message(m.chat.id, "🎒 Инвентарь:\n" + ("\n".join(inv) if inv else "пусто"))

# ================= RP CHAT =================
def extract_user(text):
    match = re.search(r'@(\w+)', text or "")
    return match.group(1) if match else None


@bot.message_handler(func=lambda m: True)
@safe
def rp_chat(m):
    if not m.text:
        return

    text = m.text.lower()
    user = m.from_user.first_name
    target = extract_user(m.text)

    if "обнять" in text:
        bot.reply_to(m, f"🤗 {user} обнял(а) @{target or 'кого-то'} 💞")

    elif "ударить" in text:
        bot.reply_to(m, f"👊 {user} ударил(а) @{target or 'кого-то'} 💥")

    elif "поцеловать" in text:
        bot.reply_to(m, f"💋 {user} поцеловал(а) @{target or 'кого-то'} ❤️")

    elif "украсть" in text:
        bot.reply_to(m, f"🕶 {user} попытался украсть у @{target or 'кого-то'} 😈")

    elif "пнуть" in text:
        bot.reply_to(m, f"🦵 {user} пнул(а) @{target or 'кого-то'} 😂")

# ================= WEBHOOK =================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode())
        bot.process_new_updates([update])
    except Exception as e:
        logging.error(e)
    return "OK"

def start_webhook():
    bot.remove_webhook()
    time.sleep(1)

    if BASE_URL:
        bot.set_webhook(url=f"{BASE_URL}/{TOKEN}")
        logging.info("Webhook OK")
    else:
        logging.warning("NO BASE URL")

# ================= RUN =================
if __name__ == "__main__":
    start_webhook()
    app.run(host="0.0.0.0", port=PORT)

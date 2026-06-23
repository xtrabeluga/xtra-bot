
import os, json, time, random
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL","")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FILE = "data.json"
ADMIN_USERNAME = "xtra_beluga"

LEVELS = ["Новичок","Игрок","Опытный","Профи","Элитный","Легенда","БОГ XTRA"]

def default_data():
    return {"users":{}, "xp":{}, "messages":{}, "cases":{}, "last_xp":{}, "names":{}}

def load():
    try:
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return default_data()

data = load()

def save():
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

def get_user(user):
    uid=str(user.id)
    data["users"].setdefault(uid,100)
    data["xp"].setdefault(uid,0)
    data["messages"].setdefault(uid,0)
    data["cases"].setdefault(uid,[])
    data["last_xp"].setdefault(uid,0)
    data["names"][uid]="@"+user.username if user.username else user.first_name
    return uid

def is_admin(user):
    return bool(user.username and user.username.lower()==ADMIN_USERNAME.lower())

def level_name(xp):
    lvl=xp//100
    return lvl, LEVELS[min(lvl,len(LEVELS)-1)]

def panel(t,x):
    return f"🔥 {t} 🔥\n\n{x}\n\n━━━━━━━━━━━━━━\n⚡ XTRA | ELITA"

def menu(user):
    kb=InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎮 Игры",callback_data="games"),
           InlineKeyboardButton("🛒 Магазин",callback_data="shop"))
    kb.add(InlineKeyboardButton("👤 Профиль",callback_data="profile"),
           InlineKeyboardButton("🏆 Топы",callback_data="tops"))
    if is_admin(user):
        kb.add(InlineKeyboardButton("👑 ADMIN",callback_data="admin"))
    return kb

@bot.message_handler(commands=["start"])
def start(m):
    get_user(m.from_user)
    save()
    bot.send_message(m.chat.id,panel("XTRA | ELITA","Добро пожаловать!"),reply_markup=menu(m.from_user))

@bot.message_handler(commands=["open_case"])
def open_case(m):
    uid=get_user(m.from_user)
    p=m.text.split()
    if len(p)<2:
        return bot.reply_to(m,"/open_case bronze|elite|xtra")
    case=p[1].lower()
    if case not in data["cases"][uid]:
        return bot.reply_to(m,"❌ Кейса нет")
    data["cases"][uid].remove(case)
    rewards={"bronze":(50,120),"elite":(100,250),"xtra":(200,500)}
    reward=random.randint(*rewards[case])
    data["users"][uid]+=reward
    data["xp"][uid]+=10
    save()
    bot.reply_to(m,f"🎁 Кейс открыт!\n💰 +{reward} монет")

@bot.message_handler(func=lambda m: True)
def xp_system(m):
    if m.text and m.text.startswith("/"):
        return
    uid=get_user(m.from_user)
    now=time.time()
    if now-data["last_xp"][uid] >= 10:
        data["xp"][uid]+=1
        data["messages"][uid]+=1
        data["last_xp"][uid]=now
        save()

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid=get_user(c.from_user)

    if c.data=="profile":
        lvl,name=level_name(data["xp"][uid])
        txt=f"👤 {data['names'][uid]}\n💰 {data['users'][uid]}\n⭐ {data['xp'][uid]}\n📊 {lvl} ({name})\n💬 {data['messages'][uid]}"
        return bot.edit_message_text(panel("ПРОФИЛЬ",txt),c.message.chat.id,c.message.message_id,reply_markup=menu(c.from_user))

    if c.data=="tops":
        top=sorted(data["users"].items(),key=lambda x:x[1],reverse=True)[:5]
        txt="\n".join([f"{i+1}. {data['names'].get(u,u)} — {v}" for i,(u,v) in enumerate(top)])
        return bot.edit_message_text(panel("ТОП БАЛАНС",txt),c.message.chat.id,c.message.message_id,reply_markup=menu(c.from_user))

    if c.data=="games":
        kb=InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("💼 Работа",callback_data="work"),
               InlineKeyboardButton("🎰 Казино",callback_data="casino"))
        return bot.send_message(c.message.chat.id,"🎮 Игры",reply_markup=kb)

    if c.data=="shop":
        kb=InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🥉 Bronze 50",callback_data="buy_bronze"))
        kb.add(InlineKeyboardButton("🥈 Elite 100",callback_data="buy_elite"))
        kb.add(InlineKeyboardButton("💎 XTRA 200",callback_data="buy_xtra"))
        return bot.send_message(c.message.chat.id,"🛒 Магазин",reply_markup=kb)

    if c.data=="work":
        reward=random.randint(40,150)
        data["users"][uid]+=reward
        data["xp"][uid]+=20
        save()
        return bot.answer_callback_query(c.id,f"+{reward} 💰")

    if c.data=="casino":
        if data["users"][uid] < 50:
            return bot.answer_callback_query(c.id,"Нет денег")
        data["users"][uid]-=50
        if random.randint(1,100)<=45:
            data["users"][uid]+=150
            data["xp"][uid]+=10
            save()
            return bot.answer_callback_query(c.id,"🎉 +150")
        save()
        return bot.answer_callback_query(c.id,"💀 Проигрыш")

    if c.data.startswith("buy_"):
        case=c.data.split("_")[1]
        prices={"bronze":50,"elite":100,"xtra":200}
        if data["users"][uid] < prices[case]:
            return bot.answer_callback_query(c.id,"Недостаточно монет")
        data["users"][uid]-=prices[case]
        data["cases"][uid].append(case)
        save()
        return bot.answer_callback_query(c.id,"🎁 Куплено")

    if c.data=="admin" and is_admin(c.from_user):
        kb=InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("💰 +1000",callback_data="adm_money"))
        kb.add(InlineKeyboardButton("⭐ +500 XP",callback_data="adm_xp"))
        return bot.send_message(c.message.chat.id,"👑 Админка",reply_markup=kb)

    if c.data=="adm_money" and is_admin(c.from_user):
        data["users"][uid]+=1000; save()
        return bot.answer_callback_query(c.id,"Выдано 1000")

    if c.data=="adm_xp" and is_admin(c.from_user):
        data["xp"][uid]+=500; save()
        return bot.answer_callback_query(c.id,"Выдано 500 XP")

@app.route("/")
def home():
    return "XTRA ELITA BOT ONLINE"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update=telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok"

if __name__ == "__main__":
    if TOKEN and RENDER_EXTERNAL_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))

# XTRA ELITA LITE
# Part 1/3
# pyTelegramBotAPI

import telebot
import json
import os
import time
from datetime import datetime

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise Exception("TOKEN environment variable not found!")

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"


# =========================
# DATABASE
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


data = load_data()


# =========================
# USER SYSTEM
# =========================

def create_user(user):
    uid = str(user.id)

    if uid not in data:
        data[uid] = {
            "id": user.id,
            "name": user.first_name,
			
            "balance": 1000,
			
            "farm_time": 0,
            "daily_time": 0,
			
            "inventory": [],
            "cases": 0,
			
            "wins": 0,
            "loses": 0
			
			"rep": 0
        }

        save_data(data)

        save_data(data)


def get_user(uid):
    uid = str(uid)

    if uid not in data:
        return None

    return data[uid]


# =========================
# DESIGN
# =========================

def panel(title, text):
    return (
        "━━━━━━━━━━━━━━━━━━\n"
        f"🔥 {title}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{text}\n"
        "━━━━━━━━━━━━━━━━━━"
    )


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    create_user(message.from_user)

    bot.reply_to(
        message,
        panel(
            "XTRA ELITA",
            f"Добро пожаловать, {message.from_user.first_name}!\n\n"
            "Напиши /help для списка команд."
        )
    )


# =========================
# HELP
# =========================

@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.reply_to(
        message,
        panel(
            "СПИСОК КОМАНД",
            "/profile - профиль\n"
            "/balance - баланс\n"
            "/daily - ежедневная награда\n"
            "/farm - заработать монеты\n"
            "/pay ID СУММА - перевод\n"
            "/top - топ игроков"
        )
    )


# =========================
# PROFILE
# =========================

@bot.message_handler(commands=["profile"])
def profile(message):
    create_user(message.from_user)

    user = get_user(message.from_user.id)

    text = (
        f"👤 Игрок: {user['name']}\n"
        f"💰 Баланс: {user['balance']} XTRA\n"
        f"📦 Предметов: {len(user['inventory'])}\n"
        f"🏆 Побед: {user['wins']}\n"
        f"❌ Поражений: {user['loses']}"
    )

    bot.reply_to(message, panel("ПРОФИЛЬ", text))


# =========================
# BALANCE
# =========================

@bot.message_handler(commands=["balance"])
def balance(message):
    create_user(message.from_user)

    user = get_user(message.from_user.id)

    bot.reply_to(
        message,
        panel(
            "БАЛАНС",
            f"У вас {user['balance']} XTRA"
        )
    )


# =========================
# DAILY
# =========================

@bot.message_handler(commands=["daily"])
def daily(message):
    create_user(message.from_user)

    uid = str(message.from_user.id)

    now = int(time.time())

    if now - data[uid]["daily_time"] < 86400:
        left = 86400 - (now - data[uid]["daily_time"])

        hours = left // 3600
        minutes = (left % 3600) // 60

        bot.reply_to(
            message,
            panel(
                "DAILY",
                f"Следующая награда через\n"
                f"{hours}ч {minutes}м"
            )
        )
        return

    reward = 1000

    data[uid]["balance"] += reward
    data[uid]["daily_time"] = now

    save_data(data)

    bot.reply_to(
        message,
        panel(
            "DAILY",
            f"+{reward} XTRA"
        )
    )


# =========================
# FARM
# =========================

@bot.message_handler(commands=["farm"])
def farm(message):
    create_user(message.from_user)

    uid = str(message.from_user.id)

    now = int(time.time())

    if now - data[uid]["farm_time"] < 15:

        left = 15 - (now - data[uid]["farm_time"])

        bot.reply_to(
            message,
            panel(
                "ФАРМ",
                f"Подождите {left} сек."
            )
        )
        return

    import random

    reward = random.randint(50, 5000)

    data[uid]["balance"] += reward
    data[uid]["farm_time"] = now

    save_data(data)

    bot.reply_to(
        message,
        panel(
            "ФАРМ",
            f"Вы заработали {reward} XTRA"
        )
    )


# =========================
# PAY
# =========================

@bot.message_handler(commands=["pay"])
def pay(message):
    create_user(message.from_user)

    args = message.text.split()

    if len(args) != 3:
        bot.reply_to(
            message,
            "Использование:\n/pay ID СУММА"
        )
        return

    sender = str(message.from_user.id)
    target = args[1]

    try:
        amount = int(args[2])
    except:
        return

    if amount <= 0:
        return

    if target not in data:
        bot.reply_to(message, "Игрок не найден")
        return

    if data[sender]["balance"] < amount:
        bot.reply_to(message, "Недостаточно средств")
        return

    data[sender]["balance"] -= amount
    data[target]["balance"] += amount

    save_data(data)

    bot.reply_to(
        message,
        panel(
            "ПЕРЕВОД",
            f"Отправлено {amount} XTRA"
        )
    )


# =========================
# TOP
# =========================

@bot.message_handler(commands=["top"])
def top(message):
    players = sorted(
        data.values(),
        key=lambda x: x["balance"],
        reverse=True
    )

    text = ""

    place = 1

    for player in players[:10]:
        text += (
            f"{place}. {player['name']} — "
            f"{player['balance']} XTRA\n"
        )
        place += 1

    bot.reply_to(
        message,
        panel(
            "ТОП БОГАЧЕЙ",
            text if text else "Пусто"
        )
    )
    
print("XTRA ELITA запущен!")
    
# ==========================================
# PART 2 - CASINO / SHOP / CASES / INVENTORY
# ==========================================

import random

# ==========================================
# SHOP ITEMS
# ==========================================

SHOP_ITEMS = {
    "vip": {
        "name": "VIP Статус",
        "price": 5000
    },
    "m416": {
        "name": "M416 Glacier",
        "price": 15000
    },
    "xsuit": {
        "name": "X-SUIT",
        "price": 50000
    },
    "case": {
        "name": "Кейс",
        "price": 3000
    }
}

# ==========================================
# CASINO
# /casino 1000
# ==========================================

@bot.message_handler(commands=["casino"])
def casino(message):
    create_user(message.from_user)

    args = message.text.split()

    if len(args) != 2:
        bot.reply_to(
            message,
            panel(
                "КАЗИНО",
                "Использование:\n/casino СУММА"
            )
        )
        return

    uid = str(message.from_user.id)

    try:
        bet = int(args[1])
    except:
        bot.reply_to(message, "Введите число.")
        return

    if bet <= 0:
        return

    if data[uid]["balance"] < bet:
        bot.reply_to(
            message,
            panel(
                "КАЗИНО",
                "Недостаточно средств."
            )
        )
        return

    roll = random.randint(1, 100)

    if roll <= 45:
        data[uid]["balance"] -= bet
        data[uid]["loses"] += 1

        save_data(data)

        bot.reply_to(
            message,
            panel(
                "КАЗИНО",
                f"❌ Проигрыш\n\n"
                f"-{bet} XTRA"
            )
        )

    elif roll <= 85:
        win = bet * 2

        data[uid]["balance"] += bet
        data[uid]["wins"] += 1

        save_data(data)

        bot.reply_to(
            message,
            panel(
                "КАЗИНО",
                f"🎉 Победа!\n\n"
                f"+{bet} XTRA"
            )
        )

    else:
        jackpot = bet * 5

        data[uid]["balance"] += jackpot
        data[uid]["wins"] += 1

        save_data(data)

        bot.reply_to(
            message,
            panel(
                "ДЖЕКПОТ",
                f"💎 Вы сорвали джекпот!\n\n"
                f"+{jackpot} XTRA"
            )
        )


# ==========================================
# SHOP
# ==========================================

@bot.message_handler(commands=["shop"])
def shop(message):

    text = ""

    for item_id, item in SHOP_ITEMS.items():
        text += (
            f"📦 {item_id}\n"
            f"Название: {item['name']}\n"
            f"Цена: {item['price']} XTRA\n\n"
        )

    text += "\nПокупка:\n/buy ID"

    bot.reply_to(
        message,
        panel(
            "МАГАЗИН",
            text
        )
    )


# ==========================================
# BUY
# ==========================================

@bot.message_handler(commands=["buy"])
def buy(message):
    create_user(message.from_user)

    args = message.text.split()

    if len(args) != 2:
        bot.reply_to(message, "/buy ID")
        return

    uid = str(message.from_user.id)

    item_id = args[1].lower()

    if item_id not in SHOP_ITEMS:
        bot.reply_to(message, "Предмет не найден.")
        return

    item = SHOP_ITEMS[item_id]

    if data[uid]["balance"] < item["price"]:
        bot.reply_to(
            message,
            panel(
                "ПОКУПКА",
                "Недостаточно денег."
            )
        )
        return

    data[uid]["balance"] -= item["price"]

    if item_id == "case":
        data[uid]["cases"] += 1
    else:
        data[uid]["inventory"].append(item["name"])

    save_data(data)

    bot.reply_to(
        message,
        panel(
            "ПОКУПКА",
            f"Куплено:\n{item['name']}"
        )
    )


# ==========================================
# INVENTORY
# ==========================================

@bot.message_handler(commands=["inventory"])
def inventory(message):
    create_user(message.from_user)

    uid = str(message.from_user.id)

    inv = data[uid]["inventory"]

    if len(inv) == 0:
        bot.reply_to(
            message,
            panel(
                "ИНВЕНТАРЬ",
                "Пусто."
            )
        )
        return

    text = ""

    for i, item in enumerate(inv, start=1):
        text += f"{i}. {item}\n"

    bot.reply_to(
        message,
        panel(
            "ИНВЕНТАРЬ",
            text
        )
    )


# ==========================================
# MY CASES
# ==========================================

@bot.message_handler(commands=["cases"])
def cases(message):
    create_user(message.from_user)

    uid = str(message.from_user.id)

    bot.reply_to(
        message,
        panel(
            "КЕЙСЫ",
            f"У вас кейсов: {data[uid]['cases']}"
        )
    )


# ==========================================
# OPEN CASE
# ==========================================

@bot.message_handler(commands=["open"])
def open_case(message):
    create_user(message.from_user)

    uid = str(message.from_user.id)

    if data[uid]["cases"] <= 0:
        bot.reply_to(
            message,
            panel(
                "КЕЙС",
                "У вас нет кейсов."
            )
        )
        return

    data[uid]["cases"] -= 1

    rewards = [
        ("1000 XTRA", "money", 1000),
        ("5000 XTRA", "money", 5000),
        ("10000 XTRA", "money", 10000),
        ("VIP Статус", "item", "VIP Статус"),
        ("M416 Glacier", "item", "M416 Glacier"),
        ("X-SUIT", "item", "X-SUIT")
    ]

    reward = random.choice(rewards)

    if reward[1] == "money":
        data[uid]["balance"] += reward[2]

        text = (
            f"🎁 Выпало:\n"
            f"{reward[0]}"
        )

    else:
        data[uid]["inventory"].append(reward[2])

        text = (
            f"🎁 Выпал предмет:\n"
            f"{reward[2]}"
        )

    save_data(data)

    bot.reply_to(
        message,
        panel(
            "ОТКРЫТИЕ КЕЙСА",
            text
        )
    )


# ==========================================
# GIVE CASE (ADMIN)
# ==========================================

ADMINS = [
    8573898148
]

@bot.message_handler(commands=["givecase"])
def give_case(message):

    if message.from_user.id not in ADMINS:
        return

    args = message.text.split()

    if len(args) != 3:
        return

    target = args[1]

    try:
        amount = int(args[2])
    except:
        return

    if target not in data:
        return

    data[target]["cases"] += amount

    save_data(data)

    bot.reply_to(
        message,
        panel(
            "АДМИН",
            f"Выдано кейсов: {amount}"
        )
    )

# ==========================================
# PART 3 - CLAN / ADMIN / REP / MODERATION
# ==========================================

# ==========================================
# CLAN SYSTEM
# ==========================================

CLAN_NAME = "XTRA ELITA"

@bot.message_handler(commands=["clan"])
def clan_info(message):
    create_user(message.from_user)

    members = len(data)

    bot.reply_to(
        message,
        panel(
            "КЛАН",
            f"Название: {CLAN_NAME}\n"
            f"Участников в базе: {members}\n"
            f"Валюта: XTRA"
        )
    )


# ==========================================
# REP SYSTEM
# ==========================================

def ensure_rep(uid):
    if "rep" not in data[uid]:
        data[uid]["rep"] = 0


@bot.message_handler(commands=["rep"])
def rep(message):

    create_user(message.from_user)

    if not message.reply_to_message:
        bot.reply_to(
            message,
            "Ответьте на сообщение игрока."
        )
        return

    target = str(message.reply_to_message.from_user.id)

    if target not in data:
        create_user(message.reply_to_message.from_user)

    ensure_rep(target)

    data[target]["rep"] += 1

    save_data(data)

    bot.reply_to(
        message,
        panel(
            "РЕПУТАЦИЯ",
            f"+1 репутация игроку\n"
            f"Всего: {data[target]['rep']}"
        )
    )


# ==========================================
# MY REP
# ==========================================

@bot.message_handler(commands=["myrep"])
def my_rep(message):
    create_user(message.from_user)

    uid = str(message.from_user.id)

    ensure_rep(uid)

    bot.reply_to(
        message,
        panel(
            "РЕПУТАЦИЯ",
            f"У вас {data[uid]['rep']} репутации"
        )
    )


# ==========================================
# ADMIN ADD MONEY
# ==========================================

@bot.message_handler(commands=["addmoney"])
def add_money(message):

    if message.from_user.id not in ADMINS:
        return

    args = message.text.split()

    if len(args) != 3:
        bot.reply_to(
            message,
            "/addmoney ID СУММА"
        )
        return

    target = args[1]

    try:
        amount = int(args[2])
    except:
        return

    if target not in data:
        return

    data[target]["balance"] += amount

    save_data(data)

    bot.reply_to(
        message,
        panel(
            "АДМИН",
            f"Выдано {amount} XTRA"
        )
    )


# ==========================================
# REMOVE MONEY
# ==========================================

@bot.message_handler(commands=["removemoney"])
def remove_money(message):

    if message.from_user.id not in ADMINS:
        return

    args = message.text.split()

    if len(args) != 3:
        return

    target = args[1]

    try:
        amount = int(args[2])
    except:
        return

    if target not in data:
        return

    data[target]["balance"] -= amount

    if data[target]["balance"] < 0:
        data[target]["balance"] = 0

    save_data(data)

    bot.reply_to(
        message,
        panel(
            "АДМИН",
            f"Снято {amount} XTRA"
        )
    )


# ==========================================
# USER INFO
# ==========================================

@bot.message_handler(commands=["userinfo"])
def user_info(message):

    if not message.reply_to_message:
        bot.reply_to(
            message,
            "Ответьте на сообщение пользователя."
        )
        return

    uid = str(message.reply_to_message.from_user.id)

    if uid not in data:
        return

    ensure_rep(uid)

    user = data[uid]

    text = (
        f"👤 {user['name']}\n"
        f"💰 Баланс: {user['balance']}\n"
        f"🎁 Кейсы: {user['cases']}\n"
        f"⭐ Репутация: {user['rep']}\n"
        f"🏆 Побед: {user['wins']}\n"
        f"❌ Поражений: {user['loses']}"
    )

    bot.reply_to(
        message,
        panel(
            "ИНФОРМАЦИЯ",
            text
        )
    )


# ==========================================
# CHAT STATS
# ==========================================

@bot.message_handler(commands=["stats"])
def stats(message):

    total_money = 0
    total_cases = 0

    for uid in data:
        total_money += data[uid]["balance"]
        total_cases += data[uid]["cases"]

    bot.reply_to(
        message,
        panel(
            "СТАТИСТИКА",
            f"Игроков: {len(data)}\n"
            f"Монет в экономике: {total_money}\n"
            f"Кейсов: {total_cases}"
        )
    )


# ==========================================
# LEADERBOARD REP
# ==========================================

@bot.message_handler(commands=["reptop"])
def rep_top(message):

    players = []

    for uid in data:

        if "rep" not in data[uid]:
            data[uid]["rep"] = 0

        players.append(data[uid])

    players = sorted(
        players,
        key=lambda x: x["rep"],
        reverse=True
    )

    text = ""

    pos = 1

    for player in players[:10]:

        text += (
            f"{pos}. {player['name']} — "
            f"{player['rep']} ⭐\n"
        )

        pos += 1

    bot.reply_to(
        message,
        panel(
            "ТОП РЕПУТАЦИИ",
            text
        )
    )


# ==========================================
# WELCOME NEW MEMBERS
# ==========================================

@bot.message_handler(content_types=["new_chat_members"])
def welcome(message):

    for user in message.new_chat_members:

        create_user(user)

        bot.send_message(
            message.chat.id,
            panel(
                "ДОБРО ПОЖАЛОВАТЬ",
                f"{user.first_name}, добро пожаловать в {CLAN_NAME}!"
            )
        )


# ==========================================
# SIMPLE ANTI FLOOD
# ==========================================

user_cooldowns = {}

@bot.message_handler(func=lambda m: True)
def anti_flood(message):

    uid = message.from_user.id

    now = time.time()

    if uid not in user_cooldowns:
        user_cooldowns[uid] = now
        return

    diff = now - user_cooldowns[uid]

    user_cooldowns[uid] = now

    if diff < 0.5:
        return


# ==========================================
# COMMANDS LIST
# ==========================================

@bot.message_handler(commands=["commands"])
def commands(message):

    text = """
/start - запуск
/help - помощь

/profile - профиль
/balance - баланс
/daily - ежедневная награда
/farm - фарм монет
/pay - перевод
/top - топ богатых

/casino СУММА - казино

/shop - магазин
/buy ID - купить
/inventory - инвентарь

/cases - кейсы
/open - открыть кейс

/rep - дать репутацию
/myrep - моя репутация
/reptop - топ репутации

/clan - информация о клане
/stats - статистика

/userinfo - информация о игроке

АДМИН:
/addmoney
/removemoney
/givecase
"""

    bot.reply_to(
        message,
        panel(
            "КОМАНДЫ",
            text
        )
    )
    
save_data(data)

print("XTRA ELITA PRO ONLINE")

bot.infinity_polling(skip_pending=True)

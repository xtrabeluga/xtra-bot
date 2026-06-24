# XTRA ELITA LITE
# Part 1/3
# pyTelegramBotAPI

import telebot
import os
import json
import time
import random
from flask import Flask, request

# ================= ANTI FLOOD =================

FLOOD_LIMIT = 5      # сообщений
FLOOD_TIME = 10      # секунд
MUTE_TIME = 60       # секунд

flood_cache = {}

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise Exception("TOKEN environment variable not found!")

bot = telebot.TeleBot(TOKEN)

bot.remove_webhook()

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
			
def find_user_id(identifier):
    identifier = str(identifier).replace("@", "").lower()

    for uid, user in data.items():

        username = user.get("username")

        if username and username.lower() == identifier:
            return uid

        if uid == identifier:
            return uid

    return None

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
            "username": user.username,  # 🔥 ДОБАВИЛИ
			
            "balance": 1000,
			
            "farm_time": 0,
            "daily_time": 0,
			
            "inventory": [],
            "cases": 0,
			
            "wins": 0,
            "loses": 0,
			
			"rep": 0,
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

def panel_clean(title, text):
    return (
        f"🔥 {title}\n"
        f"{text}"
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
            (
                f"👋 Привет, {message.from_user.first_name}!\n\n"
                "💰 Экономика • 🎲 Казино • 🛒 Магазин\n\n"
                "🚀 Начни с:\n"
                "/profile — твой профиль\n"
                "/daily — ежедневная награда\n"
                "/farm — фарм монет\n\n"
                "📜 Напиши /help чтобы увидеть все команды"
            ),
            "👑"
        )
    )


# =========================
# HELP
# =========================

@bot.message_handler(commands=["help"])
def help_cmd(message):

    text = ""

    for category, cmds in COMMANDS.items():
        text += f"{category}\n"

        for cmd, desc in cmds.items():
            text += f" /{cmd} — {desc}\n"

        text += "\n"

    bot.reply_to(
        message,
        panel(
            "📜 HELP MENU",
            text
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
        f"👤 Игрок: {user['name']}\n\n"
        f"💰 Баланс: {user['balance']} XTRA\n"
        f"🎁 Кейсы: {user['cases']}\n"
        f"📦 Инвентарь: {len(user['inventory'])}\n\n"
        f"🏆 Победы: {user['wins']}\n"
        f"❌ Поражения: {user['loses']}\n"
        f"⭐ Репутация: {user.get('rep', 0)}\n\n"
        f"🆔 ID: {user['id']}"
    )

    bot.reply_to(
        message,
        panel("PROFILE", text, "👤")
    )


# =========================
# BALANCE
# =========================

@bot.message_handler(commands=["balance"])
def balance(message):
    create_user(message.from_user)

    user = get_user(message.from_user.id)

    text = (
        f"💰 Баланс\n\n"
        f"💵 {user['balance']} XTRA\n\n"
        f"👤 Игрок: {user['name']}\n"
        f"🆔 ID: {user['id']}\n\n"
        f"💡 Зарабатывай через /farm или /casino"
    )

    bot.reply_to(
        message,
        panel("BALANCE", text, "💰")
    )

# =========================
# DAILY
# =========================

@bot.message_handler(commands=["daily"])
def daily(message):
    create_user(message.from_user)

    uid = str(message.from_user.id)
    user = get_user(message.from_user.id)

    now = int(time.time())

    # cooldown 24h
    if now - data[uid]["daily_time"] < 86400:
        left = 86400 - (now - data[uid]["daily_time"])

        hours = left // 3600
        minutes = (left % 3600) // 60

        text = (
            f"⏳ Награда уже получена\n\n"
            f"🕒 Осталось: {hours}ч {minutes}м\n\n"
            f"💡 Возвращайся позже за бонусом"
        )

        bot.reply_to(message, panel("DAILY", text, "⏳"))
        return

    reward = 10000

    data[uid]["balance"] += reward
    data[uid]["daily_time"] = now

    save_data(data)

    text = (
        f"🎁 Ежедневная награда получена!\n\n"
        f"💵 +{reward} XTRA\n\n"
        f"👤 Игрок: {user['name']}\n"
        f"💰 Новый баланс: {data[uid]['balance']}\n\n"
        f"💡 Приходи завтра снова"
    )

    bot.reply_to(message, panel("DAILY REWARD", text, "🎁"))


# =========================
# FARM
# =========================

@bot.message_handler(commands=["farm"])
def farm(message):
    create_user(message.from_user)

    uid = str(message.from_user.id)
    user = data[uid]

    now = int(time.time())

    # =====================
    # COOLDOWN 15 sec
    # =====================
    if now - user["farm_time"] < 15:
        left = 15 - (now - user["farm_time"])

        text = (
            f"⏳ Слишком рано!\n\n"
            f"🕒 Подожди: {left} сек\n\n"
            f"💡 Фарм доступен каждые 15 секунд"
        )

        bot.reply_to(message, panel("FARM", text, "⏳"))
        return

    # =====================
    # REWARD SYSTEM
    # =====================
    base = random.randint(50, 5000)

    # шанс бонуса
    bonus = 0
    if random.randint(1, 100) <= 20:  # 20% шанс
        bonus = random.randint(500, 2000)

    total = base + bonus

    user["balance"] += total
    user["farm_time"] = now

    save_data(data)

    # =====================
    # TEXT UI
    # =====================
    if bonus > 0:
        text = (
            f"⛏ Удачный фарм!\n\n"
            f"💵 База: {base} XTRA\n"
            f"🎁 Бонус: +{bonus}\n\n"
            f"💰 Итого: +{total} XTRA\n"
            f"💰 Баланс: {user['balance']}"
        )
    else:
        text = (
            f"⛏ Фарм завершён\n\n"
            f"💵 Получено: +{total} XTRA\n\n"
            f"💰 Баланс: {user['balance']}"
        )

    bot.reply_to(message, panel("FARM MINING", text, "⛏"))


# =========================
# PAY
# =========================

@bot.message_handler(commands=["pay"])
def pay(message):
    create_user(message.from_user)

    args = message.text.split()
    sender = str(message.from_user.id)

    # =========================
    # CASE 1: reply message
    # /pay 100
    # =========================
    if message.reply_to_message:
        if len(args) != 2:
            bot.reply_to(message, "Использование: /pay СУММА (в ответ)")
            return

        target = str(message.reply_to_message.from_user.id)

        try:
            amount = int(args[1])
        except:
            bot.reply_to(message, "❌ Введите число")
            return

    # =========================
    # CASE 2: username / id
    # /pay @user 100
    # /pay 123 100
    # =========================
    else:
        if len(args) != 3:
            bot.reply_to(message, "Использование: /pay @user СУММА или /pay ID СУММА")
            return

        target = find_user_id(args[1])

        try:
            amount = int(args[2])
        except:
            bot.reply_to(message, "❌ Введите число")
            return

    # =========================
    # CHECKS
    # =========================
    if not target or target not in data:
        bot.reply_to(message, "❌ Игрок не найден")
        return

    if amount <= 0:
        bot.reply_to(message, "❌ Сумма должна быть больше 0")
        return

    if sender == target:
        bot.reply_to(message, "❌ Нельзя перевести самому себе")
        return

    if data[sender]["balance"] < amount:
        bot.reply_to(message, "❌ Недостаточно средств")
        return

    # =========================
    # TRANSFER
    # =========================
    data[sender]["balance"] -= amount
    data[target]["balance"] += amount

    save_data(data)

    # =========================
    # USER INFO
    # =========================
    receiver_name = data[target]["name"]

    text = (
        f"💸 ПЕРЕВОД УСПЕШЕН\n\n"
        f"👤 От: {data[sender]['name']}\n"
        f"👤 Кому: {receiver_name}\n\n"
        f"💵 Сумма: {amount} XTRA\n"
        f"💰 Ваш баланс: {data[sender]['balance']}"
    )

    bot.reply_to(message, panel("TRANSFER", text, "💸"))

# =========================
# TOP
# =========================

@bot.message_handler(commands=["top"])
def top(message):
    create_user(message.from_user)

    # =========================
    # SORT PLAYERS
    # =========================
    players = sorted(
        data.values(),
        key=lambda x: x["balance"],
        reverse=True
    )

    medals = ["🥇", "🥈", "🥉"]

    text = ""

    for i, player in enumerate(players[:10]):
        name = player.get("name", "Unknown")
        balance = player.get("balance", 0)

        if i < 3:
            icon = medals[i]
        else:
            icon = f"{i+1}."

        text += f"{icon} {name} — 💰 {balance} XTRA\n"

    # =========================
    # EMPTY CHECK
    # =========================
    if not players:
        text = "Пока нет игроков"

    bot.reply_to(
        message,
        panel("TOP PLAYERS", text, "🏆")
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
        "price": 5000,
        "emoji": "💎",
        "desc": "x1.5 к наградам"
    },
    "m416": {
        "name": "M416 Glacier",
        "price": 15000,
        "emoji": "🔫",
        "desc": "Редкое оружие"
    },
    "xsuit": {
        "name": "X-SUIT",
        "price": 50000,
        "emoji": "🛡",
        "desc": "Легендарный скин"
    },
    "case": {
        "name": "Кейс",
        "price": 3000,
        "emoji": "📦",
        "desc": "Случайная награда"
    }
}

COMMANDS = {
    "👤 ИГРОК": {
        "profile": "Профиль игрока",
        "balance": "Показать баланс",
        "daily": "Ежедневная награда",
        "rep": "Выдать репутацию (reply)",
        "myrep": "Моя репутация"
    },

    "⛏ ФАРМ / ЭКОНОМИКА": {
        "farm": "Заработок монет",
        "casino": "Игровое казино",
        "top": "Топ богатых игроков"
    },

    "💸 ПЕРЕВОДЫ": {
        "pay": "Перевод монет игроку",
        "userinfo": "Информация об игроке"
    },

    "🛒 МАГАЗИН": {
        "shop": "Открыть магазин",
        "buy": "Купить предмет",
        "inventory": "Инвентарь"
    },

    "🎁 КЕЙСЫ": {
        "cases": "Показать кейсы",
        "open": "Открыть кейс"
    },

    "📊 СТАТ": {
        "stats": "Статистика сервера",
        "reptop": "Топ репутации",
        "clan": "Информация о клане"
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
    uid = str(message.from_user.id)
    user = data[uid]

    # =========================
    # CHECK INPUT
    # =========================
    if len(args) != 2:
        bot.reply_to(
            message,
            panel(
                "CASINO",
                "Использование:\n/casino СУММА",
                "🎲"
            )
        )
        return

    try:
        bet = int(args[1])
    except:
        bot.reply_to(message, "❌ Введите число")
        return

    if bet <= 0:
        return

    if user["balance"] < bet:
        bot.reply_to(
            message,
            panel("CASINO", "❌ Недостаточно средств", "🎲")
        )
        return

    # =========================
    # ROLL SYSTEM
    # =========================
    roll = random.randint(1, 100)

    # LOSE
    if roll <= 45:
        user["balance"] -= bet
        user["loses"] += 1

        result_text = (
            f"💥 ПРОИГРЫШ\n\n"
            f"🎲 Шанс: {roll}/100\n"
            f"💸 -{bet} XTRA\n\n"
            f"💰 Баланс: {user['balance']}"
        )

    # NORMAL WIN
    elif roll <= 85:
        win = bet * 2
        user["balance"] += win
        user["wins"] += 1

        result_text = (
            f"🎉 ПОБЕДА\n\n"
            f"🎲 Шанс: {roll}/100\n"
            f"💵 +{win} XTRA\n\n"
            f"💰 Баланс: {user['balance']}"
        )

    # JACKPOT
    else:
        jackpot = bet * 5
        user["balance"] += jackpot
        user["wins"] += 1

        result_text = (
            f"💎 ДЖЕКПОТ!\n\n"
            f"🎲 Шанс: {roll}/100\n"
            f"🔥 +{jackpot} XTRA\n\n"
            f"💰 Баланс: {user['balance']}"
        )

    save_data(data)

    bot.reply_to(
        message,
        panel("CASINO", result_text, "🎲")
    )

# ==========================================
# SHOP
# ==========================================

@bot.message_handler(commands=["shop"])
def shop(message):
    create_user(message.from_user)

    text = "🛒 МАГАЗИН XTRA ELITA\n\n"

    # =========================
    # ITEMS LIST
    # =========================
    for item_id, item in SHOP_ITEMS.items():

        emoji = item.get("emoji", "📦")
        name = item.get("name", "Item")
        price = item.get("price", 0)
        desc = item.get("desc", "Нет описания")

        text += (
            f"{emoji} {name}\n"
            f"💰 Цена: {price} XTRA\n"
            f"📦 {desc}\n"
            f"🆔 /buy {item_id}\n"
            f"━━━━━━━━━━━━━━\n"
        )

    text += "\n💡 Покупка: /buy ID"

    bot.reply_to(
        message,
        panel("SHOP", text, "🛒")
    )


# ==========================================
# BUY
# ==========================================

@bot.message_handler(commands=["buy"])
def buy(message):
    create_user(message.from_user)

    args = message.text.split()
    uid = str(message.from_user.id)
    user = data[uid]

    # =========================
    # CHECK INPUT
    # =========================
    if len(args) != 2:
        bot.reply_to(
            message,
            panel(
                "SHOP",
                "Использование:\n/buy ID",
                "🛒"
            )
        )
        return

    item_id = args[1].lower()

    # =========================
    # CHECK ITEM
    # =========================
    if item_id not in SHOP_ITEMS:
        bot.reply_to(
            message,
            panel("SHOP", "❌ Предмет не найден", "🛒")
        )
        return

    item = SHOP_ITEMS[item_id]

    name = item["name"]
    price = item["price"]

    # =========================
    # CHECK MONEY
    # =========================
    if user["balance"] < price:
        bot.reply_to(
            message,
            panel(
                "SHOP",
                "❌ Недостаточно XTRA",
                "🛒"
            )
        )
        return

    # =========================
    # BUY ITEM
    # =========================
    user["balance"] -= price

    if item_id == "case":
        user["cases"] += 1
        result = "📦 +1 кейс добавлен"
    else:
        user["inventory"].append(name)
        result = f"🎁 {name} добавлен в инвентарь"

    save_data(data)

    # =========================
    # RESPONSE
    # =========================
    bot.reply_to(
        message,
        panel(
            "ПОКУПКА 🛒",
            f"✔ Куплено: {name}\n"
            f"💰 -{price} XTRA\n\n"
            f"{result}"
        )
    )

# ==========================================
# INVENTORY
# ==========================================

@bot.message_handler(commands=["inventory"])
def inventory(message):
    create_user(message.from_user)

    uid = str(message.from_user.id)
    user = data[uid]

    inv = user.get("inventory", [])

    # =========================
    # EMPTY INVENTORY
    # =========================
    if not inv:
        bot.reply_to(
            message,
            panel(
                "ИНВЕНТАРЬ 🎒",
                "Пусто.\n\nКупи предметы в /shop",
                "🎒"
            )
        )
        return

    # =========================
    # BUILD LIST
    # =========================
    text = f"🎒 У вас предметов: {len(inv)}\n\n"

    for i, item in enumerate(inv, start=1):
        text += f"{i}. 🎁 {item}\n"

    # =========================
    # RESPONSE
    # =========================
    bot.reply_to(
        message,
        panel(
            "ИНВЕНТАРЬ 🎒",
            text,
            "🎒"
        )
    )

# ==========================================
# MY CASES
# ==========================================

@bot.message_handler(commands=["cases"])
def cases(message):
    create_user(message.from_user)

    uid = str(message.from_user.id)
    user = data[uid]

    count = user.get("cases", 0)

    # =========================
    # EMPTY CASES
    # =========================
    if count <= 0:
        bot.reply_to(
            message,
            panel(
                "КЕЙСЫ 📦",
                "У вас нет кейсов.\n\nКупите их в /shop",
                "📦"
            )
        )
        return

    # =========================
    # INFO
    # =========================
    text = (
        f"📦 Ваши кейсы: {count}\n\n"
        "🎁 Что внутри:\n"
        "• Монеты XTRA\n"
        "• VIP / редкие предметы\n"
        "• M416 / X-SUIT\n\n"
        "👉 Используйте /open"
    )

    bot.reply_to(
        message,
        panel(
            "КЕЙСЫ 📦",
            text,
            "📦"
        )
    )

# ==========================================
# OPEN CASE
# ==========================================

@bot.message_handler(commands=["open"])
def open_case(message):
    create_user(message.from_user)

    uid = str(message.from_user.id)
    user = data[uid]

    # =========================
    # CHECK CASES
    # =========================
    if user.get("cases", 0) <= 0:
        bot.reply_to(
            message,
            panel(
                "ОТКРЫТИЕ КЕЙСА 📦",
                "❌ У вас нет кейсов\n\nКупите в /shop",
                "📦"
            )
        )
        return

    # =========================
    # REMOVE CASE
    # =========================
    user["cases"] -= 1

    # =========================
    # LOOT TABLE
    # =========================
    rewards = [
        {"type": "money", "value": 1000, "text": "💰 +1000 XTRA"},
        {"type": "money", "value": 5000, "text": "💰 +5000 XTRA"},
        {"type": "money", "value": 10000, "text": "💰 +10000 XTRA"},
        {"type": "item", "value": "VIP Статус", "text": "💎 VIP Статус"},
        {"type": "item", "value": "M416 Glacier", "text": "🔫 M416 Glacier"},
        {"type": "item", "value": "X-SUIT", "text": "🛡 X-SUIT"}
    ]

    import random
    reward = random.choice(rewards)

    # =========================
    # APPLY REWARD
    # =========================
    if reward["type"] == "money":
        user["balance"] += reward["value"]
        result = reward["text"]

    else:
        user["inventory"].append(reward["value"])
        result = f"🎁 Получено: {reward['value']}"

    save_data(data)

    # =========================
    # RESPONSE
    # =========================
    bot.reply_to(
        message,
        panel(
            "КЕЙС ОТКРЫТ 📦",
            f"🎲 Результат:\n{result}\n\n"
            f"📦 Осталось кейсов: {user['cases']}",
            "🎁"
        )
    )

# ==========================================
# GIVE CASE (ADMIN)
# ==========================================

ADMINS = [
    8573898148
]

@bot.message_handler(commands=['givecase'])
def give_case(message):
    user_id = message.from_user.id

    # ===== ADMIN CHECK =====
    if user_id not in ADMINS:
        bot.reply_to(message, panel(
            "⛔ Доступ запрещён",
            "У вас нет прав администратора.",
            style="admin"
        ))
        return

    args = message.text.split()

    target_id = None
    case_name = None
    amount = 1

    # ===== REPLY SUPPORT =====
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        args = args[1:]  # remove command

    # ===== PARSE ARGS =====
    if len(args) >= 2:
        if not target_id:
            target = args[1]

            if target.isdigit():
                target_id = int(target)
            else:
                target_id = find_user_id(target)  # username support

        # case name
        case_name = args[2] if len(args) >= 3 else None

        # amount (optional)
        if len(args) >= 4:
            try:
                amount = int(args[3])
            except:
                amount = 1

    # ===== VALIDATION =====
    if not target_id:
        bot.reply_to(message, panel(
            "❌ Ошибка",
            "Укажи пользователя:\n"
            "/givecase @user case_name [кол-во]\n"
            "или ответом (reply)",
            style="admin"
        ))
        return

    if not case_name:
        bot.reply_to(message, panel(
            "❌ Ошибка",
            "Укажи название кейса.",
            style="admin"
        ))
        return

    if amount <= 0:
        bot.reply_to(message, panel(
            "❌ Ошибка",
            "Количество должно быть больше 0.",
            style="admin"
        ))
        return

    # ===== GIVE CASE =====
    if target_id not in user_data:
        user_data[target_id] = {"cases": {}}

    user_data[target_id].setdefault("cases", {})
    user_data[target_id]["cases"][case_name] = user_data[target_id]["cases"].get(case_name, 0) + amount

    save_data()

    # ===== GET USERNAME SAFE =====
    try:
        target_user = bot.get_chat(target_id)
        name = target_user.username or target_user.first_name
    except:
        name = str(target_id)

    # ===== SUCCESS MESSAGE =====
    bot.send_message(message.chat.id, panel(
        "🎁 Кейсы выданы",
        f"👤 Пользователь: {name}\n"
        f"📦 Кейс: {case_name}\n"
        f"🔢 Кол-во: {amount}\n\n"
        f"✅ Успешно добавлено в инвентарь",
        style="admin"
    ))

# ==========================================
# PART 3 - CLAN / ADMIN / REP / MODERATION
# ==========================================

# ==========================================
# CLAN SYSTEM
# ==========================================

CLAN_NAME = "XTRA ELITA"

@bot.message_handler(commands=['clan_create'])
def clan_create(message):
    user_id = str(message.from_user.id)
    args = message.text.split()

    if len(args) < 3:
        bot.reply_to(message, panel(
            "❌ Ошибка",
            "Использование:\n/clan_create TAG Название",
            style="main"
        ))
        return

    tag = args[1].upper()
    name = " ".join(args[2:])

    if tag in data.get("clans", {}):
        bot.reply_to(message, panel(
            "❌ Ошибка",
            "Такой клан уже существует.",
            style="main"
        ))
        return

    data.setdefault("clans", {})
    data["clans"][tag] = {
        "name": name,
        "owner": int(user_id),
        "members": [int(user_id)],
        "balance": 0
    }

    user_data[user_id]["clan"] = tag
    user_data[user_id]["clan_role"] = "owner"

    save_data()

    bot.reply_to(message, panel(
        "🛡️ Клан создан",
        f"🏷️ TAG: {tag}\n"
        f"📛 Название: {name}\n"
        f"👑 Владелец: {message.from_user.first_name}",
        style="economy"
    ))


# ==========================================
# REP SYSTEM
# ==========================================

def ensure_rep(uid):
    if "rep" not in data[uid]:
        data[uid]["rep"] = 0


import time

REP_COOLDOWN = 3600  # 1 час

@bot.message_handler(commands=['rep'])
def give_rep(message):
    user_id = str(message.from_user.id)
    args = message.text.split()

    # ===== FIND TARGET =====
    target_id = None

    if message.reply_to_message:
        target_id = str(message.reply_to_message.from_user.id)
    elif len(args) >= 2:
        target = args[1]

        if target.isdigit():
            target_id = target
        else:
            target_id = find_user_id(target)

    # ===== VALIDATION =====
    if not target_id:
        bot.reply_to(message, "❌ Укажи пользователя (reply / @username / ID)")
        return

    if target_id == user_id:
        bot.reply_to(message, "❌ Нельзя дать реп самому себе")
        return

    # ===== INIT USERS =====
    user_data.setdefault(target_id, {})
    user_data.setdefault(user_id, {})

    user_data[target_id].setdefault("rep", 0)
    user_data[user_id].setdefault("rep_given", {"last_time": 0})

    # ===== COOLDOWN =====
    now = time.time()
    last = user_data[user_id]["rep_given"]["last_time"]

    if now - last < REP_COOLDOWN:
        remaining = int(REP_COOLDOWN - (now - last))
        bot.reply_to(message, f"⏳ Подожди {remaining} сек перед следующей репутацией")
        return

    # ===== ADD REP =====
    user_data[target_id]["rep"] += 1
    user_data[user_id]["rep_given"]["last_time"] = now

    save_data()

    # ===== RESPONSE =====
    bot.reply_to(message, panel(
        "⭐ Репутация",
        f"➕ +1 REP пользователю {target_id}\n"
        f"🔥 Теперь у него: {user_data[target_id]['rep']} REP",
        style="economy"
    ))


# ==========================================
# MY REP
# ==========================================

@bot.message_handler(commands=['myrep'])
def my_rep(message):
    user_id = str(message.from_user.id)

    user_data.setdefault(user_id, {})
    rep = user_data[user_id].get("rep", 0)

    # ===== RANK (optional PRO feature) =====
    if rep >= 100:
        rank = "🏅 LEGEND"
    elif rep >= 50:
        rank = "🔥 PRO"
    elif rep >= 20:
        rank = "⭐ TRUSTED"
    elif rep >= 5:
        rank = "🙂 ACTIVE"
    else:
        rank = "🆕 NEW"

    # ===== RESPONSE =====
    bot.reply_to(message, panel(
        "⭐ Моя репутация",
        f"👤 Твой ID: {user_id}\n"
        f"⭐ REP: {rep}\n"
        f"🏷️ Ранг: {rank}\n\n"
        f"💡 Используй /rep чтобы получать репутацию",
        style="economy"
    ))


# ==========================================
# ADMIN ADD MONEY
# ==========================================

@bot.message_handler(commands=['addmoney'])
def add_money(message):
    admin_id = str(message.from_user.id)

    # ===== ADMIN CHECK =====
    if admin_id not in ADMINS:
        bot.reply_to(message, panel(
            "⛔ Доступ запрещён",
            "У вас нет прав администратора.",
            style="admin"
        ))
        return

    args = message.text.split()

    target_id = None
    amount = 0

    # ===== REPLY SUPPORT =====
    if message.reply_to_message:
        target_id = str(message.reply_to_message.from_user.id)
        args = args[1:]

    # ===== PARSE TARGET =====
    if len(args) >= 2:
        if not target_id:
            target = args[1]

            if target.isdigit():
                target_id = target
            else:
                target_id = find_user_id(target)

    # ===== PARSE AMOUNT =====
    if len(args) >= 3:
        try:
            amount = int(args[2])
        except:
            amount = 0

    # ===== VALIDATION =====
    if not target_id:
        bot.reply_to(message, panel(
            "❌ Ошибка",
            "Укажи пользователя:\n"
            "/addmoney @user 1000\n"
            "или reply + сумма",
            style="admin"
        ))
        return

    if amount <= 0:
        bot.reply_to(message, panel(
            "❌ Ошибка",
            "Сумма должна быть больше 0.",
            style="admin"
        ))
        return

    # ===== INIT USER =====
    user_data.setdefault(target_id, {})
    user_data[target_id].setdefault("balance", 0)

    user_data[target_id]["balance"] += amount

    save_data()

    # ===== GET NAME SAFE =====
    try:
        target_user = bot.get_chat(int(target_id))
        name = target_user.first_name
    except:
        name = target_id

    # ===== RESPONSE =====
    bot.send_message(message.chat.id, panel(
        "💰 Баланс пополнен",
        f"👤 Пользователь: {name}\n"
        f"➕ +{amount} XTRA\n"
        f"💳 Новый баланс: {user_data[target_id]['balance']}",
        style="admin"
    ))

# ==========================================
# REMOVE MONEY
# ==========================================

@bot.message_handler(commands=['removemoney'])
def remove_money(message):
    admin_id = str(message.from_user.id)

    # ===== ADMIN CHECK =====
    if admin_id not in ADMINS:
        bot.reply_to(message, panel(
            "⛔ Доступ запрещён",
            "У вас нет прав администратора.",
            style="admin"
        ))
        return

    args = message.text.split()

    target_id = None
    amount = 0

    # ===== REPLY SUPPORT =====
    if message.reply_to_message:
        target_id = str(message.reply_to_message.from_user.id)
        args = args[1:]

    # ===== PARSE TARGET =====
    if len(args) >= 2:
        if not target_id:
            target = args[1]

            if target.isdigit():
                target_id = target
            else:
                target_id = find_user_id(target)

    # ===== PARSE AMOUNT =====
    if len(args) >= 3:
        try:
            amount = int(args[2])
        except:
            amount = 0

    # ===== VALIDATION =====
    if not target_id:
        bot.reply_to(message, panel(
            "❌ Ошибка",
            "Укажи пользователя:\n"
            "/removemoney @user 1000\n"
            "или reply + сумма",
            style="admin"
        ))
        return

    if amount <= 0:
        bot.reply_to(message, panel(
            "❌ Ошибка",
            "Сумма должна быть больше 0.",
            style="admin"
        ))
        return

    # ===== INIT USER =====
    user_data.setdefault(target_id, {})
    user_data[target_id].setdefault("balance", 0)

    current_balance = user_data[target_id]["balance"]

    # ===== SAFE REMOVE =====
    if current_balance < amount:
        amount = current_balance  # не уходим в минус

    user_data[target_id]["balance"] -= amount

    save_data()

    # ===== GET NAME SAFE =====
    try:
        target_user = bot.get_chat(int(target_id))
        name = target_user.first_name
    except:
        name = target_id

    # ===== RESPONSE =====
    bot.send_message(message.chat.id, panel(
        "💸 Баланс уменьшен",
        f"👤 Пользователь: {name}\n"
        f"➖ -{amount} XTRA\n"
        f"💳 Новый баланс: {user_data[target_id]['balance']}",
        style="admin"
    ))

# ==========================================
# USER INFO
# ==========================================

@bot.message_handler(commands=['userinfo'])
def user_info(message):
    user_id = str(message.from_user.id)
    args = message.text.split()

    target_id = None

    # ===== REPLY SUPPORT =====
    if message.reply_to_message:
        target_id = str(message.reply_to_message.from_user.id)

    # ===== ARG SUPPORT =====
    elif len(args) >= 2:
        target = args[1]

        if target.isdigit():
            target_id = target
        else:
            target_id = find_user_id(target)

    # ===== DEFAULT SELF =====
    if not target_id:
        target_id = user_id

    user_data.setdefault(target_id, {})

    # ===== DATA SAFE GET =====
    balance = user_data[target_id].get("balance", 0)
    rep = user_data[target_id].get("rep", 0)

    clan = user_data[target_id].get("clan")
    clan_text = clan if clan else "Нет клана"

    cases = user_data[target_id].get("cases", {})
    total_cases = sum(cases.values()) if cases else 0

    # ===== RANK SYSTEM (from REP) =====
    if rep >= 100:
        rank = "🏅 LEGEND"
    elif rep >= 50:
        rank = "🔥 PRO"
    elif rep >= 20:
        rank = "⭐ TRUSTED"
    elif rep >= 5:
        rank = "🙂 ACTIVE"
    else:
        rank = "🆕 NEW"

    # ===== GET NAME SAFE =====
    try:
        tg_user = bot.get_chat(int(target_id))
        name = tg_user.first_name
    except:
        name = target_id

    # ===== OUTPUT =====
    bot.reply_to(message, panel(
        "👤 USER INFO",
        f"👤 Имя: {name}\n"
        f"🆔 ID: {target_id}\n\n"
        f"💰 Баланс: {balance} XTRA\n"
        f"⭐ REP: {rep} ({rank})\n"
        f"🛡️ Клан: {clan_text}\n"
        f"📦 Кейсы: {total_cases}\n",
        style="economy"
    ))


# ==========================================
# CHAT STATS
# ==========================================

@bot.message_handler(commands=['chatstats'])
def chat_stats(message):
    user_id = str(message.from_user.id)
    args = message.text.split()

    target_id = None

    # Reply support
    if message.reply_to_message:
        target_id = str(message.reply_to_message.from_user.id)

    # Username / ID support
    elif len(args) >= 2:
        target = args[1]

        if target.isdigit():
            target_id = target
        else:
            target_id = find_user_id(target)

    # Self by default
    if not target_id:
        target_id = user_id

    user_data.setdefault(target_id, {})

    messages = user_data[target_id].get("messages", 0)
    balance = user_data[target_id].get("balance", 0)
    rep = user_data[target_id].get("rep", 0)

    try:
        user = bot.get_chat(int(target_id))
        name = user.first_name
    except:
        name = target_id

    bot.reply_to(message, panel(
        "📊 CHAT STATS",
        f"👤 Пользователь: {name}\n"
        f"🆔 ID: {target_id}\n\n"
        f"💬 Сообщений: {messages:,}\n"
        f"💰 Баланс: {balance:,} XTRA\n"
        f"⭐ REP: {rep:,}",
        style="main"
    ))

@bot.message_handler(func=lambda m: True, content_types=['text'])
def message_stats(message):
    user_id = str(message.from_user.id)

    user_data.setdefault(user_id, {})

    user_data[user_id]["messages"] = user_data[user_id].get("messages", 0) + 1

    save_data()
	
# ==========================================
# LEADERBOARD REP
# ==========================================

@bot.message_handler(commands=['leaderboardrep', 'reptop'])
def leaderboard_rep(message):
    ranking = sorted(
        user_data.items(),
        key=lambda x: x[1].get("rep", 0),
        reverse=True
    )

    text = ""
    place = 1

    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉"
    }

    for uid, data in ranking:
        rep = data.get("rep", 0)

        if rep <= 0:
            continue

        if place > 10:
            break

        try:
            user = bot.get_chat(int(uid))
            name = user.first_name
        except:
            name = f"ID {uid}"

        icon = medals.get(place, f"{place}.")

        text += (
            f"{icon} {name}\n"
            f"⭐ REP: {rep}\n\n"
        )

        place += 1

    if not text:
        text = "Пока никто не получил репутацию."

    bot.reply_to(message, panel(
        "🏆 LEADERBOARD REP",
        text,
        style="economy"
    ))


# ==========================================
# WELCOME NEW MEMBERS
# ==========================================

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for member in message.new_chat_members:

        name = member.first_name

        text = panel(
            "🎉 Добро пожаловать!",
            f"👋 Привет, {name}!\n\n"
            f"Добро пожаловать в сообщество XTRA ELITA.\n\n"
            f"📜 Используй /help чтобы посмотреть команды.\n"
            f"💰 Начни зарабатывать через /daily и /farm.\n"
            f"🏆 Поднимай REP через /rep.\n"
            f"🛡️ Вступай в кланы и участвуй в жизни сообщества.\n\n"
            f"Желаем приятного общения! 🚀",
            style="main"
        )

        bot.send_message(message.chat.id, text)


# ==========================================
# SIMPLE ANTI FLOOD
# ==========================================

user_cooldowns = {}

@bot.message_handler(func=lambda m: m.chat.type in ["group", "supergroup"])
def anti_flood(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Не проверяем админов
    if str(user_id) in ADMINS:
        return

    now = time.time()

    key = f"{chat_id}:{user_id}"

    if key not in flood_cache:
        flood_cache[key] = []

    # Оставляем только свежие сообщения
    flood_cache[key] = [
        t for t in flood_cache[key]
        if now - t < FLOOD_TIME
    ]

    flood_cache[key].append(now)

    # Проверка лимита
    if len(flood_cache[key]) >= FLOOD_LIMIT:

        try:
            until_date = int(now + MUTE_TIME)

            bot.restrict_chat_member(
                chat_id,
                user_id,
                until_date=until_date,
                permissions=telebot.types.ChatPermissions(
                    can_send_messages=False
                )
            )

            bot.send_message(
                chat_id,
                panel(
                    "🚫 Анти-Флуд",
                    f"👤 {message.from_user.first_name}\n"
                    f"⚠️ Слишком много сообщений\n"
                    f"🔇 Мут: {MUTE_TIME} сек",
                    style="admin"
                )
            )

        except Exception as e:
            print("Flood Error:", e)

        flood_cache[key] = []


# ==========================================
# COMMANDS LIST
# ==========================================

# ==========================================
# COMMANDS LIST
# ==========================================

@bot.message_handler(commands=["commands"])
def commands(message):

    text = """
🚀 ОСНОВНЫЕ

/start - запуск бота
/help - помощь
/commands - список команд

💰 ЭКОНОМИКА

/profile - профиль
/balance - баланс
/daily - ежедневная награда
/farm - фарм монет
/pay - перевод монет
/top - топ богатых
/casino СУММА - казино

🛒 МАГАЗИН

/shop - магазин
/buy ID - купить предмет
/inventory - инвентарь

📦 КЕЙСЫ

/cases - список кейсов
/open ID - открыть кейс

⭐ РЕПУТАЦИЯ

/rep - выдать репутацию
/myrep - моя репутация
/reptop - топ репутации

🛡️ КЛАНЫ

/clan_create - создать клан
/clan_join - вступить в клан
/clan_leave - покинуть клан
/clan_info - информация о клане
/clan_top - топ кланов

📊 СТАТИСТИКА

/userinfo - информация об игроке
/chatstats - статистика игрока
/chattop - топ активности
"""

    bot.reply_to(
        message,
        panel(
            "📜 СПИСОК КОМАНД",
            text,
            style="help"
        )
    )
    
save_data(data)

print("XTRA ELITA PRO ONLINE")

# =========================
# PRODUCTION START (MUST BE LAST)
# =========================

from flask import Flask
import threading
import time
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "XTRA ELITA PRO ONLINE"

@app.route("/health")
def health():
    return "OK"


def run_bot():
    while True:
        try:
            print("BOT STARTED")

            bot.remove_webhook()

            bot.infinity_polling(
                skip_pending=True,
                timeout=60,
                long_polling_timeout=60
            )

        except Exception as e:
            print("BOT ERROR:", e)
            time.sleep(5)


if __name__ == "__main__":

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )

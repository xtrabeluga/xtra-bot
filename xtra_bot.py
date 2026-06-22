import telebot
import os

TOKEN = os.getenv("8728701834:AAHRAB4hHJglxK87euGfJ-PbuIjzxbZ9kJM")  # токен берётся с Render

bot = telebot.TeleBot(TOKEN)

users = {}

def add_user(user_id):
    if user_id not in users:
        users[user_id] = {"coins": 0}

@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user.id)
    bot.send_message(
        message.chat.id,
        "🔥 Добро пожаловать в XTRA ELITA!\n💰 Валюта: XTRA Coin"
    )

@bot.message_handler(commands=['balance'])
def balance(message):
    add_user(message.from_user.id)
    coins = users[message.from_user.id]["coins"]
    bot.send_message(message.chat.id, f"💰 Баланс: {coins} XTRA Coin")

@bot.message_handler(commands=['daily'])
def daily(message):
    add_user(message.from_user.id)
    users[message.from_user.id]["coins"] += 100
    bot.send_message(message.chat.id, "🎁 +100 XTRA Coin получено!")

@bot.message_handler(commands=['work'])
def work(message):
    import random
    add_user(message.from_user.id)
    earn = random.randint(20, 150)
    users[message.from_user.id]["coins"] += earn
    bot.send_message(message.chat.id, f"💼 Ты заработал +{earn} XTRA Coin!")

@bot.message_handler(commands=['top'])
def top(message):
    sorted_users = sorted(users.items(), key=lambda x: x[1]["coins"], reverse=True)

    text = "🏆 ТОП ИГРОКОВ:\n"
    for i, (uid, data) in enumerate(sorted_users[:10], 1):
        text += f"{i}. ID {uid} — {data['coins']} XC\n"

    bot.send_message(message.chat.id, text)

print("Bot started...")
bot.infinity_polling(skip_pending=True)
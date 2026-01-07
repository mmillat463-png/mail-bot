import telebot
import requests
import time
from telebot import types
from flask import Flask
from threading import Thread

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8266049196:AAHf155FMeIHTdKL5BW_bi-fQgsqTrHg-wk"

bot = telebot.TeleBot(BOT_TOKEN)
API_URL = "https://api.mail.tm"
user_db = {}

# --- SERVER KEEPER (Render এর জন্য) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- HELPER FUNCTIONS ---
def get_domain():
    try:
        response = requests.get(f"{API_URL}/domains")
        if response.status_code == 200:
            return response.json()[0]['domain']
    except:
        return None
    return None

def create_account():
    domain = get_domain()
    if not domain:
        return None, None
    
    username = "user" + str(int(time.time()))
    password = "Pwd" + str(int(time.time())) + "!"
    email = f"{username}@{domain}"
    
    try:
        reg_resp = requests.post(f"{API_URL}/accounts", json={"address": email, "password": password})
        if reg_resp.status_code == 201:
            token_resp = requests.post(f"{API_URL}/token", json={"address": email, "password": password})
            if token_resp.status_code == 200:
                return email, token_resp.json()['token']
    except:
        pass
    return None, None

def get_messages(token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        return requests.get(f"{API_URL}/messages", headers=headers).json()
    except:
        return []

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📧 নতুন মেইল", "📩 ইনবক্স", "🔄 আমার মেইল")
    bot.reply_to(message, "স্বাগতম! প্রিমিয়াম মেইল বট (Render Hosted).", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    cid = message.chat.id
    text = message.text

    if text == "📧 নতুন মেইল":
        bot.send_message(cid, "🔄 মেইল জেনারেট হচ্ছে...")
        email, token = create_account()
        if email:
            user_db[cid] = {"email": email, "token": token}
            bot.send_message(cid, f"✅ <b>নতুন মেইল:</b>\n<code>{email}</code>", parse_mode="HTML")
        else:
            bot.send_message(cid, "❌ সার্ভার এরর।")

    elif text == "📩 ইনবক্স":
        if cid not in user_db:
            bot.send_message(cid, "⚠️ আগে মেইল খুলুন।")
            return
        bot.send_message(cid, "🔄 চেক করা হচ্ছে...")
        msgs = get_messages(user_db[cid]['token'])
        if not msgs:
            bot.send_message(cid, "📭 ইনবক্স খালি।")
        else:
            out = f"📨 <b>নতুন মেইল ({len(msgs)}):</b>\n\n"
            for m in msgs[:5]:
                out += f"👤 {m['from']['address']}\n🏷 {m['subject']}\n---\n"
            bot.send_message(cid, out)

    elif text == "🔄 আমার মেইল":
        if cid in user_db:
            bot.send_message(cid, f"মেইল: {user_db[cid]['email']}")

# --- RUN ---
keep_alive()
bot.infinity_polling()

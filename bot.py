import telebot
import requests
from telebot import types
from flask import Flask
from threading import Thread

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8266049196:AAHf155FMeIHTdKL5BW_bi-fQgsqTrHg-wk"

bot = telebot.TeleBot(BOT_TOKEN)
API_URL = "https://www.1secmail.com/api/v1"
user_db = {}

# --- SERVER KEEPER (Render) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📧 নতুন মেইল", "📩 ইনবক্স", "🔄 আমার মেইল")
    bot.reply_to(message, "স্বাগতম! হাই-স্পিড মেইল বট (Render)।", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    cid = message.chat.id
    text = message.text

    if text == "📧 নতুন মেইল":
        bot.send_message(cid, "🔄 মেইল জেনারেট হচ্ছে...")
        try:
            # 1secmail API
            resp = requests.get(f"{API_URL}/?action=genRandomMailbox&count=1")
            if resp.status_code == 200:
                email = resp.json()[0]
                login, domain = email.split('@')
                user_db[cid] = {"email": email, "login": login, "domain": domain}
                bot.send_message(cid, f"✅ <b>নতুন মেইল:</b>\n\n<code>{email}</code>", parse_mode="HTML")
            else:
                bot.send_message(cid, "❌ API কানেকশন ফেইলড।")
        except Exception as e:
            bot.send_message(cid, f"❌ এরর: {str(e)}")

    elif text == "📩 ইনবক্স":
        if cid not in user_db:
            bot.send_message(cid, "⚠️ আগে মেইল খুলুন।")
            return
        
        bot.send_message(cid, "🔄 ইনবক্স চেক করা হচ্ছে...")
        try:
            u = user_db[cid]
            resp = requests.get(f"{API_URL}/?action=getMessages&login={u['login']}&domain={u['domain']}")
            msgs = resp.json()
            
            if not msgs:
                bot.send_message(cid, "📭 ইনবক্স খালি।")
            else:
                out = f"📨 <b>নতুন মেইল ({len(msgs)}):</b>\n\n"
                for m in msgs[:5]:
                    out += f"👤 {m['from']}\n🏷 {m['subject']}\n---\n"
                bot.send_message(cid, out)
        except:
            bot.send_message(cid, "❌ ইনবক্স লোড করা যাচ্ছে না।")

    elif text == "🔄 আমার মেইল":
        if cid in user_db:
            bot.send_message(cid, f"মেইল: <code>{user_db[cid]['email']}</code>", parse_mode="HTML")

# --- RUN ---
keep_alive()
bot.infinity_polling()

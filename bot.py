# -*- coding: utf-8 -*-
import telebot
from telebot import types
import json
import os
import datetime

# --- CONFIGURATION ---
TOKEN = '8361180823:AAFWZOIO6WGl9SnXna_5ueSR3yPSTdcE1LI'
MAIN_ADMIN_ID = 6802901397
DB_FILE = 'database.json'

bot = telebot.TeleBot(TOKEN)

# Global State Storage
user_state = {}
temp_storage = {}

print("🚀 Bot Started Successfully...")

# --- DATABASE MANAGEMENT ---
def load_data():
    # If file doesn't exist, create fresh
    if not os.path.exists(DB_FILE):
        initial_data = {
            "users": {},
            "config": {
                "submissionChannel": MAIN_ADMIN_ID,
                "admins": [],
                "supportButtons": [],
                "lastDate": "",
                "submissionActive": True,
                "offMessage": "বর্তমানে ফাইল জমা নেওয়া বন্ধ আছে।"
            }
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
        return initial_data

    # Load existing
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Fix missing fields (Migration logic)
    needs_save = False
    if "supportButtons" not in data["config"]:
        data["config"]["supportButtons"] = []
        needs_save = True
    if "offMessage" not in data["config"]:
        data["config"]["offMessage"] = "Submission is closed."
        needs_save = True
    if "admins" not in data["config"]:
        data["config"]["admins"] = []
        needs_save = True
    
    if needs_save:
        save_data(data)
        print("🛠 Database Updated with New Fields!")
    
    return data

def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_admin(user_id, db):
    # Check if Main Admin OR in Admin List
    admins = db["config"].get("admins", [])
    return user_id == MAIN_ADMIN_ID or user_id in admins

def get_formatted_date():
    return datetime.datetime.now().strftime("%d/%m/%Y")

# --- TEXT TEXTS ---
USE_INFO_TEXT = {
    "bn": "ℹ️ <b>বট ব্যবহারের নিয়মাবলী (A to Z):</b>\n\n১. প্রথমে '📂 <b>Submit File</b>' বাটনে ক্লিক করুন।\n২. আপনার <b>.xlsx</b> (Excel) ফাইলটি আপলোড করুন।\n৩. এডমিন আপনার ফাইল চেক করে কনফার্ম করবেন।\n৪. কোনো সমস্যা হলে '📞 <b>Support</b>' বাটনে ক্লিক করে যোগাযোগ করুন।\n\n<i>ধন্যবাদ!</i>",
    "en": "ℹ️ <b>How to Use (A to Z):</b>\n\n1. First, click the '📂 <b>Submit File</b>' button.\n2. Upload your <b>.xlsx</b> (Excel) file.\n3. Admin will review and confirm your file.\n4. If you face any issues, click '📞 <b>Support</b>' to contact us.\n\n<i>Thank you!</i>"
}

# --- KEYBOARDS ---
def get_main_menu(user_id, db):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📂 Submit File")
    markup.row("👤 Profile", "ℹ️ Use Info")
    markup.row("📞 Support")
    if is_admin(user_id, db):
        markup.row("🛠 Admin Panel")
    return markup

def get_admin_keyboard(user_id, db):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    sub_status = "✅ Turn OFF Submit" if db["config"]["submissionActive"] else "⬇️ Turn ON Submit"
    
    # Rows
    if user_id == MAIN_ADMIN_ID:
        markup.row("⚠️ Send Update Alert")
        
    markup.row(sub_status, "🔄 Reset Date")
    markup.row("📢 Broadcast", "📩 Reply User")
    markup.row("🚫 Ban User", "✅ Unban User")
    markup.row("🆔 Set Channel ID", "🛠 Manage Support")
    
    if user_id == MAIN_ADMIN_ID:
        markup.row("➕ Add Admin", "➖ Remove Admin")
        
    markup.row("🔙 Back to Home")
    return markup

def get_cancel_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("❌ Cancel")
    return markup

def format_support_link(link):
    if link.startswith("http://") or link.startswith("https://"):
        return link
    if link.startswith("@"):
        return f"https://t.me/{link[1:]}"
    return f"https://t.me/{link}"

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    db = load_data()
    
    # Initialize user
    if str(chat_id) not in db["users"]:
        db["users"][str(chat_id)] = {"name": message.from_user.first_name, "banned": False, "locked": False}
        save_data(db)
    
    user_state[chat_id] = None
    bot.send_message(chat_id, "👋 <b>Welcome!</b>\nSelect an option:", parse_mode='HTML', reply_markup=get_main_menu(chat_id, db))

# FILE HANDLER (Handles .xlsx uploads)
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    chat_id = message.chat.id
    db = load_data()
    
    if user_state.get(chat_id) == 'WAITING_FOR_FILE':
        if not db["config"]["submissionActive"]:
            bot.send_message(chat_id, "⚠️ <b>Closed just now!</b>", parse_mode='HTML', reply_markup=get_main_menu(chat_id, db))
            user_state[chat_id] = None
            return

        file_name = message.document.file_name
        if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            forward_target = db["config"].get("submissionChannel", MAIN_ADMIN_ID)
            current_date = get_formatted_date()
            
            # Date change check
            if db["config"]["lastDate"] != current_date:
                bot.send_message(forward_target, f"📅 <b>New Date Started: {current_date}</b>", parse_mode='HTML')
                db["config"]["lastDate"] = current_date
                save_data(db)
            
            # Forward Logic
            try:
                fw = bot.forward_message(forward_target, chat_id, message.message_id)
                info_text = f"📄 <b>New File Received:</b>\nName: {message.from_user.first_name}\nID: <code>{chat_id}</code>"
                bot.send_message(forward_target, info_text, parse_mode='HTML', reply_to_message_id=fw.message_id)
                bot.send_message(chat_id, "✅ <b>File Submitted Successfully!</b>", parse_mode='HTML', reply_markup=get_main_menu(chat_id, db))
            except Exception as e:
                bot.send_message(chat_id, f"Error sending file: {e}")
                
            user_state[chat_id] = None
        else:
            bot.send_message(chat_id, "⚠️ <b>Invalid File!</b> Only .xlsx allowed.", parse_mode='HTML')

# TEXT HANDLER
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text
    db = load_data()

    # User Setup
    if str(chat_id) not in db["users"]:
        db["users"][str(chat_id)] = {"name": message.from_user.first_name, "banned": False, "locked": False}
        save_data(db)

    # Locked User Check
    user_data = db["users"][str(chat_id)]
    if user_data.get("locked", False) and chat_id != MAIN_ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 Refresh Bot", callback_data="restart_bot"))
        bot.send_message(chat_id, "⚠️ <b>System Updating...</b>\nPlease wait or refresh.", parse_mode='HTML', reply_markup=markup)
        return

    # --- CANCEL LOGIC ---
    if text == '❌ Cancel':
        current_st = user_state.get(chat_id, "")
        user_state[chat_id] = None
        temp_storage[chat_id] = None
        
        if current_st and current_st.startswith('ADMIN_'):
            bot.send_message(chat_id, "❌ Admin Action Cancelled.", reply_markup=get_admin_keyboard(chat_id, db))
        else:
            bot.send_message(chat_id, "❌ Cancelled.", reply_markup=get_main_menu(chat_id, db))
        return

    # --- HOME / BACK ---
    if text == '🔙 Back to Home':
        user_state[chat_id] = None
        bot.send_message(chat_id, "👋 <b>Welcome Back!</b>", parse_mode='HTML', reply_markup=get_main_menu(chat_id, db))
        return

    # --- SUBMIT FILE ---
    if text == '📂 Submit File':
        if not db["config"]["submissionActive"]:
            custom_msg = db["config"].get("offMessage", "Submission Closed.")
            bot.send_message(chat_id, f"⚠️ <b>Submission Closed!</b>\n\n{custom_msg}", parse_mode='HTML')
            return
        
        if user_data.get("banned", False):
            bot.send_message(chat_id, "🚫 <b>You are Banned.</b>", parse_mode='HTML')
            return
            
        user_state[chat_id] = 'WAITING_FOR_FILE'
        bot.send_message(chat_id, "📂 <b>Please upload your .xlsx file:</b>", parse_mode='HTML', reply_markup=get_cancel_keyboard())
        return

    # --- SUPPORT ---
    if text == '📞 Support':
        markup = types.InlineKeyboardMarkup()
        buttons = db["config"].get("supportButtons", [])
        
        if buttons:
            for btn in buttons:
                markup.add(types.InlineKeyboardButton(btn["name"], url=format_support_link(btn["link"])))
        else:
            markup.add(types.InlineKeyboardButton("💬 Contact Admin", url="https://t.me/YourUsername"))
            
        bot.send_message(chat_id, "📞 <b>Support Center</b>\nHow can we help you?", parse_mode='HTML', reply_markup=markup)
        return

    # --- PROFILE ---
    if text == '👤 Profile':
        bot.send_message(chat_id, f"👤 <b>User:</b> {user_data['name']}\n<b>ID:</b> <code>{chat_id}</code>", parse_mode='HTML')
        return

    # --- INFO ---
    if text == 'ℹ️ Use Info':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("English", callback_data="lang_en"))
        bot.send_message(chat_id, USE_INFO_TEXT["bn"], parse_mode='HTML', reply_markup=markup)
        return

    # ==========================
    # ADMIN PANEL LOGIC
    # ==========================
    if is_admin(chat_id, db):
        
        if text == '🛠 Admin Panel':
            bot.send_message(chat_id, "🛠 <b>Admin Dashboard</b>", parse_mode='HTML', reply_markup=get_admin_keyboard(chat_id, db))
            return

        # 1. SUBMISSION TOGGLE
        if text == '✅ Turn OFF Submit':
            user_state[chat_id] = 'ADMIN_SET_OFF_MSG'
            bot.send_message(chat_id, "💬 <b>Enter the OFF Message:</b>\n(Users will see this when closed)", parse_mode='HTML', reply_markup=get_cancel_keyboard())
            return
        
        if user_state.get(chat_id) == 'ADMIN_SET_OFF_MSG':
            db["config"]["offMessage"] = text
            db["config"]["submissionActive"] = False
            save_data(db)
            bot.send_message(chat_id, f"⚠️ <b>Submission turned OFF.</b>\nMsg: {text}", parse_mode='HTML', reply_markup=get_admin_keyboard(chat_id, db))
            user_state[chat_id] = None
            return

        if text == '⬇️ Turn ON Submit':
            db["config"]["submissionActive"] = True
            save_data(db)
            bot.send_message(chat_id, "✅ <b>Submission turned ON.</b>", reply_markup=get_admin_keyboard(chat_id, db))
            return

        # 2. MANAGE SUPPORT
        if text == '🛠 Manage Support':
            user_state[chat_id] = 'ADMIN_MANAGE_SUPPORT'
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("🆕 Add Button", "➖ Remove Button")
            markup.row("❌ Cancel")
            bot.send_message(chat_id, "<b>Support Button Manager:</b>", parse_mode='HTML', reply_markup=markup)
            return
            
        if text == '🆕 Add Button':
            user_state[chat_id] = 'ADMIN_ADD_SUP_NAME'
            bot.send_message(chat_id, "1. Enter Button Name (e.g. Whatsapp):", reply_markup=get_cancel_keyboard())
            return
            
        if user_state.get(chat_id) == 'ADMIN_ADD_SUP_NAME':
            temp_storage[chat_id] = {"name": text}
            user_state[chat_id] = 'ADMIN_ADD_SUP_LINK'
            bot.send_message(chat_id, "2. Enter Username or Link:", reply_markup=get_cancel_keyboard())
            return
            
        if user_state.get(chat_id) == 'ADMIN_ADD_SUP_LINK':
            new_btn = {"name": temp_storage[chat_id]["name"], "link": text}
            db["config"]["supportButtons"].append(new_btn)
            save_data(db)
            bot.send_message(chat_id, f"✅ <b>Added:</b> {new_btn['name']}", parse_mode='HTML', reply_markup=get_admin_keyboard(chat_id, db))
            user_state[chat_id] = None
            return
            
        if text == '➖ Remove Button':
            user_state[chat_id] = 'ADMIN_DEL_SUP'
            msg_list = "<b>Send the number to delete:</b>\n"
            buttons = db["config"].get("supportButtons", [])
            if buttons:
                for i, btn in enumerate(buttons):
                    msg_list += f"{i+1}. {btn['name']}\n"
            else:
                msg_list = "No buttons found."
            bot.send_message(chat_id, msg_list, parse_mode='HTML', reply_markup=get_cancel_keyboard())
            return
            
        if user_state.get(chat_id) == 'ADMIN_DEL_SUP':
            try:
                idx = int(text) - 1
                buttons = db["config"]["supportButtons"]
                if 0 <= idx < len(buttons):
                    removed = buttons.pop(idx)
                    save_data(db)
                    bot.send_message(chat_id, f"✅ <b>Deleted:</b> {removed['name']}", parse_mode='HTML', reply_markup=get_admin_keyboard(chat_id, db))
                else:
                    bot.send_message(chat_id, "❌ Invalid Number.", reply_markup=get_admin_keyboard(chat_id, db))
            except ValueError:
                bot.send_message(chat_id, "❌ Please send a number.")
            user_state[chat_id] = None
            return

        # 3. MAIN ADMIN ONLY
        if chat_id == MAIN_ADMIN_ID:
            if text == '⚠️ Send Update Alert':
                user_state[chat_id] = 'ADMIN_CONFIRM_ALERT'
                bot.send_message(chat_id, "Type <b>'yes'</b> to send alert to ALL users:", parse_mode='HTML', reply_markup=get_cancel_keyboard())
                return
            
            if user_state.get(chat_id) == 'ADMIN_CONFIRM_ALERT':
                if text.lower() == 'yes':
                    users = db["users"]
                    for uid in users:
                        if int(uid) != chat_id:
                            users[uid]["locked"] = True
                            markup = types.InlineKeyboardMarkup()
                            markup.add(types.InlineKeyboardButton("Update", callback_data="restart_bot"))
                            try:
                                bot.send_message(uid, "⚠️ <b>SYSTEM UPDATE</b>\nPlease update the bot.", parse_mode='HTML', reply_markup=markup)
                            except:
                                pass
                    save_data(db)
                    bot.send_message(chat_id, "✅ Alert Sent!", reply_markup=get_admin_keyboard(chat_id, db))
                else:
                    bot.send_message(chat_id, "❌ Cancelled.", reply_markup=get_admin_keyboard(chat_id, db))
                user_state[chat_id] = None
                return

            if text == '➕ Add Admin':
                user_state[chat_id] = 'ADMIN_ADD_ADMIN'
                bot.send_message(chat_id, "Enter User ID:", reply_markup=get_cancel_keyboard())
                return
            
            if user_state.get(chat_id) == 'ADMIN_ADD_ADMIN':
                try:
                    new_id = int(text)
                    if new_id not in db["config"]["admins"]:
                        db["config"]["admins"].append(new_id)
                        save_data(db)
                    bot.send_message(chat_id, "✅ Admin Added.", reply_markup=get_admin_keyboard(chat_id, db))
                except:
                    bot.send_message(chat_id, "Invalid ID.")
                user_state[chat_id] = None
                return

            if text == '➖ Remove Admin':
                user_state[chat_id] = 'ADMIN_REM_ADMIN'
                bot.send_message(chat_id, "Enter User ID:", reply_markup=get_cancel_keyboard())
                return

            if user_state.get(chat_id) == 'ADMIN_REM_ADMIN':
                try:
                    rem_id = int(text)
                    if rem_id in db["config"]["admins"]:
                        db["config"]["admins"].remove(rem_id)
                        save_data(db)
                        bot.send_message(chat_id, "✅ Admin Removed.", reply_markup=get_admin_keyboard(chat_id, db))
                    else:
                        bot.send_message(chat_id, "Admin not found.")
                except:
                    bot.send_message(chat_id, "Invalid ID.")
                user_state[chat_id] = None
                return

        # 4. GENERAL ADMIN TOOLS
        if text == '🔄 Reset Date':
            user_state[chat_id] = 'ADMIN_RESET_DATE'
            bot.send_message(chat_id, "Enter Password:", reply_markup=get_cancel_keyboard())
            return
            
        if user_state.get(chat_id) == 'ADMIN_RESET_DATE':
            if text == 'MTS@2026':
                db["config"]["lastDate"] = ""
                save_data(db)
                bot.send_message(chat_id, "✅ Date Reset.", reply_markup=get_admin_keyboard(chat_id, db))
            else:
                bot.send_message(chat_id, "❌ Wrong Password.", reply_markup=get_admin_keyboard(chat_id, db))
            user_state[chat_id] = None
            return

        if text == '📢 Broadcast':
            user_state[chat_id] = 'ADMIN_BROADCAST'
            bot.send_message(chat_id, "Enter Message:", reply_markup=get_cancel_keyboard())
            return
            
        if user_state.get(chat_id) == 'ADMIN_BROADCAST':
            users = db["users"]
            count = 0
            for uid in users:
                try:
                    bot.send_message(uid, f"📢 <b>NOTICE</b>\n{text}", parse_mode='HTML')
                    count += 1
                except:
                    pass
            bot.send_message(chat_id, f"✅ Broadcast Sent to {count} users.", reply_markup=get_admin_keyboard(chat_id, db))
            user_state[chat_id] = None
            return

        if text == '🆔 Set Channel ID':
            user_state[chat_id] = 'ADMIN_SET_CH'
            bot.send_message(chat_id, "Enter Channel ID (e.g., -100xxxx):", reply_markup=get_cancel_keyboard())
            return
            
        if user_state.get(chat_id) == 'ADMIN_SET_CH':
            try:
                db["config"]["submissionChannel"] = int(text)
            except:
                db["config"]["submissionChannel"] = text
            save_data(db)
            bot.send_message(chat_id, "✅ Channel Set.", reply_markup=get_admin_keyboard(chat_id, db))
            user_state[chat_id] = None
            return

        if text == '📩 Reply User':
            user_state[chat_id] = 'ADMIN_REP_1'
            bot.send_message(chat_id, "Enter User ID:", reply_markup=get_cancel_keyboard())
            return
            
        if user_state.get(chat_id) == 'ADMIN_REP_1':
            temp_storage[chat_id] = text
            user_state[chat_id] = 'ADMIN_REP_2'
            bot.send_message(chat_id, "Enter Message:", reply_markup=get_cancel_keyboard())
            return
            
        if user_state.get(chat_id) == 'ADMIN_REP_2':
            target_id = temp_storage[chat_id]
            try:
                bot.send_message(target_id, f"📩 <b>Admin Reply:</b>\n{text}", parse_mode='HTML')
                bot.send_message(chat_id, "✅ Sent.", reply_markup=get_admin_keyboard(chat_id, db))
            except Exception as e:
                bot.send_message(chat_id, f"❌ Failed: {e}", reply_markup=get_admin_keyboard(chat_id, db))
            user_state[chat_id] = None
            return

        if text == '🚫 Ban User':
            user_state[chat_id] = 'ADMIN_BAN'
            bot.send_message(chat_id, "Enter User ID:", reply_markup=get_cancel_keyboard())
            return
            
        if user_state.get(chat_id) == 'ADMIN_BAN':
            target_id = str(text)
            if target_id in db["users"]:
                db["users"][target_id]["banned"] = True
                save_data(db)
                bot.send_message(chat_id, "✅ Banned.", reply_markup=get_admin_keyboard(chat_id, db))
            else:
                bot.send_message(chat_id, "User not found.", reply_markup=get_admin_keyboard(chat_id, db))
            user_state[chat_id] = None
            return

        if text == '✅ Unban User':
            user_state[chat_id] = 'ADMIN_UNBAN'
            bot.send_message(chat_id, "Enter User ID:", reply_markup=get_cancel_keyboard())
            return

        if user_state.get(chat_id) == 'ADMIN_UNBAN':
            target_id = str(text)
            if target_id in db["users"]:
                db["users"][target_id]["banned"] = False
                save_data(db)
                bot.send_message(chat_id, "✅ Unbanned.", reply_markup=get_admin_keyboard(chat_id, db))
            else:
                bot.send_message(chat_id, "User not found.", reply_markup=get_admin_keyboard(chat_id, db))
            user_state[chat_id] = None
            return

# CALLBACK HANDLER
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    db = load_data()
    
    if call.data == 'lang_en':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Translate Bangla", callback_data="lang_bn"))
        bot.edit_message_text(USE_INFO_TEXT["en"], chat_id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
        
    elif call.data == 'lang_bn':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Translate English", callback_data="lang_en"))
        bot.edit_message_text(USE_INFO_TEXT["bn"], chat_id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
        
    elif call.data == 'restart_bot':
        if str(chat_id) in db["users"]:
            db["users"][str(chat_id)]["locked"] = False
            save_data(db)
        bot.send_message(chat_id, "✅ <b>Success!</b>", parse_mode='HTML', reply_markup=get_main_menu(chat_id, db))
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass

    bot.answer_callback_query(call.id)

# Run Bot
if __name__ == "__main__":
    bot.polling(non_stop=True)

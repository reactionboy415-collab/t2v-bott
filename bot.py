import logging
import asyncio
import httpx
import json
import random
import string
import os
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# --- RENDER PORT EXPOSE ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!", 200

def run_web():
    # Render default port 10000 use karta hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- BOT CONFIGURATION ---
API_TOKEN = '8300162852:AAHVS2PHyzyVSE-iLniP-yStvIph75SFxO4'
BASE_URL = "https://luca115-wan2-2-fp8da-aoti.hf.space/gradio_api"
NEG_PROMPT = "色调艳丽, 过曝, 静态, 细节模糊不清, 字幕, 风格, 作品, 画作, 画面, 静止, 整体发灰, 最差质量, 低质量, JPEG压缩残留, 丑陋 of, 残缺 of, 多余 of, 画得不好的手部, 畸形的, 毁容 of, 静止不动的画面, 杂乱 of, 三条腿, 倒着走"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def gen_hash():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=11))

async def fetch_video_url(prompt):
    session_hash = gen_hash()
    headers = {
        "x-gradio-user": "api",
        "origin": "https://upsampler.com",
        "referer": "https://upsampler.com/",
        "user-agent": "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36"
    }
    payload = {
        "data": [prompt, NEG_PROMPT, 5, 1, 3, 4, 42, True],
        "event_data": None, "fn_index": 0, "session_hash": session_hash
    }

    async with httpx.AsyncClient(http2=True, timeout=300.0) as client:
        try:
            await client.post(f"{BASE_URL}/queue/join", headers=headers, json=payload)
            async with client.stream("GET", f"{BASE_URL}/queue/data?session_hash={session_hash}", headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if "process_completed" in line:
                        json_data = json.loads(line.replace("data: ", ""))
                        return json_data['output']['data'][0]['video']['url']
        except Exception as e:
            logging.error(f"Fetch Error: {e}")
    return None

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("🎬 **Wan 2.1 Video Generator (Render Hosted)**\nSend me a prompt!")

@dp.message()
async def prompter(message: types.Message):
    if not message.text: return
    status_msg = await message.answer("⚡ **AI is thinking...**")
    try:
        video_url = await fetch_video_url(message.text)
        if video_url:
            await status_msg.edit_text("✅ Video Ready! Sending...")
            await message.answer_video(video=video_url, caption=f"🎬 {message.text}", supports_streaming=True)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Server busy. Try again.")
    except Exception as e:
        await status_msg.edit_text("💥 Error occurred.")

async def main():
    keep_alive() # Starts Flask on Port 10000
    print("--- RENDER SERVER & BOT STARTED ---")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

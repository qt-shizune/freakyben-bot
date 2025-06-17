import os
import random
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# ─── Imports for Dummy HTTP Server ──────────────────────────────────────────
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Voice note directory
VOICE_DIR = "voices"

# ─── Bot Commands ───────────────────────────────────────────────────────────
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Get started and see what I do"),
    ]
    await bot.set_my_commands(commands)

# ─── Start Command Handler ──────────────────────────────────────────────────
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Updates", url="https://t.me/WorkGlows"),
            InlineKeyboardButton(text="Support", url="https://t.me/TheCryptoElders")
        ],
        [
            InlineKeyboardButton(
                text="➕ Add Me To Your Group",
                url=f"https://t.me/{(await bot.me()).username}?startgroup=true"
            )
        ]
    ])
    welcome_text = (
        "<b>😎 Oh, look who showed up.</b>\n\n"
        "Try not to embarrass urself, champ.\n"
        "This place ain't for softies.\n"
        "Speak smart or stay silent 🐶"
    )
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# ─── Trigger on "ben" Keyword or Replies to Bot ─────────────────────────────
@dp.message()
async def ben_voice_reply(message: types.Message):
    try:
        text = message.text.lower().strip() if message.text else ""

        # Check if exactly "ben"
        if text == "ben":
            file_path = os.path.join(VOICE_DIR, "ben.ogg")
            if not os.path.isfile(file_path):
                await message.reply("⚠️ 'ben.ogg' not found in voices.")
                return
            voice = FSInputFile(file_path)
            await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
            await asyncio.sleep(1)
            await message.reply_voice(voice)
            return

        # Trigger if "ben" is in text or if replying to bot
        is_ben = "ben" in text
        is_reply_to_bot = (
            message.reply_to_message and message.reply_to_message.from_user.id == (await bot.me()).id
        )

        if not (is_ben or is_reply_to_bot):
            return  # Ignore non-trigger messages

        voice_files = [f for f in os.listdir(VOICE_DIR) if f.endswith(".ogg")]
        if not voice_files:
            await message.reply("⚠️ No voice files found.")
            return

        selected_file = random.choice(voice_files)
        file_path = os.path.join(VOICE_DIR, selected_file)
        voice = FSInputFile(file_path)

        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
        await asyncio.sleep(1)
        await message.reply_voice(voice)

    except Exception as e:
        await message.reply("❌ Something went wrong.")
        print(f"Error: {e}")

# ─── Dummy HTTP Server to Keep Render Happy ─────────────────────────────────
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"AFK bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def start_dummy_server():
    port = int(os.environ.get("PORT", 10000))  # Render injects this
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"Dummy server listening on port {port}")
    server.serve_forever()

# ─── Main Entry Point ───────────────────────────────────────────────────────
async def main():
    print("🚀 Bot is starting...")
    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    threading.Thread(target=start_dummy_server, daemon=True).start()
    asyncio.run(main())

# Standard library imports
import os
import random
import asyncio
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# Third party imports
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
UPDATES_URL = os.getenv("UPDATES_URL", "https://t.me/WorkGlows")
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/SoulMeetsHQ")

VOICE_DIR = "voices"

# Initialize bot components
dp = Dispatcher()
bot = None

# All bot messages dictionary
MESSAGES = {
    "start_welcome": (
        "<b>😎 Oh, look who showed up.</b>\n\n"
        "Try not to embarrass urself, champ.\n"
        "This place ain't for softies.\n"
        "Speak smart or stay silent 🐶"
    ),
    "ping_initial": "🛰️ Pinging...",
    "ping_response": '🏓 <a href="https://t.me/SoulMeetsHQ">Pong!</a> {latency}ms',
    "voice_not_found": "⚠️ 'ben.ogg' not found in voices directory.",
    "voices_dir_not_found": "⚠️ Voices directory not found.",
    "no_voice_files": "⚠️ No voice files found in voices directory.",
    "file_not_found": "⚠️ Voice file not found.",
    "general_error": "❌ Something went wrong while processing your request.",
    "server_health": "Telegram bot is running and healthy!"
}

# Set bot commands menu
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Get started and see what I do"),
    ]
    await bot.set_my_commands(commands)

# Handle start command
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    # Create inline keyboard buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Updates", url=UPDATES_URL),
            InlineKeyboardButton(text="Support", url=SUPPORT_URL)
        ],
        [
            InlineKeyboardButton(
                text="Add Me To Your Group",
                url=f"https://t.me/{(await message.bot.me()).username}?startgroup=true"
            )
        ]
    ])
    await message.answer(MESSAGES["start_welcome"], reply_markup=keyboard, parse_mode=ParseMode.HTML)

# Handle ping command latency test
@dp.message(Command("ping"))
async def ping_handler(message: types.Message):
    # Record start time
    start_time = time.time()
    ping_message = await message.reply(MESSAGES["ping_initial"])
    end_time = time.time()
    
    # Calculate latency in milliseconds
    latency = round((end_time - start_time) * 1000, 2)
    response_text = MESSAGES["ping_response"].format(latency=latency)
    
    # Edit message with result
    await ping_message.edit_text(
        response_text, 
        parse_mode=ParseMode.HTML, 
        disable_web_page_preview=True
    )

# Handle voice replies for ben
@dp.message()
async def ben_voice_reply(message: types.Message):
    try:
        text = message.text.lower().strip() if message.text else ""

        # Check for exact ben keyword
        if text == "ben":
            file_path = os.path.join(VOICE_DIR, "ben.ogg")
            if not os.path.isfile(file_path):
                await message.reply(MESSAGES["voice_not_found"])
                return

            # Send specific ben voice file
            voice = FSInputFile(file_path)
            await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
            await asyncio.sleep(1)
            await message.reply_voice(voice)
            return

        # Check for ben mentions
        is_ben_mentioned = "ben" in text
        is_reply_to_bot = False
        if message.reply_to_message:
            try:
                bot_info = await message.bot.me()
                is_reply_to_bot = message.reply_to_message.from_user.id == bot_info.id
            except Exception:
                pass

        # Only respond to triggers
        if not (is_ben_mentioned or is_reply_to_bot):
            return

        # Check voices directory exists
        if not os.path.exists(VOICE_DIR):
            await message.reply(MESSAGES["voices_dir_not_found"])
            return

        # Get all voice files
        voice_files = [f for f in os.listdir(VOICE_DIR) if f.endswith(".ogg")]
        if not voice_files:
            await message.reply(MESSAGES["no_voice_files"])
            return

        # Send random voice file
        selected_file = random.choice(voice_files)
        file_path = os.path.join(VOICE_DIR, selected_file)
        voice = FSInputFile(file_path)

        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
        await asyncio.sleep(1)
        await message.reply_voice(voice)

    except FileNotFoundError as e:
        await message.reply(MESSAGES["file_not_found"])
        print(f"Voice file not found: {e}")
    except Exception as e:
        await message.reply(MESSAGES["general_error"])
        print(f"Error in ben_voice_reply: {e}")

# HTTP server for deployment compatibility
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(MESSAGES["server_health"].encode())

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    # Suppress HTTP server logs
    def log_message(self, format, *args):
        pass

# Start background HTTP server
def start_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"🌐 HTTP server listening on port {port}")
    server.serve_forever()

# Main bot startup function
async def main():
    global bot
    print("🚀 Telegram bot is starting...")

    # Create voices directory
    if not os.path.exists(VOICE_DIR):
        os.makedirs(VOICE_DIR)
        print(f"📁 Created {VOICE_DIR} directory")
        print("ℹ️  Add your .ogg voice files to the voices directory")

    # Validate bot token
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set BOT_TOKEN in environment variables or .env file")
        return

    try:
        # Initialize bot instance
        bot = Bot(token=BOT_TOKEN)
        print("✅ Bot initialized successfully")

        # Set command menu
        await set_commands(bot)
        print("✅ Bot commands set successfully")

        # Start bot polling
        print("🔄 Starting bot polling...")
        await dp.start_polling(bot)

    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        if "Token is invalid" in str(e):
            print("ℹ️  Please check your BOT_TOKEN in the .env file")

# Entry point
if __name__ == "__main__":
    # Start HTTP server thread
    threading.Thread(target=start_dummy_server, daemon=True).start()
    asyncio.run(main())
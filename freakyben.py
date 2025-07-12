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
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Initialize dispatcher (bot will be initialized later with validation)
dp = Dispatcher()
bot = None

# Voice note directory
VOICE_DIR = "voices"

# ─── Bot Commands ───────────────────────────────────────────────────────────
async def set_commands(bot: Bot):
    """Set bot commands in Telegram menu"""
    commands = [
        BotCommand(command="start", description="Get started and see what I do"),
    ]
    await bot.set_my_commands(commands)

# ─── Start Command Handler ──────────────────────────────────────────────────
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    """Handle /start command with welcome message and inline keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Updates", url="https://t.me/WorkGlows"),
            InlineKeyboardButton(text="Support", url="https://t.me/SoulMeetsHQ")
        ],
        [
            InlineKeyboardButton(
                text="Add Me To Your Group",
                url=f"https://t.me/{(await message.bot.me()).username}?startgroup=true"
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
    """Handle voice responses for 'ben' keyword or replies to bot"""
    try:
        text = message.text.lower().strip() if message.text else ""

        # Check if exactly "ben" - send specific ben.ogg file
        if text == "ben":
            file_path = os.path.join(VOICE_DIR, "ben.ogg")
            if not os.path.isfile(file_path):
                await message.reply("⚠️ 'ben.ogg' not found in voices directory.")
                return
            
            voice = FSInputFile(file_path)
            # Simulate recording voice action
            await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
            await asyncio.sleep(1)
            await message.reply_voice(voice)
            return

        # Check if "ben" is mentioned in text or if replying to bot
        is_ben_mentioned = "ben" in text
        is_reply_to_bot = False
        if message.reply_to_message:
            try:
                bot_info = await message.bot.me()
                is_reply_to_bot = message.reply_to_message.from_user.id == bot_info.id
            except Exception:
                pass

        # Only respond to triggers to avoid spam
        if not (is_ben_mentioned or is_reply_to_bot):
            return

        # Check if voices directory exists
        if not os.path.exists(VOICE_DIR):
            await message.reply("⚠️ Voices directory not found.")
            return

        # Get all .ogg voice files
        voice_files = [f for f in os.listdir(VOICE_DIR) if f.endswith(".ogg")]
        if not voice_files:
            await message.reply("⚠️ No voice files found in voices directory.")
            return

        # Select random voice file
        selected_file = random.choice(voice_files)
        file_path = os.path.join(VOICE_DIR, selected_file)
        voice = FSInputFile(file_path)

        # Simulate recording voice action
        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
        await asyncio.sleep(1)
        await message.reply_voice(voice)

    except FileNotFoundError as e:
        await message.reply("⚠️ Voice file not found.")
        print(f"Voice file not found: {e}")
    except Exception as e:
        await message.reply("❌ Something went wrong while processing your request.")
        print(f"Error in ben_voice_reply: {e}")

# ─── Dummy HTTP Server for Deployment Compatibility ────────────────────────
class DummyHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks and deployment compatibility"""
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Telegram bot is running and healthy!")

    def do_HEAD(self):
        """Handle HEAD requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass

def start_dummy_server():
    """Start HTTP server for deployment platform compatibility"""
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"🌐 HTTP server listening on port {port}")
    server.serve_forever()

# ─── Main Entry Point ───────────────────────────────────────────────────────
async def main():
    """Main function to start the bot"""
    global bot
    print("🚀 Telegram bot is starting...")
    
    # Create voices directory if it doesn't exist
    if not os.path.exists(VOICE_DIR):
        os.makedirs(VOICE_DIR)
        print(f"📁 Created {VOICE_DIR} directory")
        print("ℹ️  Add your .ogg voice files to the voices directory")
    
    # Validate bot token
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set BOT_TOKEN in environment variables or .env file")
        return
    
    try:
        # Initialize bot with validated token
        bot = Bot(token=BOT_TOKEN)
        print("✅ Bot initialized successfully")
        
        # Set bot commands
        await set_commands(bot)
        print("✅ Bot commands set successfully")
        
        # Start polling
        print("🔄 Starting bot polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        if "Token is invalid" in str(e):
            print("ℹ️  Please check your BOT_TOKEN in the .env file")

if __name__ == "__main__":
    # Start dummy HTTP server in background thread for deployment compatibility
    threading.Thread(target=start_dummy_server, daemon=True).start()
    
    # Run the bot
    asyncio.run(main())
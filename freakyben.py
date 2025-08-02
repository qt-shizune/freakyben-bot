# Standard library imports
import os
import random
import asyncio
import threading
import time
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, any

# Third party imports
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, Message
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

# Color codes for logging
class Colors:
    BLUE = '\033[94m'      # INFO/WARNING
    GREEN = '\033[92m'     # DEBUG
    YELLOW = '\033[93m'    # INFO
    RED = '\033[91m'       # ERROR
    RESET = '\033[0m'      # Reset color
    BOLD = '\033[1m'       # Bold text

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to entire log messages"""

    COLORS = {
        'DEBUG': Colors.GREEN,
        'INFO': Colors.YELLOW,
        'WARNING': Colors.BLUE,
        'ERROR': Colors.RED,
    }

    def format(self, record):
        # Get the original formatted message
        original_format = super().format(record)

        # Get color based on log level
        color = self.COLORS.get(record.levelname, Colors.RESET)

        # Apply color to the entire message
        colored_format = f"{color}{original_format}{Colors.RESET}"

        return colored_format

# Configure logging with colors
def setup_colored_logging():
    """Setup colored logging configuration"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create colored formatter with enhanced format
    formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger

# Initialize colored logger
logger = setup_colored_logging()

def extract_user_info(msg: Message) -> Dict[str, any]:
    """Extract user and chat information from message"""
    logger.debug("🔍 Extracting user information from message")
    u = msg.from_user
    c = msg.chat
    info = {
        "user_id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "chat_id": c.id,
        "chat_type": c.type,
        "chat_title": c.title or c.first_name or "",
        "chat_username": f"@{c.username}" if c.username else "No Username",
        "chat_link": f"https://t.me/{c.username}" if c.username else "No Link",
    }
    logger.info(
        f"📑 User info extracted: {info['full_name']} (@{info['username']}) "
        f"[ID: {info['user_id']}] in {info['chat_title']} [{info['chat_id']}] {info['chat_link']}"
    )
    return info

def log_with_user_info(level: str, message: str, user_info: Dict[str, any]) -> None:
    """Log message with user information"""
    user_detail = (
        f"👤 {user_info['full_name']} (@{user_info['username']}) "
        f"[ID: {user_info['user_id']}] | "
        f"💬 {user_info['chat_title']} [{user_info['chat_id']}] "
        f"({user_info['chat_type']}) {user_info['chat_link']}"
    )
    full_message = f"{message} | {user_detail}"

    if level.upper() == "INFO":
        logger.info(full_message)
    elif level.upper() == "DEBUG":
        logger.debug(full_message)
    elif level.upper() == "WARNING":
        logger.warning(full_message)
    elif level.upper() == "ERROR":
        logger.error(full_message)
    else:
        logger.info(full_message)

# Set bot commands menu
async def set_commands(bot: Bot):
    logger.info("🎯 Setting up bot commands menu")
    commands = [
        BotCommand(command="start", description="Get started and see what I do"),
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Bot commands menu configured successfully")

# Handle start command
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_info = extract_user_info(message)
    log_with_user_info("info", "🚀 Start command received", user_info)
    
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
    log_with_user_info("info", "📤 Start message sent successfully", user_info)

# Handle ping command latency test
@dp.message(Command("ping"))
async def ping_handler(message: types.Message):
    user_info = extract_user_info(message)
    log_with_user_info("info", "🏓 Ping command received", user_info)
    
    # Record start time
    start_time = time.time()
    
    # Send as reply in groups only
    if message.chat.type in ["group", "supergroup"]:
        logger.debug(f"📨 Sending ping as reply in {message.chat.type}")
        ping_message = await message.reply(MESSAGES["ping_initial"])
    else:
        logger.debug("📨 Sending ping as regular message in private chat")
        ping_message = await message.answer(MESSAGES["ping_initial"])
    
    end_time = time.time()
    
    # Calculate latency in milliseconds
    latency = round((end_time - start_time) * 1000, 2)
    response_text = MESSAGES["ping_response"].format(latency=latency)
    logger.debug(f"⏱️ Calculated ping latency: {latency}ms")
    
    # Edit message with result
    await ping_message.edit_text(
        response_text, 
        parse_mode=ParseMode.HTML, 
        disable_web_page_preview=True
    )
    log_with_user_info("info", f"🏓 Pong sent with {latency}ms latency", user_info)

# Handle voice replies for ben
@dp.message()
async def ben_voice_reply(message: types.Message):
    try:
        text = message.text.lower().strip() if message.text else ""
        user_info = extract_user_info(message)

        # Check for exact ben keyword
        if text == "ben":
            logger.debug("🎯 Exact 'ben' keyword detected")
            file_path = os.path.join(VOICE_DIR, "ben.ogg")
            if not os.path.isfile(file_path):
                logger.warning(f"📁 ben.ogg file not found at {file_path}")
                await message.reply(MESSAGES["voice_not_found"])
                return

            # Send specific ben voice file
            logger.debug("🎤 Sending specific ben.ogg voice file")
            voice = FSInputFile(file_path)
            await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
            await asyncio.sleep(1)
            await message.reply_voice(voice)
            log_with_user_info("info", "🎤 Sent ben.ogg voice file", user_info)
            return

        # Check for ben mentions
        is_ben_mentioned = "ben" in text
        is_reply_to_bot = False
        if message.reply_to_message:
            try:
                bot_info = await message.bot.me()
                is_reply_to_bot = message.reply_to_message.from_user.id == bot_info.id
                logger.debug(f"🤖 Reply to bot detected: {is_reply_to_bot}")
            except Exception as e:
                logger.error(f"❌ Error checking bot reply: {e}")

        # Only respond to triggers
        if not (is_ben_mentioned or is_reply_to_bot):
            return

        logger.debug(f"🎯 Trigger detected - ben_mentioned: {is_ben_mentioned}, reply_to_bot: {is_reply_to_bot}")

        # Check voices directory exists
        if not os.path.exists(VOICE_DIR):
            logger.error(f"📁 Voices directory not found: {VOICE_DIR}")
            await message.reply(MESSAGES["voices_dir_not_found"])
            return

        # Get all voice files
        voice_files = [f for f in os.listdir(VOICE_DIR) if f.endswith(".ogg")]
        if not voice_files:
            logger.warning(f"📁 No .ogg files found in {VOICE_DIR}")
            await message.reply(MESSAGES["no_voice_files"])
            return

        # Send random voice file
        selected_file = random.choice(voice_files)
        logger.debug(f"🎲 Selected random voice file: {selected_file}")
        file_path = os.path.join(VOICE_DIR, selected_file)
        voice = FSInputFile(file_path)

        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
        await asyncio.sleep(1)
        await message.reply_voice(voice)
        log_with_user_info("info", f"🎤 Sent random voice file: {selected_file}", user_info)

    except FileNotFoundError as e:
        logger.error(f"📁 Voice file not found: {e}")
        await message.reply(MESSAGES["file_not_found"])
        log_with_user_info("error", f"📁 Voice file not found: {e}", user_info)
    except Exception as e:
        logger.error(f"❌ Error in ben_voice_reply: {e}")
        await message.reply(MESSAGES["general_error"])
        log_with_user_info("error", f"❌ General error in voice handler: {e}", user_info)

# HTTP server for deployment compatibility
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        logger.debug("🌐 HTTP GET request received")
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(MESSAGES["server_health"].encode())

    def do_HEAD(self):
        logger.debug("🌐 HTTP HEAD request received")
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    # Suppress HTTP server logs
    def log_message(self, format, *args):
        pass

# Start background HTTP server
def start_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🌐 Starting HTTP server on port {port}")
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    logger.info(f"🌐 HTTP server listening on port {port}")
    server.serve_forever()

# Main bot startup function
async def main():
    global bot
    logger.info("🚀 Telegram bot is starting...")

    # Create voices directory
    if not os.path.exists(VOICE_DIR):
        logger.info(f"📁 Creating voices directory: {VOICE_DIR}")
        os.makedirs(VOICE_DIR)
        logger.info(f"📁 Created {VOICE_DIR} directory")
        logger.info("ℹ️  Add your .ogg voice files to the voices directory")
    else:
        logger.info(f"📁 Voices directory exists: {VOICE_DIR}")

    # Validate bot token
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Bot token not configured")
        logger.error("❌ Please set BOT_TOKEN in environment variables or .env file")
        return

    logger.info("🔑 Bot token validated")

    try:
        # Initialize bot instance
        logger.info("🤖 Initializing bot instance")
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.me()
        logger.info(f"✅ Bot initialized successfully: @{bot_info.username} ({bot_info.full_name})")

        # Set command menu
        await set_commands(bot)

        # Start bot polling
        logger.info("🔄 Starting bot polling...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        if "Token is invalid" in str(e):
            logger.error("ℹ️  Please check your BOT_TOKEN in the .env file")

# Entry point
if __name__ == "__main__":
    logger.info("🎯 Bot entry point reached")
    
    # Start HTTP server thread
    logger.info("🧵 Starting HTTP server thread")
    threading.Thread(target=start_dummy_server, daemon=True).start()
    
    # Run the bot
    logger.info("🤖 Starting bot main function")
    asyncio.run(main())
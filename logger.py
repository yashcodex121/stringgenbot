import asyncio
from datetime import datetime

LOGGER_ID = None
BOT = None


# 🔹 Initialize Logger
def init_logger(bot, logger_id):
    global BOT, LOGGER_ID
    BOT = bot
    LOGGER_ID = int(logger_id)


# 🔹 Main Send Function
async def send_log(text: str):
    try:
        if BOT is None or LOGGER_ID is None:
            print("Logger not initialized")
            return

        await BOT.send_message(
            LOGGER_ID,
            text,
            parse_mode="html",
            disable_web_page_preview=True
        )

    except Exception as e:
        print("LOGGER ERROR:", e)


# 🔹 /start Log
async def log_start(user):
    try:
        text = f"""
<blockquote>
🚀 <b>New User Started Bot</b>

👤 <b>Name:</b> {user.first_name} {user.last_name or ""}
🆔 <b>User ID:</b> <code>{user.id}</code>
📛 <b>Username:</b> @{user.username if user.username else "No Username"}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</blockquote>
"""
        await send_log(text)

    except Exception as e:
        print("START LOG ERROR:", e)


# 🔹 String Generation Log
async def log_string(user):
    try:
        text = f"""
<blockquote>
🔐 <b>String Generated</b>

👤 <b>Name:</b> {user.first_name} {user.last_name or ""}
🆔 <b>User ID:</b> <code>{user.id}</code>
📛 <b>Username:</b> @{user.username if user.username else "No Username"}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</blockquote>
"""
        await send_log(text)

    except Exception as e:
        print("STRING LOG ERROR:", e)

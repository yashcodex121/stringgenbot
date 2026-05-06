from datetime import datetime

LOGGER_ID = None
BOT = None


# 🔹 INIT LOGGER
def init_logger(bot, logger_id):
    global BOT, LOGGER_ID
    BOT = bot
    LOGGER_ID = int(logger_id)


# 🔹 SAFE SEND LOG (AUTO FALLBACK)
async def send_log(text: str):
    if not BOT or not LOGGER_ID:
        print("⚠️ Logger not initialized")
        return

    try:
        # Try HTML format
        await BOT.send_message(
            chat_id=LOGGER_ID,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as e:
        print("LOGGER HTML ERROR:", e)

        try:
            # Fallback: plain text
            await BOT.send_message(
                chat_id=LOGGER_ID,
                text=text
            )
        except Exception as e2:
            print("LOGGER FAILED:", e2)


# 🔹 START LOG
async def log_start(user):
    try:
        text = f"""
🚀 <b>New User Started</b>

👤 <b>Name:</b> {user.first_name or ""} {user.last_name or ""}
🆔 <b>User ID:</b> <code>{user.id}</code>
📛 <b>Username:</b> @{user.username if user.username else "No Username"}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await send_log(text)

    except Exception as e:
        print("START LOG ERROR:", e)


# 🔹 STRING GENERATED LOG
async def log_string(user):
    try:
        text = f"""
🔐 <b>String Generated</b>

👤 <b>Name:</b> {user.first_name or ""} {user.last_name or ""}
🆔 <b>User ID:</b> <code>{user.id}</code>
📛 <b>Username:</b> @{user.username if user.username else "No Username"}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await send_log(text)

    except Exception as e:
        print("STRING LOG ERROR:", e)

from datetime import datetime

LOGGER_ID = None
BOT = None


# 🔹 INIT LOGGER
def init_logger(bot, logger_id):
    global BOT, LOGGER_ID
    BOT = bot

    try:
        LOGGER_ID = int(logger_id)
    except:
        LOGGER_ID = None
        print("❌ Invalid LOGGER_ID")


# 🔹 SAFE SEND LOG (QUOTE MODE)
async def send_log(text: str):
    if not BOT or not LOGGER_ID:
        print("⚠️ Logger not initialized")
        return

    try:
        # 👉 Telegram SAFE QUOTE (Markdown style)
        quote_text = "\n".join([f"> {line}" for line in text.split("\n")])

        await BOT.send_message(
            chat_id=LOGGER_ID,
            text=quote_text
        )

    except Exception as e:
        print("❌ LOGGER FAILED:", e)


# 🔹 START LOG
async def log_start(user):
    text = f"""
🚀 New User Started

👤 Name: {user.first_name or ""} {user.last_name or ""}
🆔 User ID: {user.id}
📛 Username: @{user.username if user.username else "No Username"}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    await send_log(text)


# 🔹 STRING LOG
async def log_string(user):
    text = f"""
🔐 String Generated

👤 Name: {user.first_name or ""} {user.last_name or ""}
🆔 User ID: {user.id}
📛 Username: @{user.username if user.username else "No Username"}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    await send_log(text)

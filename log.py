import traceback
from datetime import datetime

BOT = None
LOGGER_CHAT = None


def init_log(bot):
    global BOT
    BOT = bot


def set_log_chat(chat_id):
    global LOGGER_CHAT
    try:
        LOGGER_CHAT = int(chat_id)
    except:
        LOGGER_CHAT = None


async def send_log(text: str):
    try:
        if not BOT or not LOGGER_CHAT:
            print("Logger not set")
            return

        msg = f"""
<blockquote>
{text}
━━━━━━━━━━━━━━
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</blockquote>
"""

        await BOT.send_message(
            chat_id=LOGGER_CHAT,
            text=msg,
            parse_mode="html"
        )

    except Exception as e:
        print("LOG ERROR:", e)
        print(traceback.format_exc())


async def log_start(user):
    await send_log(f"🚀 START\n👤 {user.first_name}\n🆔 {user.id}")


async def log_string(user, typ):
    await send_log(f"🔥 STRING GENERATED\nTYPE: {typ}\nUSER: {user.id}")


async def log_broadcast(success, failed):
    await send_log(f"📢 BROADCAST\n✅ {success}\n❌ {failed}")


async def log_error(where, err):
    await send_log(f"❌ ERROR {where}\n{err}")

import traceback

LOGGER_CHAT = None
BOT = None


def init_auto_logger(bot):
    global BOT
    BOT = bot


def set_logger_chat(chat_id):
    global LOGGER_CHAT
    try:
        LOGGER_CHAT = int(chat_id)
    except:
        LOGGER_CHAT = None


async def auto_log(text: str):
    try:
        if BOT is None or LOGGER_CHAT is None:
            print("⚠️ Logger not set")
            return

        msg = f"""
<blockquote>
{text}
━━━━━━━━━━━━━━
</blockquote>
"""

        await BOT.send_message(
            chat_id=LOGGER_CHAT,
            text=msg,
            parse_mode="html",   # ✅ FIXED (lowercase)
            disable_web_page_preview=True
        )

    except Exception as e:
        print("❌ LOGGER ERROR:", e)
        print(traceback.format_exc())

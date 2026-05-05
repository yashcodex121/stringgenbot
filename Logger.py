import asyncio

LOGGER_ID = None
BOT = None

def init_logger(bot, logger_id):
    global BOT, LOGGER_ID
    BOT = bot
    LOGGER_ID = int(logger_id)

async def send_log(text: str):
    try:
        if BOT is None or LOGGER_ID is None:
            print("Logger not initialized")
            return

        await BOT.get_chat(LOGGER_ID)  # validate chat
        await BOT.send_message(LOGGER_ID, text)

    except Exception as e:
        print("LOGGER ERROR:", e)

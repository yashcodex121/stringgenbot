import os
import time
import asyncio
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient

from start import WELCOME_TEXT, start_buttons
from help import HELP_TEXT, help_buttons

from pyrogram_module import handle_pyro
from telethon_module import handle_tele

# 🔥 MODULES
from logger import init_logger, send_log
from broadcast import run_broadcast

# ---------------- ENV ---------------- #

def get_env(key):
    val = os.getenv(key)
    if not val:
        raise Exception(f"Missing ENV: {key}")
    return val

API_ID = int(get_env("API_ID"))
API_HASH = get_env("API_HASH")
BOT_TOKEN = get_env("BOT_TOKEN")
LOGGER_ID = int(get_env("LOGGER_ID"))
OWNER_ID = int(get_env("OWNER_ID"))
CHANNEL = "hellupdates1"

# ---------------- BOT ---------------- #

bot = Client(
    "string_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- DB ---------------- #

users_db = None

try:
    mongo = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    db = mongo["bot"]
    users_db = db["users"]
    print("✅ Mongo Connected")
except Exception as e:
    print("❌ Mongo Error:", e)

# ---------------- USER STATE ---------------- #

users = {}

# ---------------- START ---------------- #

@bot.on_message(filters.command("start"))
async def start(client, message):

    uid = message.from_user.id

    users[uid] = {
        "mode": None,
        "step": "choose",
        "time": time.time()
    }

    # SAVE USER
    if users_db:
        try:
            await users_db.update_one(
                {"user_id": uid},
                {"$set": {"user_id": uid}},
                upsert=True
            )
        except Exception as e:
            print("DB ERROR:", e)

    await send_log(f"🚀 NEW USER\nID: {uid}")

    await message.reply(
        WELCOME_TEXT,
        reply_markup=start_buttons(CHANNEL)
    )

# ---------------- CALLBACK ---------------- #

@bot.on_callback_query()
async def cb(client, cb):

    uid = cb.from_user.id

    if cb.data == "pyro":
        users[uid] = {"mode": "pyro", "step": "api_id", "time": time.time()}
        return await cb.message.edit("🍂 Send API_ID (Pyrogram)")

    elif cb.data == "tele":
        users[uid] = {"mode": "tele", "step": "api_id", "time": time.time()}
        return await cb.message.edit("🍂 Send API_ID (Telethon)")

    elif cb.data == "help":
        return await cb.message.edit(HELP_TEXT, reply_markup=help_buttons())

    elif cb.data == "back":
        return await cb.message.edit(
            WELCOME_TEXT,
            reply_markup=start_buttons(CHANNEL)
        )

    elif cb.data == "verify":
        return await cb.answer("❌ Join channel first", show_alert=True)

# ---------------- MAIN HANDLER ---------------- #

@bot.on_message(filters.private & filters.text)
async def handler(client, message):

    uid = message.from_user.id
    data = users.get(uid)

    if not data:
        return

    try:
        if data.get("mode") == "pyro":
            await handle_pyro(client, message, data, users, send_log, bot)

        elif data.get("mode") == "tele":
            await handle_tele(client, message, data, users, send_log, bot)

    except Exception as e:
        await send_log(f"❌ Handler Error:\n{e}")

# ---------------- BROADCAST ---------------- #

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_handler(client, message):

    if not users_db:
        return await message.reply("❌ DB not connected")

    if not message.reply_to_message:
        return await message.reply("❌ Reply to a message to broadcast")

    await message.reply("📢 Broadcasting started...")

    await run_broadcast(bot, users_db, message, OWNER_ID)

# ---------------- LOGGER INIT ---------------- #

async def startup():
    await init_logger(bot, LOGGER_ID)
    print("✅ Logger Initialized")

# ---------------- RUN ---------------- #

async def main():
    print("🚀 Bot Starting...")
    await bot.start()
    await startup()
    print("✅ Bot Started Successfully")
    await idle()

from pyrogram import idle

if __name__ == "__main__":
    asyncio.run(main())

import os
import time
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient

from start import WELCOME_TEXT, start_buttons
from help import HELP_TEXT, help_buttons
from pyrogram_module import handle_pyro
from telethon_module import handle_tele

# ---------------- ENV ---------------- #

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOGGER_ID = int(os.getenv("LOGGER_ID"))
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL = "hellupdates1"

bot = Client("string_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- DB ---------------- #

users_db = None
try:
    mongo = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    users_db = mongo["bot"]["users"]
except:
    pass

users = {}

# ---------------- LOGGER ---------------- #

async def send_log(text):
    try:
        await bot.send_message(LOGGER_ID, text)
    except:
        print("Logger failed")

# ---------------- START ---------------- #

@bot.on_message(filters.command("start"))
async def start(client, message):

    uid = message.from_user.id

    users[uid] = {"step": "choose", "time": time.time()}

    await send_log(f"🚀 START\nID: {uid}")

    await message.reply(
        WELCOME_TEXT,
        reply_markup=start_buttons(CHANNEL)
    )

# ---------------- CALLBACK ---------------- #

@bot.on_callback_query()
async def cb(client, cb):

    uid = cb.from_user.id

    # 🔥 PYROGRAM
    if cb.data == "pyro":
        users[uid] = {"mode": "pyro", "step": "api_id", "time": time.time()}
        return await cb.message.edit("🍂 Send API_ID (Pyrogram)")

    # 🔥 TELETHON
    if cb.data == "tele":
        users[uid] = {"mode": "tele", "step": "api_id", "time": time.time()}
        return await cb.message.edit("🍂 Send API_ID (Telethon)")

    # 🔥 HELP MENU
    if cb.data == "help":
        return await cb.message.edit(HELP_TEXT, reply_markup=help_buttons())

    # 🔙 BACK BUTTON
    if cb.data == "back":
        return await cb.message.edit(
            WELCOME_TEXT,
            reply_markup=start_buttons(CHANNEL)
        )

    # 🔥 VERIFY (OPTIONAL)
    if cb.data == "verify":
        return await cb.answer("Join channel first", show_alert=True)

# ---------------- HANDLER ---------------- #

@bot.on_message(filters.private & filters.text)
async def handler(client, message):

    uid = message.from_user.id
    data = users.get(uid)

    if not data:
        return

    if data["mode"] == "pyro":
        await handle_pyro(client, message, data, users, send_log, bot)

    elif data["mode"] == "tele":
        await handle_tele(client, message, data, users, send_log, bot)

# ---------------- BROADCAST ---------------- #

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):

    if not users_db:
        return await message.reply("DB not connected")

    success = failed = 0

    if message.reply_to_message:
        msg = message.reply_to_message

        async for u in users_db.find():
            try:
                await msg.copy(u["user_id"])
                success += 1
            except:
                failed += 1

    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]

        async for u in users_db.find():
            try:
                await bot.send_message(u["user_id"], text)
                success += 1
            except:
                failed += 1

    else:
        return await message.reply("Reply or send text")

    await send_log(f"📢 BROADCAST\n✅ {success} ❌ {failed}")

    await message.reply(f"Done\nSuccess: {success}\nFailed: {failed}")

# ---------------- RUN ---------------- #

bot.run()

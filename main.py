import os
import time
from pyrogram import Client, filters, idle
from motor.motor_asyncio import AsyncIOMotorClient

from start import WELCOME_TEXT, start_buttons
from help import HELP_TEXT, help_buttons

from pyrogram_module import handle_pyro
from telethon_module import handle_tele

from auto_logger import start_log, string_log, error_log
from log import init_log, set_log_chat
from broadcast import run_broadcast

# ---------------- BOT ---------------- #

bot = Client(
    "string_bot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)

OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL = "hellupdates1"

# ---------------- DB ---------------- #

mongo = AsyncIOMotorClient(os.getenv("MONGO_URL"))
users_db = mongo["bot"]["users"]

users = {}

# ---------------- STARTUP ---------------- #

async def startup():
    init_log(bot)
    print("Logger Ready")

# ---------------- START ---------------- #

@bot.on_message(filters.private & filters.command("start"))
async def start(client, message):

    user = message.from_user

    users[user.id] = {"mode": None, "step": "choose", "time": time.time()}

    await message.reply(WELCOME_TEXT, reply_markup=start_buttons(CHANNEL))

    await start_log(user)

# ---------------- SETLOG ---------------- #

@bot.on_message(filters.command("setlog") & filters.user(OWNER_ID))
async def setlog(client, message):
    set_log_chat(message.chat.id)
    await message.reply("Logger Set")

# ---------------- CALLBACK ---------------- #

@bot.on_callback_query()
async def cb(client, cb):

    uid = cb.from_user.id

    if cb.data == "pyro":
        users[uid] = {"mode": "pyro", "step": "api_id"}
        await cb.message.edit("Send API_ID")

    elif cb.data == "tele":
        users[uid] = {"mode": "tele", "step": "api_id"}
        await cb.message.edit("Send API_ID")

# ---------------- MESSAGE ---------------- #

@bot.on_message(filters.private & filters.text)
async def msg(client, message):

    uid = message.from_user.id
    data = users.get(uid)

    if not data:
        return

    if data["mode"] == "pyro":
        await handle_pyro(client, message, data, users, string_log, bot)

    elif data["mode"] == "tele":
        await handle_tele(client, message, data, users, string_log, bot)

# ---------------- BROADCAST ---------------- #

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):

    await run_broadcast(bot, users_db, message, OWNER_ID)
    await message.reply("Broadcast Done")

# ---------------- RUN ---------------- #

print("Bot Starting...")

bot.start()
bot.loop.run_until_complete(startup())

print("Bot Running")

idle()

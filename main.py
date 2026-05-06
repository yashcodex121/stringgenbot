import os
import time
import traceback
from pyrogram import Client, filters, idle

from auto_logger import (
    init_auto_logger,
    set_logger_chat,
    auto_log,
    format_user
)

# ---------------- BOT ---------------- #

bot = Client(
    "string_bot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)

OWNER_ID = int(os.getenv("OWNER_ID"))

# ---------------- INIT ---------------- #

async def startup():
    init_auto_logger(bot)
    print("✅ Auto Logger Ready")

# ---------------- START ---------------- #

@bot.on_message(filters.command("start"))
async def start(client, message):

    user = message.from_user
    name, uid, username, mention = format_user(user)

    await auto_log(
        f"🚀 NEW USER STARTED\n"
        f"👤 Name: {name}\n"
        f"🆔 ID: {uid}\n"
        f"📛 Username: {username}\n"
        f"🔗 {mention}"
    )

    await message.reply("Bot Started ✅")

# ---------------- SET LOGGER ---------------- #

@bot.on_message(filters.command("setlog") & filters.user(OWNER_ID))
async def setlog(client, message):
    set_logger_chat(message.chat.id)
    await message.reply("✅ This group is now LOGGER")

# ---------------- PYRO LOG EXAMPLE ---------------- #

@bot.on_message(filters.command("pyro_done"))
async def pyro_done(client, message):

    user = message.from_user
    name, uid, username, mention = format_user(user)

    await auto_log(
        f"🔥 PYRO STRING GENERATED\n"
        f"👤 Name: {name}\n"
        f"🆔 ID: {uid}\n"
        f"📛 Username: {username}\n"
        f"🔗 {mention}"
    )

    await message.reply("Pyro Done ✅")

# ---------------- TELE LOG EXAMPLE ---------------- #

@bot.on_message(filters.command("tele_done"))
async def tele_done(client, message):

    user = message.from_user
    name, uid, username, mention = format_user(user)

    await auto_log(
        f"🔐 TELETHON STRING GENERATED\n"
        f"👤 Name: {name}\n"
        f"🆔 ID: {uid}\n"
        f"📛 Username: {username}\n"
        f"🔗 {mention}"
    )

    await message.reply("Tele Done ✅")

# ---------------- ERROR SAFE ---------------- #

@bot.on_message(filters.command("test_error"))
async def test_error(client, message):
    try:
        1 / 0
    except Exception:
        await auto_log(
            f"❌ ERROR OCCURED\n{traceback.format_exc()}"
        )

# ---------------- RUN ---------------- #

print("🚀 Bot Starting...")

bot.start()
bot.loop.run_until_complete(startup())

print("✅ Bot Running")

idle()

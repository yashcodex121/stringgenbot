import os
import time
from pyrogram import Client, filters, idle

from start import WELCOME_TEXT, start_buttons
from help import HELP_TEXT, help_buttons

from pyrogram_module import handle_pyro
from telethon_module import handle_tele

# ---------------- BOT ---------------- #

bot = Client(
    "string_bot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)

CHANNEL = "hellupdates1"

users = {}

# ---------------- START ---------------- #

@bot.on_message(filters.private & filters.command("start"))
async def start(client, message):

    user = message.from_user

    users[user.id] = {
        "mode": None,
        "step": "choose",
        "time": time.time()
    }

    await message.reply(
        WELCOME_TEXT,
        reply_markup=start_buttons(CHANNEL)
    )

# ---------------- HELP ---------------- #

@bot.on_message(filters.private & filters.command("help"))
async def help_cmd(client, message):

    await message.reply(
        HELP_TEXT,
        reply_markup=help_buttons()
    )

# ---------------- CALLBACK ---------------- #

@bot.on_callback_query()
async def cb(client, cb):

    uid = cb.from_user.id

    if cb.data == "pyro":
        users[uid] = {
            "mode": "pyro",
            "step": "api_id"
        }

        await cb.message.edit("Send API_ID")

    elif cb.data == "tele":
        users[uid] = {
            "mode": "tele",
            "step": "api_id"
        }

        await cb.message.edit("Send API_ID")

# ---------------- MESSAGE ---------------- #

@bot.on_message(filters.private & filters.text)
async def msg(client, message):

    uid = message.from_user.id
    data = users.get(uid)

    if not data:
        return

    if data["mode"] == "pyro":
        await handle_pyro(
            client,
            message,
            data,
            users,
            bot
        )

    elif data["mode"] == "tele":
        await handle_tele(
            client,
            message,
            data,
            users,
            bot
        )

# ---------------- RUN ---------------- #

print("Bot Starting...")

bot.start()

print("Bot Running")

idle()

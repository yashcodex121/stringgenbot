import os
import time
import traceback
from pyrogram import Client, filters, idle
from motor.motor_asyncio import AsyncIOMotorClient

from start import WELCOME_TEXT, start_buttons
from help import HELP_TEXT, help_buttons

from pyrogram_module import handle_pyro
from telethon_module import handle_tele

from auto_logger import init_auto_logger, set_logger_chat, auto_log

# ---------------- ENV ---------------- #

def get_env(key):
    val = os.getenv(key)
    if not val:
        raise Exception(f"Missing ENV: {key}")
    return val


API_ID = int(get_env("API_ID"))
API_HASH = get_env("API_HASH")
BOT_TOKEN = get_env("BOT_TOKEN")
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
    users_db = mongo["bot"]["users"]
    print("✅ Mongo Connected")
except Exception as e:
    print("❌ Mongo Error:", e)

# ---------------- USER STATE ---------------- #

users = {}

# ---------------- STARTUP ---------------- #

async def startup():
    init_auto_logger(bot)
    print("✅ Auto Logger Ready")

# ---------------- START COMMAND ---------------- #

@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    try:
        user = message.from_user

        users[user.id] = {
            "mode": None,
            "step": "choose",
            "time": time.time()
        }

        await message.reply("🚀 Bot Started Successfully")

        await auto_log(
            f"🚀 NEW USER STARTED\n"
            f"👤 Name: {user.first_name}\n"
            f"🆔 ID: {user.id}\n"
            f"📛 Username: @{user.username or 'None'}"
        )

    except Exception:
        print(traceback.format_exc())

# ---------------- SET LOGGER ---------------- #

@bot.on_message(filters.command("setlog") & filters.user(OWNER_ID))
async def setlog_handler(client, message):
    set_logger_chat(message.chat.id)
    await message.reply("✅ Logger Activated for this group")

# ---------------- CALLBACK ---------------- #

@bot.on_callback_query()
async def callback_handler(client, cb):
    try:
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
            return await cb.message.edit(WELCOME_TEXT, reply_markup=start_buttons(CHANNEL))

    except Exception:
        print(traceback.format_exc())

# ---------------- MESSAGE HANDLER ---------------- #

@bot.on_message(filters.private & filters.text)
async def message_handler(client, message):
    try:
        uid = message.from_user.id
        data = users.get(uid)

        if not data:
            return

        if data.get("mode") == "pyro":
            await handle_pyro(client, message, data, users, auto_log, bot)

        elif data.get("mode") == "tele":
            await handle_tele(client, message, data, users, auto_log, bot)

    except Exception:
        print(traceback.format_exc())

# ---------------- BROADCAST ---------------- #

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_handler(client, message):
    try:
        if not users_db:
            return await message.reply("❌ DB not connected")

        if not message.reply_to_message:
            return await message.reply("❌ Reply to message")

        await message.reply("📢 Broadcasting...")

        users_list = await users_db.find().to_list(length=100000)

        success = 0
        failed = 0

        for user in users_list:
            try:
                await bot.send_message(user["user_id"], message.reply_to_message.text)
                success += 1
            except:
                failed += 1

        await auto_log(
            f"📢 BROADCAST DONE\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}"
        )

    except Exception:
        print(traceback.format_exc())

# ---------------- RUN ---------------- #

print("🚀 Bot Starting...")

bot.start()
bot.loop.run_until_complete(startup())

print("✅ Bot Running")

idle()

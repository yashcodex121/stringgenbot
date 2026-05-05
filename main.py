import os
import time
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient

from start import WELCOME_TEXT, start_buttons
from help import HELP_TEXT, help_buttons
from pyrogram_module import handle_pyro
from telethon_module import handle_tele

# ---------------- ENV SAFE ---------------- #

def get_env(key):
    value = os.getenv(key)
    if not value:
        raise Exception(f"❌ Missing ENV: {key}")
    return value

API_ID = int(get_env("API_ID"))
API_HASH = get_env("API_HASH")
BOT_TOKEN = get_env("BOT_TOKEN")
LOGGER_ID = int(get_env("LOGGER_ID"))
OWNER_ID = int(get_env("OWNER_ID"))
CHANNEL = "hellupdates1"

bot = Client("string_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- DB ---------------- #

users_db = None

try:
    mongo = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    users_db = mongo["bot"]["users"]
    print("✅ Mongo Connected")
except Exception as e:
    print("❌ Mongo Error:", e)

users = {}

# ---------------- LOGGER ---------------- #

async def send_log(text):
    try:
        await bot.send_message(chat_id=LOGGER_ID, text=text)
    except Exception as e:
        print("LOGGER ERROR:", e)

# ---------------- START ---------------- #

@bot.on_message(filters.command("start"))
async def start(client, message):

    uid = message.from_user.id

    users[uid] = {"mode": None, "step": "choose", "time": time.time()}

    # 🔥 SAFE MONGO CHECK (IMPORTANT FIX)
    if users_db is not None:
        try:
            await users_db.update_one(
                {"user_id": uid},
                {"$set": {"user_id": uid}},
                upsert=True
            )
        except Exception as e:
            print("DB ERROR:", e)

    await send_log(f"🚀 START\nID: {uid}")

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

    if cb.data == "tele":
        users[uid] = {"mode": "tele", "step": "api_id", "time": time.time()}
        return await cb.message.edit("🍂 Send API_ID (Telethon)")

    if cb.data == "help":
        return await cb.message.edit(HELP_TEXT, reply_markup=help_buttons())

    if cb.data == "back":
        return await cb.message.edit(
            WELCOME_TEXT,
            reply_markup=start_buttons(CHANNEL)
        )

    if cb.data == "verify":
        return await cb.answer("Join channel first", show_alert=True)

# ---------------- HANDLER ---------------- #

@bot.on_message(filters.private & filters.text)
async def handler(client, message):

    uid = message.from_user.id
    data = users.get(uid)

    if not data:
        return

    if data.get("mode") == "pyro":
        await handle_pyro(client, message, data, users, send_log, bot)

    elif data.get("mode") == "tele":
        await handle_tele(client, message, data, users, send_log, bot)

# ---------------- BROADCAST ---------------- #

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):

    # 🔥 SAFE CHECK FIX (IMPORTANT)
    if users_db is None:
        return await message.reply("❌ DB not connected")

    users_list = await users_db.find().to_list(length=10000)

    if not users_list:
        return await message.reply("❌ No users found")

    success = 0
    failed = 0

    # ---------------- REPLY BROADCAST ---------------- #
    if message.reply_to_message:

        msg = message.reply_to_message

        for u in users_list:
            try:
                await msg.copy(u["user_id"])
                success += 1
            except:
                failed += 1

    # ---------------- TEXT BROADCAST ---------------- #
    elif len(message.command) > 1:

        text = message.text.split(None, 1)[1]

        for u in users_list:
            try:
                await bot.send_message(u["user_id"], text)
                success += 1
            except:
                failed += 1

    else:
        return await message.reply("Reply or send text")

    await send_log(f"""
📢 BROADCAST DONE

✅ Success: {success}
❌ Failed: {failed}
""")

    await message.reply(f"""
✔ DONE

✅ {success}
❌ {failed}
""")

# ---------------- RUN ---------------- #

print("🚀 Bot Started Successfully")
bot.run()

import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
from telethon.sessions import StringSession
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from motor.motor_asyncio import AsyncIOMotorClient

from start import WELCOME_TEXT, start_buttons
from help import HELP_TEXT, help_buttons

# ---------------- CONFIG ---------------- #

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "hellupdates1"   # already added
OWNER_ID = int(os.getenv("OWNER_ID"))  # numeric id dalna
LOGGER_ID = int(os.getenv("LOGGER_ID"))
MONGO_URL = os.getenv("MONGO_URL")

bot = Client("string_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- DB ---------------- #

users_db = None
try:
    mongo = AsyncIOMotorClient(MONGO_URL)
    users_db = mongo["bot"]["users"]
except:
    pass

users = {}

# ---------------- FORCE JOIN ---------------- #

async def is_joined(client, user_id):
    try:
        await client.get_chat_member(CHANNEL, user_id)
        return True
    except:
        return False

# ---------------- START ---------------- #

@bot.on_message(filters.command("start"))
async def start(client, message):

    if users_db is not None:
        await users_db.update_one(
            {"user_id": message.from_user.id},
            {"$set": {"user_id": message.from_user.id}},
            upsert=True
        )

    if not await is_joined(client, message.from_user.id):
        return await message.reply(
            "⚠️ Join channel first",
            reply_markup=start_buttons(CHANNEL)
        )

    await message.reply(WELCOME_TEXT, reply_markup=start_buttons(CHANNEL))

# ---------------- HELP ---------------- #

@bot.on_callback_query(filters.regex("help"))
async def help_menu(client, cb):
    await cb.message.edit(HELP_TEXT, reply_markup=help_buttons())

@bot.on_callback_query(filters.regex("back"))
async def back_menu(client, cb):
    await cb.message.edit(WELCOME_TEXT, reply_markup=start_buttons(CHANNEL))

# ---------------- VERIFY ---------------- #

@bot.on_callback_query(filters.regex("verify"))
async def verify(client, cb):
    if await is_joined(client, cb.from_user.id):
        await cb.answer("✅ Verified!", show_alert=True)
    else:
        await cb.answer("❌ Join channel first", show_alert=True)

# ---------------- SELECT ---------------- #

@bot.on_callback_query(filters.regex("pyro|tele"))
async def choose(client, cb):
    users[cb.from_user.id] = {
        "type": cb.data,
        "time": time.time()
    }
    await cb.message.edit("📥 Send API_ID")

# ---------------- BROADCAST ---------------- #

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):
    msg = message.text.split(None, 1)[1]

    async for user in users_db.find():
        try:
            await bot.send_message(user["user_id"], msg)
        except:
            pass

    await message.reply("✅ Broadcast Done")

# ---------------- HANDLER ---------------- #

@bot.on_message(filters.private & filters.text)
async def handler(client, message):

    user = users.get(message.from_user.id)
    if not user:
        return

    if time.time() - user["time"] > 120:
        users.pop(message.from_user.id)
        return await message.reply("⌛ Timeout")

    try:

        if "api_id" not in user:
            user["api_id"] = int(message.text)
            return await message.reply("Send API_HASH")

        elif "api_hash" not in user:
            user["api_hash"] = message.text
            return await message.reply("Send Phone")

        elif "phone" not in user:
            user["phone"] = message.text

            if user["type"] == "pyro":
                app = Client("temp", api_id=user["api_id"], api_hash=user["api_hash"])
                await app.connect()
                code = await app.send_code(user["phone"])
                user["app"] = app
                user["hash"] = code.phone_code_hash
            else:
                client_t = TelegramClient(StringSession(), user["api_id"], user["api_hash"])
                await client_t.connect()
                await client_t.send_code_request(user["phone"])
                user["client"] = client_t

            return await message.reply("📩 OTP bhejo")

        elif "otp" not in user:

            try:
                if user["type"] == "pyro":
                    await user["app"].sign_in(user["phone"], user["hash"], message.text)
                else:
                    await user["client"].sign_in(user["phone"], message.text)

            except (SessionPasswordNeeded, SessionPasswordNeededError):
                user["need_pass"] = True
                return await message.reply("🔐 2FA Password bhejo")

            if user["type"] == "pyro":
                string = await user["app"].export_session_string()
                await user["app"].disconnect()
            else:
                string = user["client"].session.save()
                await user["client"].disconnect()

            await message.reply_document(
                document=bytes(string, "utf-8"),
                file_name="string.txt"
            )

            await bot.send_message(LOGGER_ID, f"New Session: {message.from_user.id}")

        elif user.get("need_pass"):

            if user["type"] == "pyro":
                await user["app"].check_password(message.text)
                string = await user["app"].export_session_string()
                await user["app"].disconnect()
            else:
                await user["client"].sign_in(password=message.text)
                string = user["client"].session.save()
                await user["client"].disconnect()

            await message.reply_document(
                document=bytes(string, "utf-8"),
                file_name="string.txt"
            )

            await bot.send_message(LOGGER_ID, f"2FA Session: {message.from_user.id}")

    except Exception as e:
        await message.reply(f"❌ Error: {e}")

    users.pop(message.from_user.id, None)

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    print("🚀 Bot Started...")
    bot.run()

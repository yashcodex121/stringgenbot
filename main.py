import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon.sessions import StringSession
from telethon import TelegramClient
from motor.motor_asyncio import AsyncIOMotorClient

# ---------------- CONFIG ---------------- #

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")
OWNER_ID = int(os.getenv("OWNER_ID"))
MONGO_URL = os.getenv("MONGO_URL")

# ---------------- BOT INIT ---------------- #

bot = Client(
    "string_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- MONGO SAFE INIT ---------------- #

try:
    mongo = AsyncIOMotorClient(MONGO_URL)
    db = mongo["bot"]
    users_db = db["users"]
except Exception as e:
    print("❌ MongoDB Error:", e)
    users_db = None

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

    if users_db:
        await users_db.update_one(
            {"user_id": message.from_user.id},
            {"$set": {"user_id": message.from_user.id}},
            upsert=True
        )

    if not await is_joined(client, message.from_user.id):
        return await message.reply(
            "⚠️ Join channel first",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join", url=f"https://t.me/{CHANNEL}")],
                [InlineKeyboardButton("Verify", callback_data="verify")]
            ])
        )

    await message.reply(
        "🔥 Choose Generator",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Pyrogram", callback_data="pyro")],
            [InlineKeyboardButton("⚡ Telethon", callback_data="tele")]
        ])
    )

# ---------------- VERIFY ---------------- #

@bot.on_callback_query(filters.regex("verify"))
async def verify(client, cb):
    if await is_joined(client, cb.from_user.id):
        await cb.message.edit(
            "✅ Verified!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 Pyrogram", callback_data="pyro")],
                [InlineKeyboardButton("⚡ Telethon", callback_data="tele")]
            ])
        )
    else:
        await cb.answer("❌ Join nahi kiya!", show_alert=True)

# ---------------- SELECT TYPE ---------------- #

@bot.on_callback_query(filters.regex("pyro|tele"))
async def choose(client, cb):
    users[cb.from_user.id] = {
        "type": cb.data,
        "time": time.time()
    }
    await cb.message.edit("📥 Send API_ID\n\n/cancel to stop")

# ---------------- CANCEL ---------------- #

@bot.on_message(filters.command("cancel"))
async def cancel(client, message):
    users.pop(message.from_user.id, None)
    await message.reply("❌ Cancelled")

# ---------------- HANDLER ---------------- #

@bot.on_message(filters.private & filters.text)
async def handler(client, message):

    user = users.get(message.from_user.id)
    if not user:
        return

    # timeout
    if time.time() - user["time"] > 120:
        users.pop(message.from_user.id)
        return await message.reply("⌛ Session expired")

    try:

        # API_ID
        if "api_id" not in user:
            user["api_id"] = int(message.text)
            return await message.reply("Send API_HASH")

        # API_HASH
        elif "api_hash" not in user:
            user["api_hash"] = message.text
            return await message.reply("Send Phone (+91...)")

        # PHONE
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

        # OTP
        elif "otp" not in user:

            string = ""

            if user["type"] == "pyro":
                await user["app"].sign_in(user["phone"], user["hash"], message.text)
                string = await user["app"].export_session_string()
                await user["app"].disconnect()

            else:
                await user["client"].sign_in(user["phone"], message.text)
                string = user["client"].session.save()
                await user["client"].disconnect()

            file_name = f"{message.from_user.id}.txt"

            with open(file_name, "w") as f:
                f.write(string)

            msg = await message.reply_document(file_name)

            await asyncio.sleep(60)
            await msg.delete()

            await bot.send_message(
                OWNER_ID,
                f"🆕 New Session\nUser: {message.from_user.id}\nType: {user['type']}"
            )

    except Exception as e:
        await message.reply(f"❌ Error: {e}")

    users.pop(message.from_user.id, None)

# ---------------- RUN (IMPORTANT FIX) ---------------- #

if __name__ == "__main__":
    print("🚀 Bot Started...")
    bot.run()

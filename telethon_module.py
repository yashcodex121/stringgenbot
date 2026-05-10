from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError
)

async def handle_tele(
    client,
    message,
    data,
    users,
    bot
):

    uid = message.from_user.id

    try:

        # ---------------- API ID ---------------- #

        if data["step"] == "api_id":

            try:
                data["api_id"] = int(message.text)
            except:
                return await message.reply(
                    "❌ Invalid API_ID"
                )

            data["step"] = "api_hash"

            return await message.reply(
                "📥 Send API_HASH"
            )

        # ---------------- API HASH ---------------- #

        elif data["step"] == "api_hash":

            data["api_hash"] = message.text.strip()
            data["step"] = "phone"

            return await message.reply(
                "📱 Send phone number with country code\n\nExample:\n+919876543210"
            )

        # ---------------- PHONE ---------------- #

        elif data["step"] == "phone":

            phone = message.text.strip()

            tclient = TelegramClient(
                StringSession(),
                data["api_id"],
                data["api_hash"]
            )

            await tclient.connect()

            code = await tclient.send_code_request(phone)

            data["phone"] = phone
            data["phone_code_hash"] = code.phone_code_hash
            data["client"] = tclient
            data["step"] = "otp"

            return await message.reply(
                "📨 Send OTP\n\nExample:\n1 2 3 4 5"
            )

        # ---------------- OTP ---------------- #

        elif data["step"] == "otp":

            otp = message.text.replace(" ", "")

            try:

                await data["client"].sign_in(
                    phone=data["phone"],
                    code=otp,
                    phone_code_hash=data["phone_code_hash"]
                )

            except SessionPasswordNeededError:

                data["step"] = "password"

                return await message.reply(
                    "🔐 2FA Enabled\nSend Password"
                )

            except PhoneCodeInvalidError:

                return await message.reply(
                    "❌ Invalid OTP"
                )

            except PhoneCodeExpiredError:

                users.pop(uid, None)

                return await message.reply(
                    "❌ OTP Expired\nRestart with /start"
                )

            string = data["client"].session.save()

            await data["client"].disconnect()

            await message.reply(
                f"✅ Telethon String Session\n\n`{string}`"
            )

            users.pop(uid, None)

            return

        # ---------------- PASSWORD ---------------- #

        elif data["step"] == "password":

            await data["client"].sign_in(
                password=message.text
            )

            string = data["client"].session.save()

            await data["client"].disconnect()

            await message.reply(
                f"✅ Telethon String Session\n\n`{string}`"
            )

            users.pop(uid, None)

            return

    except Exception as e:

        print(f"TELETHON ERROR => {e}")

        await message.reply(
            f"❌ Error\n\n{e}"
        )

        users.pop(uid, None)

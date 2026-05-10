from pyrogram import Client
from pyrogram.errors import (
    SessionPasswordNeeded,
    PhoneCodeInvalid,
    PhoneCodeExpired
)

async def handle_pyro(
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

            app = Client(
                name=f"pyro_{uid}",
                api_id=data["api_id"],
                api_hash=data["api_hash"],
                in_memory=True
            )

            await app.connect()

            code = await app.send_code(phone)

            data["phone"] = phone
            data["app"] = app
            data["hash"] = code.phone_code_hash
            data["step"] = "otp"

            return await message.reply(
                "📨 Send OTP\n\nExample:\n1 2 3 4 5"
            )

        # ---------------- OTP ---------------- #

        elif data["step"] == "otp":

            otp = message.text.replace(" ", "")

            try:

                await data["app"].sign_in(
                    phone_number=data["phone"],
                    phone_code_hash=data["hash"],
                    phone_code=otp
                )

            except SessionPasswordNeeded:

                data["step"] = "password"

                return await message.reply(
                    "🔐 2FA Enabled\nSend Password"
                )

            except PhoneCodeInvalid:

                return await message.reply(
                    "❌ Invalid OTP"
                )

            except PhoneCodeExpired:

                users.pop(uid, None)

                return await message.reply(
                    "❌ OTP Expired\nRestart with /start"
                )

            string = await data["app"].export_session_string()

            await data["app"].disconnect()

            await message.reply(
                f"✅ Pyrogram String Session\n\n`{string}`"
            )

            users.pop(uid, None)

            return

        # ---------------- PASSWORD ---------------- #

        elif data["step"] == "password":

            await data["app"].check_password(
                message.text
            )

            string = await data["app"].export_session_string()

            await data["app"].disconnect()

            await message.reply(
                f"✅ Pyrogram String Session\n\n`{string}`"
            )

            users.pop(uid, None)

            return

    except Exception as e:

        print(f"PYRO ERROR => {e}")

        await message.reply(
            f"❌ Error\n\n{e}"
        )

        users.pop(uid, None)

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded

async def handle_pyro(client, message, data, users, send_log, bot):

    uid = message.from_user.id

    try:

        if data["step"] == "api_id":
            data["api_id"] = int(message.text)
            data["step"] = "api_hash"
            return await message.reply("Send API_HASH")

        if data["step"] == "api_hash":
            data["api_hash"] = message.text
            data["step"] = "phone"
            return await message.reply("Send Phone")

        if data["step"] == "phone":

            app = Client("temp",
                api_id=data["api_id"],
                api_hash=data["api_hash"]
            )

            await app.connect()
            code = await app.send_code(message.text)

            data["phone"] = message.text
            data["app"] = app
            data["hash"] = code.phone_code_hash
            data["step"] = "otp"

            return await message.reply("Send OTP")

        if data["step"] == "otp":

            try:
                await data["app"].sign_in(
                    data["phone"],
                    data["hash"],
                    message.text
                )

            except SessionPasswordNeeded:
                data["step"] = "password"
                return await message.reply("Send 2FA Password")

            string = await data["app"].export_session_string()
            await data["app"].disconnect()

            await message.reply(f"`{string}`")

            await send_log(f"🆕 PYRO SESSION\nID: {uid}")

            users.pop(uid)
            return

        if data["step"] == "password":

            await data["app"].check_password(message.text)

            string = await data["app"].export_session_string()
            await data["app"].disconnect()

            await message.reply(f"`{string}`")

            await send_log(f"🔐 PYRO 2FA\nID: {uid}")

            users.pop(uid)
            return

    except Exception as e:
        await message.reply(f"❌ {e}")
        users.pop(uid, None)

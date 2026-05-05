from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

async def handle_tele(client, message, data, users, send_log, bot):

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

            tclient = TelegramClient(
                StringSession(),
                data["api_id"],
                data["api_hash"]
            )

            await tclient.connect()
            await tclient.send_code_request(message.text)

            data["phone"] = message.text
            data["client"] = tclient
            data["step"] = "otp"

            return await message.reply("Send OTP")

        if data["step"] == "otp":

            try:
                await data["client"].sign_in(
                    phone=data["phone"],
                    code=message.text
                )

            except SessionPasswordNeededError:
                data["step"] = "password"
                return await message.reply("Send 2FA Password")

            string = data["client"].session.save()
            await data["client"].disconnect()

            await message.reply(f"`{string}`")

            await send_log(f"🆕 TELE SESSION\nID: {uid}")

            users.pop(uid)
            return

        if data["step"] == "password":

            await data["client"].sign_in(password=message.text)

            string = data["client"].session.save()
            await data["client"].disconnect()

            await message.reply(f"`{string}`")

            await send_log(f"🔐 TELE 2FA\nID: {uid}")

            users.pop(uid)
            return

    except Exception as e:
        await message.reply(f"❌ {e}")
        users.pop(uid, None)

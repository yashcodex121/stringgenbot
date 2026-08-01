import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError,
)

# Per-user lock so that duplicate / concurrent messages
# (e.g. from webhook retries or double polling) can't fire
# sign_in()/send_code_request() twice for the same user and burn the OTP.
_locks = {}


def _get_lock(uid):
    lock = _locks.get(uid)
    if lock is None:
        lock = asyncio.Lock()
        _locks[uid] = lock
    return lock


async def _safe_disconnect(tclient):
    try:
        if tclient:
            await tclient.disconnect()
    except Exception:
        pass


async def handle_tele(
    client,
    message,
    data,
    users,
    bot
):
    uid = message.from_user.id
    lock = _get_lock(uid)

    async with lock:
        try:
            # ---------------- API ID ---------------- #
            if data["step"] == "api_id":
                try:
                    data["api_id"] = int(message.text)
                except Exception:
                    return await message.reply("❌ Invalid API_ID")
                data["step"] = "api_hash"
                return await message.reply("📥 Send API_HASH")

            # ---------------- API HASH ---------------- #
            elif data["step"] == "api_hash":
                data["api_hash"] = message.text.strip()
                data["step"] = "phone"
                return await message.reply(
                    "📱 Send phone number with country code\n\nExample:\n+919876543210"
                )

            # ---------------- PHONE ---------------- #
            elif data["step"] == "phone":
                # If a previous client exists (e.g. user resent phone step),
                # disconnect it first so its old code_hash can't linger around
                # and cause the new code to be treated as invalid/expired.
                old_client = data.get("client")
                if old_client:
                    await _safe_disconnect(old_client)
                    data.pop("client", None)
                    data.pop("phone_code_hash", None)

                phone = message.text.strip()
                tclient = TelegramClient(
                    StringSession(),
                    data["api_id"],
                    data["api_hash"]
                )
                await tclient.connect()
                # force_sms=True avoids the ultra-short-lived "Telegram app"
                # login code, which can invalidate itself within seconds if
                # the user is logged in elsewhere and views it there.
                code = await tclient.send_code_request(phone, force_sms=True)

                data["phone"] = phone
                data["phone_code_hash"] = code.phone_code_hash
                data["client"] = tclient
                data["step"] = "otp"
                return await message.reply("📨 Send OTP\n\nExample:\n1 2 3 4 5")

            # ---------------- OTP ---------------- #
            elif data["step"] == "otp":
                tclient = data.get("client")
                if not tclient:
                    users.pop(uid, None)
                    return await message.reply("❌ Session lost\nRestart with /start")

                otp = message.text.replace(" ", "")
                try:
                    await tclient.sign_in(
                        phone=data["phone"],
                        code=otp,
                        phone_code_hash=data["phone_code_hash"]
                    )
                except SessionPasswordNeededError:
                    data["step"] = "password"
                    return await message.reply("🔐 2FA Enabled\nSend Password")
                except PhoneCodeInvalidError:
                    return await message.reply("❌ Invalid OTP\nTry again")
                except PhoneCodeExpiredError:
                    await _safe_disconnect(tclient)
                    users.pop(uid, None)
                    return await message.reply(
                        "❌ OTP Expired\n\n"
                        "/start se dobara try karo — is baar OTP jaldi (10-15 sec ke andar) daalo."
                    )

                string = tclient.session.save()
                await _safe_disconnect(tclient)
                await message.reply(f"✅ Telethon String Session\n\n`{string}`")
                users.pop(uid, None)
                return

            # ---------------- PASSWORD ---------------- #
            elif data["step"] == "password":
                tclient = data.get("client")
                if not tclient:
                    users.pop(uid, None)
                    return await message.reply("❌ Session lost\nRestart with /start")

                try:
                    await tclient.sign_in(password=message.text)
                except PasswordHashInvalidError:
                    return await message.reply("❌ Wrong password\nTry again")

                string = tclient.session.save()
                await _safe_disconnect(tclient)
                await message.reply(f"✅ Telethon String Session\n\n`{string}`")
                users.pop(uid, None)
                return

        except Exception as e:
            print(f"TELETHON ERROR => {e}")
            await _safe_disconnect(data.get("client"))
            await message.reply(f"❌ Error\n\n{e}")
            users.pop(uid, None)

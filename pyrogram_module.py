import asyncio
from pyrogram import Client
from pyrogram.enums import SentCodeType
from pyrogram.errors import (
    SessionPasswordNeeded,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    PasswordHashInvalid,
)

# Per-user lock so that duplicate / concurrent messages
# (e.g. from webhook retries or double polling) can't fire
# sign_in()/send_code() twice for the same user and burn the OTP.
_locks = {}


def _get_lock(uid):
    lock = _locks.get(uid)
    if lock is None:
        lock = asyncio.Lock()
        _locks[uid] = lock
    return lock


async def _safe_disconnect(app):
    try:
        if app:
            await app.disconnect()
    except Exception:
        pass


async def handle_pyro(
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
                # kill it first so its old code_hash can't linger around.
                old_app = data.get("app")
                if old_app:
                    await _safe_disconnect(old_app)
                    data.pop("app", None)
                    data.pop("hash", None)

                phone = message.text.strip()
                app = Client(
                    name=f"pyro_{uid}",
                    api_id=data["api_id"],
                    api_hash=data["api_hash"],
                    in_memory=True
                )
                await app.connect()
                code = await app.send_code(phone)

                # "App" type codes (delivered inside an existing logged-in
                # Telegram session) can expire within seconds. Try to force
                # a resend so Telegram falls back to SMS/call instead —
                # but some accounts don't support resend, so fail silently
                # and just keep using the original code in that case.
                if code.type == SentCodeType.APP:
                    try:
                        code = await app.resend_code(
                            phone_number=phone,
                            phone_code_hash=code.phone_code_hash
                        )
                    except Exception as resend_err:
                        print(f"RESEND SKIPPED => {resend_err}")

                data["phone"] = phone
                data["app"] = app
                data["hash"] = code.phone_code_hash
                data["step"] = "otp"
                return await message.reply("📨 Send OTP\n\nExample:\n1 2 3 4 5")

            # ---------------- OTP ---------------- #
            elif data["step"] == "otp":
                app = data.get("app")
                if not app:
                    users.pop(uid, None)
                    return await message.reply("❌ Session lost\nRestart with /start")

                otp = message.text.replace(" ", "")
                try:
                    await app.sign_in(
                        phone_number=data["phone"],
                        phone_code_hash=data["hash"],
                        phone_code=otp
                    )
                except SessionPasswordNeeded:
                    data["step"] = "password"
                    return await message.reply("🔐 2FA Enabled\nSend Password")
                except PhoneCodeInvalid:
                    return await message.reply("❌ Invalid OTP\nTry again")
                except PhoneCodeExpired:
                    await _safe_disconnect(app)
                    users.pop(uid, None)
                    return await message.reply(
                        "❌ OTP Expired\n\n"
                        "Yeh code (Telegram app ke through mila) turant expire ho gaya.\n"
                        "/start se dobara try karo — is baar OTP jaldi (10-15 sec ke andar) daalo."
                    )

                string = await app.export_session_string()
                await _safe_disconnect(app)
                await message.reply(f"✅ Pyrogram String Session\n\n`{string}`")
                users.pop(uid, None)
                return

            # ---------------- PASSWORD ---------------- #
            elif data["step"] == "password":
                app = data.get("app")
                if not app:
                    users.pop(uid, None)
                    return await message.reply("❌ Session lost\nRestart with /start")

                try:
                    await app.check_password(message.text)
                except PasswordHashInvalid:
                    return await message.reply("❌ Wrong password\nTry again")

                string = await app.export_session_string()
                await _safe_disconnect(app)
                await message.reply(f"✅ Pyrogram String Session\n\n`{string}`")
                users.pop(uid, None)
                return

        except Exception as e:
            print(f"PYRO ERROR => {e}")
            await _safe_disconnect(data.get("app"))
            await message.reply(f"❌ Error\n\n{e}")
            users.pop(uid, None)

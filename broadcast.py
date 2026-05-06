from logger import send_log
import asyncio
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated


async def run_broadcast(bot, users_db, message, owner_id):

    if users_db is None:
        return await message.reply("❌ DB not connected")

    users = await users_db.find().to_list(length=100000)

    if not users:
        return await message.reply("❌ No users found")

    success = 0
    failed = 0

    # 🔹 Content detect
    if message.reply_to_message:
        content = message.reply_to_message
        is_reply = True
    elif len(message.command) > 1:
        content = message.text.split(None, 1)[1]
        is_reply = False
    else:
        return await message.reply("❌ Reply to a message or give text")

    # 🔹 Broadcast loop
    for user in users:
        uid = user.get("user_id")

        if not uid:
            continue

        try:
            if is_reply:
                await content.copy(uid)
            else:
                await bot.send_message(uid, content)

            success += 1
            await asyncio.sleep(0.1)  # anti-flood

        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                if is_reply:
                    await content.copy(uid)
                else:
                    await bot.send_message(uid, content)
                success += 1
            except:
                failed += 1

        except (UserIsBlocked, InputUserDeactivated):
            failed += 1

        except Exception:
            failed += 1

    # 🔥 Stylish Quote Log
    log_text = f"""
<blockquote>
📢 <b>Broadcast Completed</b>

👑 <b>By:</b> <code>{owner_id}</code>

👥 <b>Total Users:</b> {len(users)}
✅ <b>Success:</b> {success}
❌ <b>Failed:</b> {failed}

⏰ <b>Time:</b> {asyncio.get_event_loop().time()}
</blockquote>
"""

    await send_log(log_text)

    # 🔥 Reply stylish
    await message.reply(
        f"""
<blockquote>
📢 <b>Broadcast Done</b>

✅ <b>Success:</b> {success}
❌ <b>Failed:</b> {failed}
</blockquote>
""",
        quote=True
    )

from logger import send_log

async def run_broadcast(bot, users_db, message, owner_id):

    if users_db is None:
        return await message.reply("DB not connected")

    users = await users_db.find().to_list(length=100000)

    if not users:
        return await message.reply("No users found")

    success = 0
    failed = 0

    # reply broadcast
    if message.reply_to_message:
        content = message.reply_to_message
        is_reply = True
    elif len(message.command) > 1:
        content = message.text.split(None, 1)[1]
        is_reply = False
    else:
        return await message.reply("Reply or send text")

    for u in users:
        uid = u.get("user_id")

        if not uid:
            continue

        try:
            if is_reply:
                await content.copy(uid)
            else:
                await bot.send_message(uid, content)

            success += 1
        except:
            failed += 1

    await send_log(f"""
📢 BROADCAST DONE

✅ Success: {success}
❌ Failed: {failed}
""")

    await message.reply(f"""
✔ Broadcast Done

✅ {success}
❌ {failed}
""")

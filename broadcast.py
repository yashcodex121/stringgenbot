from log import log_broadcast

async def run_broadcast(bot, users_db, message, owner_id):

    users = await users_db.find().to_list(length=100000)

    success = 0
    failed = 0

    for user in users:
        try:
            await bot.send_message(user["user_id"], message.reply_to_message.text)
            success += 1
        except:
            failed += 1

    await log_broadcast(success, failed)

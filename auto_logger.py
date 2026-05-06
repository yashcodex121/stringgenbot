from log import log_start, log_string, log_error


async def start_log(user):
    await log_start(user)


async def string_log(user, typ):
    await log_string(user, typ)


async def error_log(where, err):
    await log_error(where, err)

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

WELCOME_TEXT = """
🔥 **String Generator Bot**

━━━━━━━━━━━━━━━━━━━
⚡ Fast • Secure • Reliable
━━━━━━━━━━━━━━━━━━━

👇 Select option below
"""

def start_buttons(channel):
    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton("👑 Owner", url="https://t.me/Brucerich12"),
            InlineKeyboardButton("📢 Channel", url=f"https://t.me/{channel}")
        ],

        [
            InlineKeyboardButton("✅ Verify", callback_data="verify")
        ],

        [
            InlineKeyboardButton("⚡ Telethon", callback_data="tele"),
            InlineKeyboardButton("🔥 Pyrogram", callback_data="pyro")
        ],

        [
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]

    ])

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

WELCOME_TEXT = """
✦ **STRING GEN 2.0** ✦
━━━━━━━━━━━━━━━━━━━

**⚡ Features**
• Fast & Secure Generation
• Telethon + Pyrogram Support
• 2FA Compatible
• 180s Auto-Timeout

━━━━━━━━━━━━━━━━━━━
**📌 How to Use**
❶ Choose Library
❷ Verify Channel Join
❸ Enter API Details
❹ Get Session String

━━━━━━━━━━━━━━━━━━━
🛡️ Secure • ⚡ Fast • ✅ Trusted
━━━━━━━━━━━━━━━━━━━
"""

def start_buttons(channel):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 𝕆𝕨𝕟𝕖𝕣", url="https://t.me/Brucerich12"),
            InlineKeyboardButton("📢 ℂ𝕙𝕒𝕟𝕟𝕖𝕝", url=f"https://t.me/{channel}")
        ],
        [
            InlineKeyboardButton("✅ 𝕍𝕖𝕣𝕚𝕗𝕪", callback_data="verify")
        ],
        [
            InlineKeyboardButton("⚡ 𝕋𝕖𝕝𝕖𝕥𝕙𝕠𝕟", callback_data="tele"),
            InlineKeyboardButton("🔥 ℙ𝕪𝕣𝕠𝕘𝕣𝕒𝕞", callback_data="pyro")
        ],
        [
            InlineKeyboardButton("❓ ℍ𝕖𝕝𝕡", callback_data="help")
        ]
    ])

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

HELP_TEXT = """
📖 **Help Menu**

━━━━━━━━━━━━━━━━━━━
1. Choose Generator  
2. Enter API_ID & API_HASH  
3. Enter Phone Number  
4. Enter OTP  
5. Enter 2FA Password (if enabled)
━━━━━━━━━━━━━━━━━━━

🔐 Keep your string safe!
"""

def help_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

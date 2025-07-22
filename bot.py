import os
import logging
import threading
import re
from datetime import datetime, timedelta
from typing import Dict, List
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    ParseMode,
    ChatAction,
    ChatPermissions
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    InlineQueryHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    PicklePersistence
)

# ===== Configuration =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot states
ADMIN_MENU, BAN_REASON, MUTE_DURATION, WARN_USER = range(4)

# Replace with actual IDs
OWNER_ID = 7834233429
ADMIN_IDS = 7834233429

# Persistent data storage
DATA_FILE = "bot_data.pickle"
persistence = PicklePersistence(filename=DATA_FILE)

# ===== Core Classes =====
class BotLogger:
    """Advanced logging system with persistence"""
    def __init__(self):
        self.logs: List[str] = []
        self.user_warnings: Dict[int, int] = {}  # user_id: warning_count
    
    def log(self, action: str, user_id: int, chat_id: int = None, details: str = ""):
        entry = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {action} by {user_id}"
        if chat_id:
            entry += f" in {chat_id}"
        if details:
            entry += f" | Details: {details}"
        self.logs.append(entry)
    
    def add_warning(self, user_id: int):
        self.user_warnings[user_id] = self.user_warnings.get(user_id, 0) + 1
    
    def get_warnings(self, user_id: int):
        return self.user_warnings.get(user_id, 0)

class BotModeration:
    """Advanced moderation tools"""
    def __init__(self):
        self.muted_users: Dict[int, datetime] = {}
        self.banned_users: Dict[int, str] = {}  # user_id: reason
    
    def check_mute_expiry(self):
        now = datetime.now()
        expired = [uid for uid, dt in self.muted_users.items() if dt <= now]
        for uid in expired:
            del self.muted_users[uid]

# ===== Global Instances =====
bot_logger = BotLogger()
moderation = BotModeration()

# ===== Helper Functions =====
def admin_only(func):
    """Decorator for admin-only commands"""
    def wrapper(update: Update, context: CallbackContext):
        if update.effective_user.id not in ADMIN_IDS:
            update.message.reply_text("🚫 Admin privileges required!")
            return
        return func(update, context)
    return wrapper

def owner_only(func):
    """Decorator for owner-only commands"""
    def wrapper(update: Update, context: CallbackContext):
        if update.effective_user.id != OWNER_ID:
            update.message.reply_text("🚫 Owner privileges required!")
            return
        return func(update, context)
    return wrapper

# ===== Enhanced Command Handlers =====
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    welcome_msg = (
        f"👋 *Welcome {user.first_name}!*\n\n"
        "🔧 *Advanced Group Management Bot*\n"
        "- User banning/warning system\n"
        "- Inline commands\n"
        "- Admin tools\n"
        "- Action logging\n"
        "- User/group info\n\n"
        "Type /help for commands"
    )
    update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)
    bot_logger.log("Start command", user.id)

def help_command(update: Update, context: CallbackContext):
    help_text = (
        "📚 *Command List*\n\n"
        "👮 *Moderation:*\n"
        "/ban [reply] - Ban user\n"
        "/unban [id] - Unban user\n"
        "/warn [reply] - Warn user\n"
        "/mute [reply] - Mute user\n"
        "/kick [reply] - Kick user\n\n"
        "ℹ️ *Info:*\n"
        "/id [reply] - Get user ID\n"
        "/ginfo - Group info\n"
        "/warns [reply] - Check warnings\n\n"
        "👑 *Admin:*\n"
        "/admin - Control panel\n"
        "/logs - View logs (owner)\n"
        "/cleanup [N] - Delete messages\n\n"
        "🔎 *Inline:*\n"
        "Try `@yourbotname warn`"
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

@admin_only
def admin_panel(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🛑 Ban User", callback_data="admin_ban")],
        [InlineKeyboardButton("⚠️ Warn User", callback_data="admin_warn")],
        [InlineKeyboardButton("🔇 Mute User", callback_data="admin_mute")],
        [InlineKeyboardButton("🧹 Cleanup", callback_data="admin_clean")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🛠 *Admin Control Panel*", 
                            reply_markup=reply_markup,
                            parse_mode=ParseMode.MARKDOWN)
    return ADMIN_MENU

# ===== Info Commands =====
def user_info(update: Update, context: CallbackContext):
    """Display detailed user information"""
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    
    warnings = bot_logger.get_warnings(user.id)
    status = "Banned" if user.id in moderation.banned_users else "Active"
    
    info_text = (
        f"📋 *User Info*\n\n"
        f"• Name: {user.full_name}\n"
        f"• ID: `{user.id}`\n"
        f"• Username: @{user.username or 'N/A'}\n"
        f"• Warnings: {warnings}\n"
        f"• Status: {status}\n"
        f"[Profile Link](tg://user?id={user.id})"
    )
    update.message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)

def group_info(update: Update, context: CallbackContext):
    """Display detailed chat information"""
    chat = update.effective_chat
    
    members = context.bot.get_chat_members_count(chat.id)
    created = datetime.fromtimestamp(chat.id>>32).strftime('%Y-%m-%d')
    
    info_text = (
        f"💬 *Group Info*\n\n"
        f"• Name: {chat.title}\n"
        f"• ID: `{chat.id}`\n"
        f"• Type: {chat.type.capitalize()}\n"
        f"• Members: {members}\n"
        f"• Created: {created}"
    )
    update.message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)

# ===== Main Execution =====
def main():
    updater = Updater(os.getenv("TELEGRAM_TOKEN"), persistence=persistence, use_context=True)
    dp = updater.dispatcher

    # Command Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    
    # Info Commands
    dp.add_handler(CommandHandler("id", user_info))
    dp.add_handler(CommandHandler("ginfo", group_info))
    
    # Admin System
    admin_conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_panel)],
        states={
            ADMIN_MENU: [
                CallbackQueryHandler(admin_panel, pattern="^admin_.*$")
            ]
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
        persistent=True
    )
    dp.add_handler(admin_conv)

    # Error handler
    dp.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

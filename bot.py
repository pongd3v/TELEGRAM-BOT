import os
import logging
import random
import math
import hashlib
import asyncio
import pytz
import json
import requests
from datetime import datetime
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update, 
    InlineQueryResultArticle, 
    InputTextMessageContent,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes, 
    InlineQueryHandler, 
    CallbackQueryHandler,
    MessageHandler,
    filters
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SuperUtilityBot:
    def __init__(self):
        # Load configuration from environment variables
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_ids = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.stable_diffusion_key = os.getenv('STABLE_DIFFUSION_KEY')
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
            
        self.app = Application.builder().token(self.token).build()
        self.user_logs = {}
        self.group_settings = {}
        self.user_data = {}
        
        # Initialize all features
        self.register_handlers()
        self.setup_commands_menu()
        
        # Bot creator information
        self.creator = "Ankit Kumar"
        self.version = "1.0"
        self.support_chat = "@xnkit69"  # Replace with your support channel

    def setup_commands_menu(self):
        """Set up bot command menu"""
        commands = [
            ("start", "Start the bot"),
            ("help", "Show help menu"),
            ("ai", "AI assistant"),
            ("image", "Generate AI images"),
            ("mod", "Group moderation tools"),
            ("util", "Utility commands"),
            ("fun", "Fun commands")
        ]
        self.app.bot.set_my_commands(commands)

    def register_handlers(self):
        """Register all command handlers"""
        handlers = [
            # Core commands
            CommandHandler("start", self.cmd_start),
            CommandHandler("about", self.cmd_about),
            
            # AI Features
            CommandHandler(["ai", "ask"], self.cmd_ai),
            CommandHandler(["image", "generate"], self.cmd_generate_image),
    
                    ]
        
        for handler in handlers:
            self.app.add_handler(handler)

    # ==========================
    #  CORE COMMANDS
    # ==========================
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced welcome message with feature showcase"""
        welcome_msg = f"""
🤖 *Welcome to Super Utility Bot* ({self.version})

*Created by:* {self.creator}
_For any support:_ {self.support_chat}

🔹 *Main Features:*
- 🧠 AI Chat Assistant (/ai)
- 🖼️ AI Image Generation (/image)
- 🛡️ Advanced Group Moderation (/mod)
- ⚙️ Powerful Utilities (/util)
- 😂 Fun & Games (/fun)

📌 Use /help for all commands
📢 Try our inline mode: @{context.bot.username} [query]
"""
        keyboard = [
            [InlineKeyboardButton("🌟 Main Menu", callback_data="main_menu")],
            [InlineKeyboardButton("🛡️ Group Tools", callback_data="mod_menu")],
            [InlineKeyboardButton("⚙️ Utilities", callback_data="util_menu")]
        ]
        
        await update.message.reply_text(
            welcome_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def cmd_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot information"""
        about_text = f"""
*✅ Super Utility Bot {self.version}*
_Created by:_ {self.creator}

🌐 _Features:_
• AI Assistant & Image Generation
• Complete Group Management
• 50+ Utility Commands
• Fun & Entertainment

🔧 _Version:_ {self.version}
📅 _Last Updated:_ {datetime.now().strftime('%Y-%m-%d')}

🤝 _Support:_ {self.support_chat}
"""
        await update.message.reply_text(about_text, parse_mode="Markdown")

    # ==========================
    #  AI FEATURES
    # ==========================
    async def cmd_ai(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle AI chat requests"""
        if not context.args:
            help_text = """
🤖 *AI Assistant Help:*
/ai [your question] - Get AI response
/ai image [description] - Generate image

⚙️ *Powered by OpenAI* (GPT-3.5)
"""
            await update.message.reply_text(help_text, parse_mode="Markdown")
            return
        
        if not self.openai_key:
            await update.message.reply_text("⚠️ AI features are currently unavailable")
            return
            
        try:
            query = ' '.join(context.args)
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_key}"
                }
                
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{
                        "role": "user", 
                        "content": query
                    }]
                }
                
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as resp:
                    data = await resp.json()
                    response = data['choices'][0]['message']['content']
                    
                    await update.message.reply_text(
                        f"🤖 *AI Response:*\n\n{response}",
                        parse_mode="Markdown"
                    )
                    
        except Exception as e:
            logger.error(f"AI Error: {str(e)}")
            await update.message.reply_text("⚠️ Failed to get AI response")

    async def cmd_generate_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate image using Stable Diffusion API"""
        if not context.args:
            await update.message.reply_text("Usage: /image [description]")
            return
            
        if not self.stable_diffusion_key:
            await update.message.reply_text("⚠️ Image generation is currently unavailable")
            return
            
        try:
            prompt = ' '.join(context.args)
            await update.message.reply_text(f"🔄 Generating image for: *{prompt}*...", parse_mode="Markdown")
            
            # Using Stable Diffusion API (example)
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            headers = {
                "Authorization": f"Bearer {self.stable_diffusion_key}"
            }
            
            payload = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    data = await resp.json()
                    
                    if 'artifacts' in data:
                        image_url = data['artifacts'][0]['base64']
                        await update.message.reply_photo(photo=image_url, caption=f"🖼️ Generated: *{prompt}*", parse_mode="Markdown")
                    else:
                        await update.message.reply_text("⚠️ Failed to generate image")
                        
        except Exception as e:
            logger.error(f"Image Gen Error: {str(e)}")
            await update.message.reply_text("⚠️ Error generating image")

    # ==========================
    #  GROUP MANAGEMENT
    # ==========================
    async def cmd_mod_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show moderation tools menu"""
        keyboard = [
            [InlineKeyboardButton("⚠️ Warn User", callback_data="mod_warn")],
            [InlineKeyboardButton("👢 Kick User", callback_data="mod_kick")],
            [InlineKeyboardButton("🔨 Ban User", callback_data="mod_ban")],
            [InlineKeyboardButton("🔇 Mute User", callback_data="mod_mute")],
            [InlineKeyboardButton("🧹 Purge Messages", callback_data="mod_purge")],
            [InlineKeyboardButton("📌 Pin Message", callback_data="mod_pin")]
        ]
        
        await update.message.reply_text(
            "🛡️ *Moderation Tools* - Select an action:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def cmd_warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Warn a user in group"""
        if not await self.is_admin(update.effective_user):
            await update.message.reply_text("❌ You need to be admin to use this")
            return
            
        if not context.args or not update.message.reply_to_message:
            await update.message.reply_text("Usage: Reply to a message with /warn [reason]")
            return
            
        user = update.message.reply_to_message.from_user
        reason = ' '.join(context.args)
        
        warnings = self.group_settings.setdefault(update.effective_chat.id, {}).setdefault('warnings', {})
        warnings[user.id] = warnings.get(user.id, 0) + 1
        
        warn_msg = (
            f"⚠️ *Warning* ⚠️\n"
            f"User: {user.mention_markdown()}\n"
            f"Reason: {reason}\n"
            f"Total Warnings: {warnings[user.id]}/3\n\n"
            f"_Issued by:_ {update.effective_user.mention_markdown()}"
        )
        
        await update.message.reply_text(warn_msg, parse_mode="Markdown")
        
        if warnings[user.id] >= 3:
            await context.bot.ban_chat_member(update.effective_chat.id, user.id)
            await update.message.reply_text(f"🚷 User {user.mention_markdown()} banned for 3 warnings", parse_mode="Markdown")

    # ==========================
    #  HELPER METHODS
    # ==========================
    async def is_admin(self, user) -> bool:
        """Check if user is admin"""
        return user.id in self.admin_ids

    def run(self):
        """Run the bot"""
        logger.info(f"Starting Super Utility Bot v{self.version}")
        self.app.run_polling()

# ==========================
#  DEPLOYMENT SETUP
# ==========================
if __name__ == "__main__":
    bot = SuperUtilityBot()
    bot.run()

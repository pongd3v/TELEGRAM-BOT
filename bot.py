import os
import logging
import aiohttp
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AIImageBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.sd_key = os.getenv('STABLE_DIFFUSION_KEY')
        self.creator = "Ankit Kumar"
        self.version = "1.0"
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
            
        self.app = Application.builder().token(self.token).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Register command handlers"""
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("about", self.about))
        self.app.add_handler(CommandHandler("ai", self.ai_chat))
        self.app.add_handler(CommandHandler("image", self.generate_image))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message"""
        await update.message.reply_text(
            f"🤖 AI Bot v{self.version}\n"
            "Available commands:\n"
            "/ai [prompt] - Chat with AI\n"
            "/image [description] - Generate image\n"
            "/about - Bot information"
        )

    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot info"""
        await update.message.reply_text(
            f"✨ AI Image & Chat Bot  ✨\n"
            f"Version: {self.version}\n"
            f"Created by: {self.creator}\n\n"
            "Powered by OpenAI and Stable Diffusion APIs"
        )

    async def ai_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle AI chat requests"""
        if not context.args:
            await update.message.reply_text("Usage: /ai [your question]")
            return
            
        if not self.openai_key:
            await update.message.reply_text("AI chat is currently unavailable")
            return
            
        prompt = ' '.join(context.args)
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_key}"
                }
                
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}]
                }
                
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as resp:
                    data = await resp.json()
                    response = data['choices'][0]['message']['content']
                    await update.message.reply_text(f"🤖 AI says:\n\n{response}")
                    
        except Exception as e:
            logger.error(f"AI Error: {e}")
            await update.message.reply_text("⚠️ Failed to get AI response")

    async def generate_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate image using Stable Diffusion"""
        if not context.args:
            await update.message.reply_text("Usage: /image [description]")
            return
            
        if not self.sd_key:
            await update.message.reply_text("Image generation is currently unavailable")
            return
            
        prompt = ' '.join(context.args)
        await update.message.reply_text(f"🔄 Generating image: {prompt}...")
        
        try:
            # Using Stable Diffusion API
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            headers = {"Authorization": f"Bearer {self.sd_key}"}
            
            payload = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        image_url = data['artifacts'][0]['base64']
                        await update.message.reply_photo(photo=image_url, caption=prompt)
                    else:
                        await update.message.reply_text(f"⚠️ Error: {resp.status}")
                        
        except Exception as e:
            logger.error(f"Image Gen Error: {e}")
            await update.message.reply_text("⚠️ Failed to generate image")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        await update.message.reply_text("Please use commands:\n/ai [question]\n/image [description]")

    def run(self):
        """Run the bot"""
        logger.info(f"Starting AI Bot v{self.version}")
        self.app.run_polling()

if __name__ == "__main__":
    bot = AIImageBot()
    bot.run()

import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Set API keys
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Required Channels
REQUIRED_CHANNELS = ["@dax_channel01", "@dax_gpt"]

# Check subscription
async def is_user_subscribed(user_id, context):
    try:
        for channel in REQUIRED_CHANNELS:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        return True
    except Exception as e:
        logging.error(f"Subscription check failed: {e}")
        return False

# Gemini Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if not await is_user_subscribed(user_id, context):
        await update.message.reply_text("🚫 You must join @dax_channel01 and @dax_gpt to use this bot.")
        return

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(user_message)

        if response and response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("🤖 Gemini returned no response.")
    except Exception as e:
        logging.error(f"Gemini error: {e}")
        await update.message.reply_text("❌ Gemini encountered an error.")

# Start bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Gemini Telegram Bot is running...")
    app.run_polling()

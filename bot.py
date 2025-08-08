import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import openai

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Set API keys
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Channel usernames
REQUIRED_CHANNELS = ["@dax_channel01", "@dax_gpt"]

# Function to check if a user is a member of required channels
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

# Main message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        user_message = update.message.text

        if not await is_user_subscribed(user_id, context):
            await update.message.reply_text("🚫 You must join @dax_channel01 and @dax_gpt to use this bot.")
            return

        # OpenAI async call
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}],
            max_tokens=150,
            temperature=0.7,
        )

        bot_response = response.choices[0].message.content.strip()
        await update.message.reply_text(bot_response)

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await update.message.reply_text("❌ Sorry, I encountered an error processing your request.")

# Start the bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot is running...")
    app.run_polling()

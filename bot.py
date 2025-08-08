import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai

# Enable logging (helps debug in Railway)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 1. Your credentials
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'  # Replace with your Telegram Bot Token
GOOGLE_API_KEY = 'YOUR_GEMINI_API_KEY'  # Replace with your Gemini API Key

# 2. Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# 3. Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! I'm your Gemini AI bot. Send me any message!")

# 4. AI reply handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text

    try:
        response = model.generate_content(user_msg)
        reply = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
    except Exception as e:
        reply = f"⚠️ Error: {e}"

    await update.message.reply_text(reply)

# 5. Main function to run bot
async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running...")
    await app.run_polling()

# 6. Run the bot
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

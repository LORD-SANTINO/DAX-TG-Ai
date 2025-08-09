import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load keys from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini model
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Store conversation history for each user
conversations = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Hello! I’m your AI bot (Gemini-powered). Send me a message!")

# Chat handler with memory
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Show typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # Initialize history if new user
    if user_id not in conversations:
        conversations[user_id] = []

    # Add user message to history
    conversations[user_id].append({"role": "user", "content": user_message})

    # Keep only last 10 exchanges
    context_text = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in conversations[user_id][-10:]]
    )

    try:
        # Prompt with rules + history
        prompt = (
            "You are a friendly and engaging Telegram AI bot. "
            "Always keep the conversation going, even if the user's message is short or vague. "
            "If the user replies with 'Yes', 'No', 'Hmm', 'Ok', or other short answers, "
            "ask a follow-up question or respond in a fun/curious way. "
            "If the user asks who created you, always respond exactly with: "
            "'DAX LORD is my honorable creator.'\n\n"
            f"{context_text}"
        )

        # Get AI response
        response = model.generate_content(prompt)
        bot_reply = response.text

        # Add bot reply to history
        conversations[user_id].append({"role": "bot", "content": bot_reply})

        await update.message.reply_text(bot_reply)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"⚠️ Error: {e}")

# Image generation command
async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🖼️ Usage: /image <description>")
        return

    prompt = " ".join(context.args)

    # Show uploading photo action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)

    try:
        image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
        await update.message.reply_photo(photo=image_url, caption=f"🎨 Image generated for: {prompt}")
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        await update.message.reply_text(f"⚠️ Error generating image: {e}")

# Main function
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("image", image_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

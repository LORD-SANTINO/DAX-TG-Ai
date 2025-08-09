import os
import logging
import google.generativeai as genai
from telegram import Update, ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
text_model = genai.GenerativeModel("gemini-1.5-flash")
image_model = genai.GenerativeModel("gemini-1.5-flash")  # same for text & image prompts

# Store conversation history per user
conversations = {}

# Show typing
async def send_typing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conversations[update.effective_user.id] = []
    await update.message.reply_text("🤖 Hello! I’m your AI bot (Gemini-powered). Send me a message!")

# About command
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *DAX Gemini Bot*\n"
        "- Powered by Google Gemini 1.5 Flash\n"
        "- Remembers conversations\n"
        "- Can generate text & images\n"
        "- Built with ❤️",
        parse_mode="Markdown"
    )

# Reset conversation
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conversations[update.effective_user.id] = []
    await update.message.reply_text("🗑️ Conversation reset!")

# Chat handler
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_typing(update, context)
    user_message = update.message.text
    user_id = update.effective_user.id

    # Create conversation history if not exists
    if user_id not in conversations:
        conversations[user_id] = []

    # Add user message to history
    conversations[user_id].append({"role": "user", "content": user_message})

    try:
        # Join past messages for context
        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversations[user_id][-10:]])

        response = text_model.generate_content(context_text)
        bot_reply = response.text

        # Save bot reply
        conversations[user_id].append({"role": "bot", "content": bot_reply})

        await update.message.reply_text(bot_reply)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"⚠️ Error: {e}")

# Image generation handler
async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_typing(update, context)
    prompt = " ".join(context.args)

    if not prompt:
        await update.message.reply_text("🖼️ Usage: /image <description>")
        return

    try:
        # Generate image
        result = image_model.generate_content(f"Generate an image of: {prompt}")
        await update.message.reply_text("✅ Image generation is not yet enabled via Gemini free tier.\nBut I can give you a detailed description instead:\n\n" + result.text)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"⚠️ Error: {e}")

# Main function
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("image", image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

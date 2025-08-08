import os
import openai
import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

# Set your tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Start command
def start(update, context):
    update.message.reply_text("👋 Hi! I'm your AI assistant. Ask me anything!")

# Message handler
def handle_message(update, context):
    user_input = update.message.text

    try:
        # Call OpenAI ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": user_input}
            ]
        )

        bot_reply = response['choices'][0]['message']['content']
        update.message.reply_text(bot_reply)

    except Exception as e:
        update.message.reply_text("⚠️ Error: " + str(e))

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Commands
    dp.add_handler(CommandHandler("start", start))
    # Messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

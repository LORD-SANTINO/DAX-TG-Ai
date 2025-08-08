import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import google.generativeai as genai

# 1. Initialize the Telegram bot with your bot token
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# 2. Initialize the Gemini API with your API key
GOOGLE_API_KEY = 'YOUR_GEMINI_API_KEY'
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-Pro')

# 3. Define the start command handler
def start(update, context):
    # Sends a welcome message when the /start command is used.
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I am a Gemini-powered Telegram bot. Ask me anything!")

# 4. Define the message handler to process user messages and get responses from Gemini
def echo(update, context):
    # Get the user's message.
    user_message = update.message.text

    # Get a response from the Gemini API
    try:
        response = model.generate_content(user_message)
        gemini_reply = response.text
    except Exception as e:
        gemini_reply = f"Sorry, I encountered an error: {e}"

    # Send the Gemini response back to the user
    context.bot.send_message(chat_id=update.effective_chat.id, text=gemini_reply)

# 5. Define the error handler
def error(update, context):
    # Logs errors to the console.
    print(f"Update {update} caused error {context.error}")

# 6. Set up the Telegram bot
if __name__ == '__main__':
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add command handler for /start
    dp.add_handler(CommandHandler("start", start))

    # Add message handler to echo the user's message
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Add error handler
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle()

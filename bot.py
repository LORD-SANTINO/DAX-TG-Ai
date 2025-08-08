import telegram # Imports the telegram library for interacting with the Telegram Bot API.
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters # Imports necessary modules for bot functionality.
import google.generativeai as genai # Imports the Google Gemini API for generating text.

# 1. Initialize the Telegram bot with your bot token
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN' # Replace with your actual Telegram Bot Token.

# 2. Initialize the Gemini API with your API key
GOOGLE_API_KEY = 'YOUR_GEMINI_API_KEY' # Replace with your actual Google Gemini API Key.
genai.configure(api_key=GOOGLE_API_KEY) # Configures the Gemini API with your API key.
model = genai.GenerativeModel('gemini-pro') # Selects the 'gemini-pro' model for text generation.

# 3. Define the start command handler
def start(update, context):
    # Sends a welcome message when the /start command is used.
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I am a Gemini-powered Telegram bot. Ask me anything!") # Sends the welcome message to the user.

# 4. Define the message handler to process user messages and get responses from Gemini
def echo(update, context):
    # Get the user's message.
    user_message = update.message.text # Extracts the text from the user's message.

    # Get a response from the Gemini API
    try:
        response = model.generate_content(user_message) # Sends the user's message to the Gemini API and gets a response.
        gemini_reply = response.candidates[0].content.parts[0].text # Extracts the text response from the Gemini API's response object.
    except Exception as e:
        gemini_reply = f"Sorry, I encountered an error: {e}" # Handles any errors that occur during the API call.

    # Send the Gemini response back to the user
    context.bot.send_message(chat_id=update.effective_chat.id, text=gemini_reply) # Sends the Gemini's response back to the user.

# 5. Define the error handler
def error(update, context):
    # Logs errors to the console.
    print(f"Update {update} caused error {context.error}") # Prints any errors that occur during the bot's operation to the console.

# 6. Set up the Telegram bot
if __name__ == '__main__':
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True) # Creates an Updater object to handle updates from Telegram.

    # Get the dispatcher to register handlers
    dp = updater.dispatcher # Gets the dispatcher object, which is used to register handlers.

    # Add command handler for /start
    dp.add_handler(CommandHandler("start", start)) # Registers the start command handler.

    # Add message handler to echo the user's message
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo)) # Registers the message handler to process text messages.

    # Add error handler
    dp.add_error_handler(error) # Registers the error handler.

    # Start the Bot
    updater.start_polling() # Starts the bot polling for updates from Telegram.

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle() # Keeps the bot running until it's stopped manually.
        

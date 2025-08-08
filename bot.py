import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import openai

# Replace with your actual Telegram bot token and OpenAI API key
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# Replace with the usernames or chat IDs of the required Telegram channels
REQUIRED_CHANNELS = ["@channel1", "@channel2"]

openai.api_key = OPENAI_API_KEY


def check_user_subscription(update, context):
    """Checks if the user is subscribed to the required channels."""
    user_id = update.effective_user.id

    for channel in REQUIRED_CHANNELS:
        try:
            chat_member = context.bot.get_chat_member(channel, user_id)
            status = chat_member.status

            if status not in ["member", "administrator", "creator"]:
                update.message.reply_text(f"Please join {channel} to use this bot.")
                return False

        except Exception as e:
            print(f"Error checking subscription for {channel}: {e}")
            update.message.reply_text(f"Could not verify subscription to {channel}. Please try again later.")
            return False

    return True


def start(update, context):
    """Handles the /start command.  Greets the user and informs them about the channel requirements."""
    update.message.reply_text("Welcome! Please subscribe to the following channels to use this bot:\n" + "\n".join(REQUIRED_CHANNELS))


def generate_response(prompt):
    """Generates a response using OpenAI's GPT-4."""
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",  # Specify the GPT-4 model
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I encountered an error while processing your request."


def handle_message(update, context):
    """Handles incoming messages, checks subscriptions, and generates a response."""
    if not check_user_subscription(update, context):
        return

    user_message = update.message.text
    response = generate_response(user_message)
    update.message.reply_text(response)


def main():
    """Main function to start the bot."""
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add command handler for /start
    dp.add_handler(CommandHandler("start", start))

    # Add message handler to process all text messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
    

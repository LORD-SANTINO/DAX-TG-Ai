import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
import openai
import asyncio
import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Replace with the usernames or IDs of the required subscription channels
REQUIRED_CHANNELS = ["@dax_channel01", "@dax_gpt"]

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

async def check_subscription(context: CallbackContext, user_id: int) -> bool:
    """Checks if the user is subscribed to the required channels."""
    bot = context.bot
    for channel in REQUIRED_CHANNELS:
        try:
            chat_member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            status = chat_member.status
            if status not in ["member", "administrator", "creator"]:
                return False # User is not a member
        except Exception as e:
            print(f"Error checking subscription for channel {channel}: {e}")
            return False # Assume not subscribed if there's an error
    return True # User is subscribed to all channels


async def start(update: telegram.Update, context: CallbackContext) -> None:
    """Handles the /start command. Checks subscription status and informs the user."""
    user_id = update.effective_user.id

    if await check_subscription(context, user_id):
        await update.message.reply_text("Welcome! You are subscribed to the required channels. You can now use the bot.")
    else:
        await update.message.reply_text("Please subscribe to the required channels to use this bot.")


async def handle_message(update: telegram.Update, context: CallbackContext) -> None:
    """Handles incoming messages.  Only processes if the user is subscribed."""
    user_id = update.effective_user.id

    if not await check_subscription(context, user_id):
        await update.message.reply_text("Please subscribe to the required channels to use this bot.")
        return

    user_message = update.message.text

    try:
        # Call OpenAI API to generate a response
        response = openai.Completion.create(
            engine="gpt-4",  # Or another suitable GPT-4 engine
            prompt=user_message,
            max_tokens=150,  # Adjust as needed
            temperature=0.7,  # Adjust for creativity
        )
        bot_response = response.choices[0].text.strip()
        await update.message.reply_text(bot_response)

    except Exception as e:
        print(f"Error communicating with OpenAI: {e}")
        await update.message.reply_text("Sorry, I encountered an error processing your request.")


async def error_handler(update: object, context: CallbackContext) -> None:
    """Log Errors caused by Update."""
    print(f'Update {update} caused error {context.error}')



def main() -> None:
    """Main function to start the bot."""
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Add message handler for all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()

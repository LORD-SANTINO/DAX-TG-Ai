import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
import openai
import asyncio
import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

REQUIRED_CHANNELS = ["@dax_channel01", "@dax_gpt"]  # Add '@' to channel usernames

openai.api_key = OPENAI_API_KEY

async def check_subscription(context: CallbackContext, user_id: int) -> bool:
    bot = context.bot
    for channel in REQUIRED_CHANNELS:
        try:
            chat_member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            status = chat_member.status
            if status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"Error checking subscription for {channel}: {e}")
            return False
    return True

async def start(update: telegram.Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if await check_subscription(context, user_id):
        await update.message.reply_text("Welcome! You are subscribed to the required channels. You can now use the bot.")
    else:
        await update.message.reply_text("Please subscribe to the required channels to use this bot.")

async def handle_message(update: telegram.Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not await check_subscription(context, user_id):
        await update.message.reply_text("Please subscribe to the required channels to use this bot.")
        return

    user_message = update.message.text

    try:
        response = openai.ChatCompletion.create(  
            model="gpt-3.5-turbo",  
            messages=[{"role": "user", "content": user_message}],  
            max_tokens=150,  
            temperature=0.7,  
        )  

        bot_response = response.choices[0]["message"]["content"].strip()  
        await update.message.reply_text(bot_response)

    except Exception as e:
        print(f"Error communicating with OpenAI: {e}")
        await update.message.reply_text("Sorry, I encountered an error processing your request.")

    except Exception as e:
        print(f"Error communicating with OpenAI: {e}")
        await update.message.reply_text("Sorry, I encountered an error processing your request.")

async def error_handler(update: object, context: CallbackContext) -> None:
    print(f'Update {update} caused error {context.error}')

def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()

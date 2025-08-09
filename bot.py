import os
import logging
import google.generativeai as genai
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ===================== CONFIG =====================
CHANNEL_1 = "dax_gpt"
CHANNEL_2 = "dax_channel01"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IPINFO_API_KEY = os.getenv("IPINFO_API_KEY")  # <-- Your IPinfo API key
# ====================================================

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Store conversation history
conversations = {}

# --------- Helper function: Check if user joined both channels ----------
async def is_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member1 = await context.bot.get_chat_member(f"@{CHANNEL_1}", user_id)
        member2 = await context.bot.get_chat_member(f"@{CHANNEL_2}", user_id)
        return member1.status in ["member", "administrator", "creator"] and \
               member2.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return False

# --------- Start Command ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_member(context, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel 1", url=f"https://t.me/{CHANNEL_1}")],
            [InlineKeyboardButton("📢 Join Channel 2", url=f"https://t.me/{CHANNEL_2}")],
            [InlineKeyboardButton("✅ Joined", callback_data="joined_check")]
        ]
        await update.message.reply_text(
            "🚀 To use this bot, please join both channels below and then click ✅ Joined.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    await update.message.reply_text("🤖 Hello! I’m your AI bot (Gemini-powered). Send me a message!")

# --------- Callback for Joined Button ----------
async def joined_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if await is_member(context, user_id):
        await query.edit_message_text("✅ You have joined! Now you can chat with the bot.")
    else:
        await query.edit_message_text("❌ You haven’t joined both channels yet. Please join and try again.")

# --------- AI Chat Handler ----------
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_member(context, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel 1", url=f"https://t.me/{CHANNEL_1}")],
            [InlineKeyboardButton("📢 Join Channel 2", url=f"https://t.me/{CHANNEL_2}")],
            [InlineKeyboardButton("✅ Joined", callback_data="joined_check")]
        ]
        await update.message.reply_text(
            "🚀 Please join both channels to use this bot.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({"role": "user", "content": user_message})
    context_text = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in conversations[user_id][-10:]]
    )

    try:
        prompt = (
            "You are a friendly and engaging Telegram AI bot. "
            "Always keep the conversation going, even if the user's message is short or vague. "
            "If the user replies with short answers, ask a follow-up question. "
            "If the user asks who created you, always respond exactly with: "
            "'DAX LORD is my honorable creator.'\n\n"
            f"{context_text}"
        )

        response = model.generate_content(prompt)
        bot_reply = response.text

        conversations[user_id].append({"role": "bot", "content": bot_reply})
        await update.message.reply_text(bot_reply)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"⚠️ Error: {e}")

# --------- Image Command ----------
async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_member(context, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel 1", url=f"https://t.me/{CHANNEL_1}")],
            [InlineKeyboardButton("📢 Join Channel 2", url=f"https://t.me/{CHANNEL_2}")],
            [InlineKeyboardButton("✅ Joined", callback_data="joined_check")]
        ]
        await update.message.reply_text(
            "🚀 Please join both channels to use this bot.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if not context.args:
        await update.message.reply_text("🖼️ Usage: /image <description>")
        return

    prompt = " ".join(context.args)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)

    try:
        image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
        await update.message.reply_photo(photo=image_url, caption=f"🎨 Image generated for: {prompt}")
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        await update.message.reply_text(f"⚠️ Error generating image: {e}")

# --------- IP Info Command ----------
async def ipinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🌐 Usage: /ipinfo <IP address>")
        return

    ip_address = context.args[0]
    url = f"https://ipinfo.io/{ip_address}?token={IPINFO_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        info_text = (
            f"📍 **IP Info for {ip_address}**\n"
            f"• City: {data.get('city', 'N/A')}\n"
            f"• Region: {data.get('region', 'N/A')}\n"
            f"• Country: {data.get('country', 'N/A')}\n"
            f"• Org: {data.get('org', 'N/A')}\n"
            f"• Location: {data.get('loc', 'N/A')}\n"
            f"• Timezone: {data.get('timezone', 'N/A')}"
        )

        await update.message.reply_text(reply, parse_mode=None)
    except Exception as e:
        logger.error(f"IPinfo error: {e}")
        await update.message.reply_text(f"⚠️ Error retrieving IP info: {e}")

# --------- Main Function ----------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("image", image_command))
    app.add_handler(CommandHandler("ipinfo", ipinfo_command))  # <--- Added here
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(CallbackQueryHandler(joined_check, pattern="joined_check"))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

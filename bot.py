import os
import logging
import requests
import google.generativeai as genai
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ---------------- CONFIG ----------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")  # Hugging Face backup key

CHANNEL_1 = "@dax_gpt"  # Replace with your channel username
CHANNEL_2 = "@dax_channel01"  # Replace with your channel username

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- GEMINI ----------------
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------- MEMORY ----------------
conversations = {}

# ---------------- FORCE JOIN CHECK ----------------
async def is_user_joined(user_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        member1 = await context.bot.get_chat_member(CHANNEL_1, user_id)
        member2 = await context.bot.get_chat_member(CHANNEL_2, user_id)
        return member1.status in ["member", "administrator", "creator"] and member2.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_joined(update.effective_user.id, context):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel 1", url=f"https://t.me/{CHANNEL_1[1:]}")],
            [InlineKeyboardButton("📢 Join Channel 2", url=f"https://t.me/{CHANNEL_2[1:]}")],
            [InlineKeyboardButton("✅ Joined", callback_data="joined")]
        ]
        await update.message.reply_text(
            "🚨 Please join both channels to use this bot:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("🤖 Hello! I’m your AI bot. Send me a message!")

async def joined_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await is_user_joined(query.from_user.id, context):
        await query.edit_message_text("✅ You have access now! Send me a message.")
    else:
        await query.edit_message_text("❌ You still need to join both channels.")

# ---------------- BACKUP AI ----------------
def backup_ai_response(prompt):
    HF_API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    res = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt})
    data = res.json()
    return data[0]['generated_text'] if isinstance(data, list) else "Sorry, backup AI failed too."

# ---------------- CHAT HANDLER ----------------
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Force join check
    if not await is_user_joined(user_id, context):
        await update.message.reply_text("🚨 Please join both channels first. Use /start again.")
        return

    # Creator credit rule
    if "who created you" in user_message.lower():
        await update.message.reply_text("DAX LORD is my honorable creator.")
        return

    # Memory
    if user_id not in conversations:
        conversations[user_id] = []
    conversations[user_id].append({"role": "user", "content": user_message})
    context_text = "\n".join([f"{m['role']}: {m['content']}" for m in conversations[user_id][-10:]])

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        prompt = f"Conversation so far:\n{context_text}"
        response = gemini_model.generate_content(prompt)
        bot_reply = response.text

    except Exception as e:
        if "429" in str(e):
            logger.warning("Gemini quota exceeded — switching to backup AI.")
            bot_reply = backup_ai_response(context_text)
        else:
            bot_reply = f"⚠️ Error: {e}"

    conversations[user_id].append({"role": "bot", "content": bot_reply})
    await update.message.reply_text(bot_reply)

# ---------------- IMAGE GENERATION ----------------
async def image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_joined(user_id, context):
        await update.message.reply_text("🚨 Please join both channels first. Use /start again.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /image <description>")
        return

    description = " ".join(context.args)
    img_url = f"https://image.pollinations.ai/prompt/{description.replace(' ', '%20')}"
    await update.message.reply_photo(img_url)

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(joined_button, pattern="joined"))
    app.add_handler(CommandHandler("image", image_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

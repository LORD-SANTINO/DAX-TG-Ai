import os
import logging
import google.generativeai as genai
import requests
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from gtts import gTTS

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
    await update.message.reply_text("🤖 Hello! I’m DAX your AI bot. Send me a message!")

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

    try:
        ip = context.args[0] if context.args else update.effective_message.text.split()[-1]
        response = requests.get(f"https://ipinfo.io/{ip}?token={IPINFO_API_KEY}")
        data = response.json()

        text = (
            f"📍 IP Info for {ip}\n"
            f"• City: {data.get('city', 'N/A')}\n"
            f"• Region: {data.get('region', 'N/A')}\n"
            f"• Country: {data.get('country', 'N/A')}\n"
            f"• Org: {data.get('org', 'N/A')}\n"
            f"• Location: {data.get('loc', 'N/A')}\n"
            f"• Timezone: {data.get('timezone', 'N/A')}"
        )

        await update.message.reply_text(text, parse_mode=None)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error retrieving IP info: {e}", parse_mode=None)

# --------- Text to Speech ----------
async def tts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🔊 Usage: /tts <text>")
        return

    text = " ".join(context.args)
    file_path = "/tmp/tts.mp3"

    try:
        tts = gTTS(text=text, lang="en")
        tts.save(file_path)

        await update.message.reply_voice(voice=open(file_path, "rb"))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error generating speech: {e}")

# --------- Image to File (Catbox) ----------
async def image_to_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if there's a photo in the same message
    if update.message.photo:
        photo = update.message.photo[-1]
    # Or if user replied to a message with a photo
    elif update.message.reply_to_message and update.message.reply_to_message.photo:
        photo = update.message.reply_to_message.photo[-1]
    else:
        await update.message.reply_text("📷 Send `/imgtofile` with an image or reply to an image.")
        return

    # Download the image
    file = await context.bot.get_file(photo.file_id)
    file_path = "/tmp/temp_image.jpg"
    await file.download_to_drive(file_path)

    try:
        with open(file_path, "rb") as f:
            files = {"fileToUpload": f}
            data = {"reqtype": "fileupload"}
            response = requests.post("https://catbox.moe/user/api.php", data=data, files=files)

        if response.status_code == 200:
            await update.message.reply_text(f"✅ Uploaded to Catbox:\n{response.text}")
        else:
            await update.message.reply_text(f"⚠️ Upload failed: {response.status_code}")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error uploading image: {e}")



# --------- Trivia Questions ---------
questions = [
    {
        "question": "What is the capital of France?",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "answer": "Paris"
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "options": ["Earth", "Mars", "Jupiter", "Saturn"],
        "answer": "Mars"
    },
    {
        "question": "Who wrote 'Harry Potter'?",
        "options": ["J.R.R. Tolkien", "J.K. Rowling", "George R.R. Martin", "C.S. Lewis"],
        "answer": "J.K. Rowling"
    }
]

# Store game states { user_id: {score, current_q} }
game_state = {}

# --------- Start Game Command ---------
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    game_state[user_id] = {"score": 0, "current_q": None}
    await send_question(update, context)

# --------- Send Question ---------
async def send_question(update_or_query, context):
    user_id = update_or_query.effective_user.id
    question = random.choice(questions)
    game_state[user_id]["current_q"] = question

    keyboard = [[InlineKeyboardButton(opt, callback_data=f"answer|{opt}")] for opt in question["options"]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if hasattr(update_or_query, "message"):  # From /game command
        await update_or_query.message.reply_text(f"❓ {question['question']}", reply_markup=reply_markup)
    else:  # From callback query
        await update_or_query.edit_message_text(f"❓ {question['question']}", reply_markup=reply_markup)

# --------- Handle Answer ---------
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    chosen = query.data.split("|")[1]
    correct = game_state[user_id]["current_q"]["answer"]

    if chosen == correct:
        game_state[user_id]["score"] += 1
        text = f"✅ Correct! Your score: {game_state[user_id]['score']}"
    else:
        text = f"❌ Wrong! The correct answer was: {correct}\nYour score: {game_state[user_id]['score']}"

    await query.edit_message_text(text)
    await send_question(query, context)

# --------- Main Function ----------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("image", image_command))
    app.add_handler(CommandHandler("ipinfo", ipinfo_command))  # <--- Added here
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(CallbackQueryHandler(joined_check, pattern="joined_check"))
    app.add_handler(CommandHandler("imgtofile", image_to_file))
    app.add_handler(CommandHandler("tts", tts_command))
    app.add_handler(CommandHandler("game", start_game))
    app.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer\|"))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

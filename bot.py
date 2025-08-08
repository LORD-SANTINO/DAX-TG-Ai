import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# === CONFIGURATION ===
BOT_TOKEN = "8209367267:AAEAtSi_oXF3Q_cZfYw0T3jCI_NdRQ36J_E"

# === AES UTILS ===
def encrypt_message(message, password):
    key = password.ljust(32, '0').encode('utf-8')[:32]
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(message.encode('utf-8'), AES.block_size))
    encrypted = base64.b64encode(iv + ct_bytes).decode('utf-8')
    return encrypted

def decrypt_message(ciphertext, password):
    try:
        raw = base64.b64decode(ciphertext)
        iv = raw[:16]
        ct = raw[16:]
        key = password.ljust(32, '0').encode('utf-8')[:32]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size).decode('utf-8')
        return pt
    except Exception as e:
        return f"❌ Error: {e}"

# === COMMANDS ===
def start(update: Update, context: CallbackContext):
    update.message.reply_text("🔐 Welcome to DAX Cipher Bot!\nUse /encrypt or /decrypt.\nExample:\n/encrypt Hello123 password\n/decrypt <ciphertext> password")

def encrypt_cmd(update: Update, context: CallbackContext):
    try:
        text = ' '.join(context.args)
        if len(context.args) < 2:
            raise ValueError("You must provide a message and a password.")
        *msg_parts, password = context.args
        message = ' '.join(msg_parts)
        encrypted = encrypt_message(message, password)
        update.message.reply_text(f"🔒 Encrypted:\n{encrypted}")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")

def decrypt_cmd(update: Update, context: CallbackContext):
    try:
        if len(context.args) < 2:
            raise ValueError("You must provide a ciphertext and a password.")
        *cipher_parts, password = context.args
        ciphertext = ' '.join(cipher_parts)
        decrypted = decrypt_message(ciphertext, password)
        update.message.reply_text(f"🔓 Decrypted:\n{decrypted}")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")

# === MAIN ===
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("encrypt", encrypt_cmd))
    dp.add_handler(CommandHandler("decrypt", decrypt_cmd))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

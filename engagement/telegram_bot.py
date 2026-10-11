from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

# Get absolute path to the root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
env_path = os.path.join(root_dir, '.env')

load_dotenv(env_path)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN or "your_" in BOT_TOKEN or len(BOT_TOKEN) < 10:
    print("ℹ️ Telegram bot token not configured. Exiting bot process safely.")
    sys.exit(0)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    message = f"""
🤖 TalentAI Recruitment Bot

Your Telegram Chat ID is:

{chat_id}

Please copy this ID and paste it in the job application form to receive interview notifications.
"""

    # Check if update.message exists, else use fallback
    if update.message:
        await update.message.reply_text(message)
    else:
        await context.bot.send_message(chat_id=chat_id, text=message)

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.run_polling()
from telegram import Update
from telegram.ext import ContextTypes
from collections import defaultdict
import time

# Simple in-memory spam detection
user_last_message_time = defaultdict(float)
user_message_count = defaultdict(int)
SPAM_THRESHOLD = 5  # messages
SPAM_TIMEFRAME = 10  # seconds


async def delete_join_leave_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and (update.message.new_chat_members or update.message.left_chat_member):
        try:
            await update.message.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")


async def anti_spam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return

    user_id = update.message.from_user.id
    current_time = time.time()

    if current_time - user_last_message_time[user_id] > SPAM_TIMEFRAME:
        user_last_message_time[user_id] = current_time
        user_message_count[user_id] = 1
    else:
        user_message_count[user_id] += 1
        user_last_message_time[user_id] = current_time

    if user_message_count[user_id] > SPAM_THRESHOLD:
        try:
            await update.message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"@{update.message.from_user.username}, please don't spam."
            )
        except Exception as e:
            print(f"Error handling spam: {e}")

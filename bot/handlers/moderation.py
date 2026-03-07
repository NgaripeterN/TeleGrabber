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
    # This handler is for both new members and users who left.
    if update.message and (update.message.new_chat_members or update.message.left_chat_member):
        
        # If a user leaves, ban them.
        if leaver := update.message.left_chat_member:
            # Do not try to ban the bot itself if it gets removed.
            if leaver.id != context.bot.id:
                try:
                    await context.bot.ban_chat_member(
                        chat_id=update.effective_chat.id, user_id=leaver.id
                    )
                    print(f"Banned user {leaver.id} for leaving chat {update.effective_chat.id}")
                except Exception as e:
                    print(f"Failed to ban leaving user {leaver.id}: {e}")

        # In all cases, delete the service message (e.g., "User left" or "User joined").
        try:
            await update.message.delete()
        except Exception as e:
            print(f"Error deleting join/leave service message: {e}")


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

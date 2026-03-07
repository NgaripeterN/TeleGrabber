import re
import time
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import GroupSubscription
from bot.services.media_downloader import download_media
from bot.core.config import OWNER_ID
import os

URL_REGEX = r'(https?://(?:www\.)?(?:twitter\.com|x\.com|reddit\.com)/[^\s]+)'
DOWNLOAD_COOLDOWN = 30  # seconds
group_last_download = {}

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.type == 'private':
        return True
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    return update.effective_user.id in [admin.user.id for admin in admins]


async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    if not update.message or not update.message.text:
        return

    group_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not await is_admin(update, context):
        return

    # Check subscription
    subscription = db.query(GroupSubscription).filter_by(group_id=group_id).first()

    # Owner is always subscribed
    if user_id == OWNER_ID:
        pass
    elif not subscription or not subscription.is_active():
        return
        
    # Rate limit check
    current_time = time.time()
    last_download_time = group_last_download.get(group_id, 0)

    if current_time - last_download_time < DOWNLOAD_COOLDOWN:
        await update.message.reply_text(f"Please wait {int(DOWNLOAD_COOLDOWN - (current_time - last_download_time))} more seconds before downloading another file.")
        return
        
    urls = re.findall(URL_REGEX, update.message.text)
    if not urls:
        return

    group_last_download[group_id] = current_time
    for url in urls:
        status_message = await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Downloading media from {url}..."
        )
        media_path = await download_media(url)
        if media_path:
            try:
                if media_path.endswith(('.mp4', '.mov', '.mkv')):
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id, video=open(media_path, 'rb'), supports_streaming=True
                    )
                else:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id, photo=open(media_path, 'rb')
                    )
                os.remove(media_path)
                await update.message.delete()
                await status_message.delete()
            except Exception as e:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text=f"Failed to send media: {e}"
                )
        else:
            await status_message.edit_text(text="Failed to download media.")

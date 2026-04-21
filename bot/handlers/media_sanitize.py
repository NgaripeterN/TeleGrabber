import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.media_sanitizer import sanitize_media_file


async def media_sanitizer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    message = update.message
    file_id = None
    media_type = None
    input_suffix = ".bin"

    if message.photo:
        file_id = message.photo[-1].file_id
        media_type = "image"
        input_suffix = ".jpg"
    elif message.video:
        file_id = message.video.file_id
        media_type = "video"
        input_suffix = ".mp4"
    elif message.document:
        mime_type = (message.document.mime_type or "").lower()
        if mime_type.startswith("image/"):
            file_id = message.document.file_id
            media_type = "image"
            input_suffix = ".jpg"
        elif mime_type.startswith("video/"):
            file_id = message.document.file_id
            media_type = "video"
            input_suffix = ".mp4"

    if not file_id or not media_type:
        return

    status_message = await message.reply_text("Removing metadata...")
    input_path = None
    output_path = None

    try:
        telegram_file = await context.bot.get_file(file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=input_suffix) as input_file:
            input_path = input_file.name

        await telegram_file.download_to_drive(custom_path=input_path)
        output_path = await sanitize_media_file(input_path, media_type)

        if not output_path:
            await status_message.edit_text("Failed to process this media.")
            return

        with open(output_path, "rb") as cleaned_file:
            if media_type == "video":
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=cleaned_file,
                    caption=message.caption,
                    supports_streaming=True,
                )
            else:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=cleaned_file,
                    caption=message.caption,
                )

        await status_message.delete()
    except Exception as e:
        print(f"Error in media sanitizer handler: {e}")
        try:
            await status_message.edit_text("Failed to process this media.")
        except Exception:
            pass
    finally:
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)

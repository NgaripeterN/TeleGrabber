import asyncio
import os
from fastapi import FastAPI, Request, Depends
from sqlalchemy.orm import Session
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes,
)

from bot.core.config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL
from bot.database.database import engine, Base, get_db
from bot.database.models import GroupSubscription
from bot.handlers.media import media_handler
from bot.handlers.media_sanitize import media_sanitizer_handler
from bot.handlers.moderation import (
    delete_join_leave_messages,
    anti_spam_handler,
)
from bot.handlers.subscription import (
    start_command,
    subscribe_command,
    precheckout_callback,
    successful_payment_callback,
    status_command,
    set_caption_command,
    grant_subscription_command,
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Telegram Bot Application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# FastAPI App
app = FastAPI()

@app.on_event("startup")
async def startup():
    # Initialize the bot application
    await application.initialize()
    # The webhook URL should point to the root of your service, where the webhook handler is.
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/")
    
    # Set bot commands for the / menu
    commands = [
        BotCommand("start", "Welcome message"),
        BotCommand("subscribe", "Subscribe the group to the bot"),
        BotCommand("status", "Check subscription status"),
        BotCommand("setcaption", "Set a custom caption for downloaded media"),
    ]
    await application.bot.set_my_commands(commands)


@app.on_event("shutdown")
async def shutdown():
    # Cleanly shut down the bot application
    await application.shutdown()
    await application.bot.delete_webhook()


async def db_decorator(handler, update: Update, context: ContextTypes.DEFAULT_TYPE):
    db: Session = next(get_db())
    try:
        await handler(update, context, db=db)
    finally:
        db.close()


@app.post("/")
async def webhook(request: Request):
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"status": "ok"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return {"status": "ok"}


# Command Handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("status", lambda u, c: db_decorator(status_command, u, c)))
application.add_handler(CommandHandler("subscribe", lambda u, c: db_decorator(subscribe_command, u, c)))
application.add_handler(CommandHandler("setcaption", lambda u, c: db_decorator(set_caption_command, u, c)))
application.add_handler(CommandHandler("grant", lambda u, c: db_decorator(grant_subscription_command, u, c)))

# Message Handlers
application.add_handler(
    MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER,
        delete_join_leave_messages,
    )
)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: db_decorator(media_handler, u, c)))
application.add_handler(
    MessageHandler(
        (filters.PHOTO | filters.VIDEO | filters.Document.IMAGE | filters.Document.VIDEO) & ~filters.COMMAND,
        media_sanitizer_handler,
    )
)
application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, anti_spam_handler))

# Payment Handlers
application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
application.add_handler(
    MessageHandler(filters.SUCCESSFUL_PAYMENT, lambda u, c: db_decorator(successful_payment_callback, u, c))
)

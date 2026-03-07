import asyncio
from fastapi import FastAPI, Request, Depends
from sqlalchemy.orm import Session
from telegram import Update
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
    # The webhook URL should point to the root of your service, where the webhook handler is.
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/")


@app.on_event("shutdown")
async def shutdown():
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
application.add_handler(CommandHandler("grant", lambda u, c: db_decorator(grant_subscription_command, u, c)))

# Message Handlers
application.add_handler(
    MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER,
        delete_join_leave_messages,
    )
)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: db_decorator(media_handler, u, c)))
application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, anti_spam_handler))

# Payment Handlers
application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
application.add_handler(
    MessageHandler(filters.SUCCESSFUL_PAYMENT, lambda u, c: db_decorator(successful_payment_callback, u, c))
)

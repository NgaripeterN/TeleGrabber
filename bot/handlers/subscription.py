from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import GroupSubscription
from bot.core.config import INVOICE_TITLE, INVOICE_DESCRIPTION, CURRENCY, PRICE, OWNER_ID
import datetime


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am a bot that can help you with group management and media downloading. "
        "Add me to your group and make me an admin to get started.

"
        "To subscribe, use the /subscribe command."
    )


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    admins = await context.bot.get_chat_administrators(chat_id)
    if user_id not in [admin.user.id for admin in admins] and user_id != OWNER_ID:
        await update.message.reply_text("Only admins can subscribe.")
        return

    payload = f"{chat_id}_{user_id}"
    await context.bot.send_invoice(
        chat_id=user_id,
        title=INVOICE_TITLE,
        description=INVOICE_DESCRIPTION,
        payload=payload,
        provider_token=None,  # For Telegram Stars, no provider token is needed
        currency=CURRENCY,
        prices=[LabeledPrice("Subscription", PRICE)],
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    payload = update.message.successful_payment.invoice_payload
    chat_id, user_id = map(int, payload.split("_"))

    subscription = db.query(GroupSubscription).filter_by(group_id=chat_id).first()
    if not subscription:
        subscription = GroupSubscription(group_id=chat_id, subscriber_id=user_id)
        db.add(subscription)

    subscription.subscribed = True
    subscription.expiry_date = datetime.datetime.utcnow() + datetime.timedelta(days=30)
    db.commit()

    await context.bot.send_message(
        chat_id=chat_id, text="Subscription successful! The bot is now active for 30 days."
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    group_id = update.effective_chat.id
    subscription = db.query(GroupSubscription).filter_by(group_id=group_id).first()

    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text("You are the owner. The bot is always active for you.")
        return
        
    if subscription and subscription.is_active():
        await update.message.reply_text(
            f"Subscription is active. Expires on: {subscription.expiry_date.strftime('%Y-%m-%d')}"
        )
    else:
        await update.message.reply_text("No active subscription found.")


async def grant_subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("This command is only for the bot owner.")
        return

    try:
        group_id = int(context.args[0])
        days = int(context.args[1]) if len(context.args) > 1 else 30
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /grant <group_id> [days]")
        return

    subscription = db.query(GroupSubscription).filter_by(group_id=group_id).first()
    if not subscription:
        subscription = GroupSubscription(group_id=group_id, subscriber_id=OWNER_ID)
        db.add(subscription)

    subscription.subscribed = True
    subscription.expiry_date = datetime.datetime.utcnow() + datetime.timedelta(days=days)
    db.commit()

    await update.message.reply_text(f"Subscription granted to group {group_id} for {days} days.")

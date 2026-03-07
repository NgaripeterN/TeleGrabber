import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
DATABASE_URL = os.getenv("DATABASE_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Bot settings
INVOICE_TITLE = "Bot Subscription"
INVOICE_DESCRIPTION = "Monthly subscription for the bot"
CURRENCY = "XTR"
PRICE = 100  # 100 stars

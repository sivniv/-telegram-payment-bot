import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TRANSACTIONS_FILE = 'transactions.json'
PAYMENT_SYSTEM_IDENTIFIER = 'kb_prasac_merchant_payment'
DAILY_REPORT_TIME = "09:00"  # 24-hour format
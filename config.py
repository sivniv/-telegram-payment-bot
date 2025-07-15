"""Configuration module for Telegram Payment Bot."""

import os

from dotenv import load_dotenv

load_dotenv()

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# File paths
TRANSACTIONS_FILE = "transactions.json"
CLIENTS_FILE = "clients.json"
GROUP_SETTINGS_FILE = "group_settings.json"

# Payment system settings
PAYMENT_SYSTEM_IDENTIFIER = "kb_prasac_merchant_payment"
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
TRANSACTION_TIMEOUT_HOURS = int(os.getenv("TRANSACTION_TIMEOUT_HOURS", "24"))

# Scheduler settings
DAILY_REPORT_TIME = "09:00"  # 24-hour format

# Feature flags
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"

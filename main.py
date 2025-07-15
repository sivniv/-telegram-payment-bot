#!/usr/bin/env python3
"""
Simple Payment Bot - No Authentication Version
For testing and simple deployments
"""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN
from group_settings import GroupSettingsManager
from payment_parser import PaymentParser
from transaction_storage import TransactionStorage

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
parser = PaymentParser()
storage = TransactionStorage()
settings_manager = GroupSettingsManager()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and parse payment notifications."""
    if not update.message or not update.message.text:
        return

    message_text = update.message.text
    group_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id) if update.effective_user else "unknown"

    # Try to parse as payment notification (no authentication required)
    transaction = parser.parse_payment(message_text, group_id)
    if transaction:
        success = storage.save_transaction(transaction)
        if success:
            logger.info(
                f"💰 Payment recorded: ${transaction['amount']} from {transaction['payer']} via {transaction['source']}"
            )


async def cmd_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate daily report for today."""
    user = update.effective_user
    user_info = f"@{user.username}" if user.username else f"{user.first_name}"

    date_str = datetime.now().strftime("%Y-%m-%d")
    summary = storage.get_daily_summary(date_str)

    if summary["transaction_count"] == 0:
        await update.message.reply_text(f"📊 No transactions found for {date_str}")
        logger.info(f"DAILY command used by: {user_info} (ID: {user.id}) - No transactions")
        return

    report = f"📊 Daily Report - {date_str}\n\n"
    report += f"💰 Total: ${summary['total_amount']:.2f} USD\n"
    report += f"📝 Count: {summary['transaction_count']}\n\n"

    for i, t in enumerate(summary["transactions"], 1):
        report += f"{i}. ${t['amount']:.2f} - {t['payer']}\n"

    await update.message.reply_text(report)
    logger.info(
        f"DAILY command used by: {user_info} (ID: {user.id}) - Showed {summary['transaction_count']} transactions"
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    try:
        user = update.effective_user
        user_info = f"@{user.username}" if user.username else f"{user.first_name}"

        welcome_text = "👋 Welcome to Payment Bot!\n\n"
        welcome_text += "I track payment notifications automatically.\n\n"
        welcome_text += "Commands:\n"
        welcome_text += "/daily - Today's report\n"
        welcome_text += "/help - Show help"

        await update.message.reply_text(welcome_text)
        logger.info(f"START command used by: {user_info} (ID: {user.id})")
    except Exception as e:
        logger.error(f"Error in start command: {e}")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message."""
    try:
        user = update.effective_user
        user_info = f"@{user.username}" if user.username else f"{user.first_name}"

        help_text = "🤖 Payment Bot Commands\n\n"
        help_text += "📊 Reports:\n"
        help_text += "/daily - Today's payment report\n"
        help_text += "/start - Welcome message\n"
        help_text += "/help - Show this help\n\n"
        help_text += "I automatically track payment notifications from various sources."

        await update.message.reply_text(help_text)
        logger.info(f"HELP command used by: {user_info} (ID: {user.id})")
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await update.message.reply_text("Bot is working! ✅")


def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Bot token not found! Check your .env file")
        return

    print("🚀 Starting Simple Payment Bot (No Auth)...")

    # Create application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("daily", cmd_daily_report))
    app.add_handler(CommandHandler("help", cmd_help))

    print("✅ Simple bot is running! Send /help in your group to test.")

    # Start polling
    app.run_polling()


if __name__ == "__main__":
    main()

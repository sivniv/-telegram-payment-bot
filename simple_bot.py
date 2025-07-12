#!/usr/bin/env python3
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from payment_parser import PaymentParser
from transaction_storage import TransactionStorage
from config import TELEGRAM_BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
parser = PaymentParser()
storage = TransactionStorage()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and parse payment notifications."""
    if not update.message or not update.message.text:
        return
    
    message_text = update.message.text
    
    # Try to parse as payment notification
    transaction = parser.parse_payment(message_text)
    if transaction:
        success = storage.save_transaction(transaction)
        if success:
            logger.info(f"💰 Payment recorded: ${transaction['amount']} from {transaction['payer']}")

async def cmd_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate daily report for today."""
    date_str = datetime.now().strftime('%Y-%m-%d')
    summary = storage.get_daily_summary(date_str)
    
    if summary['transaction_count'] == 0:
        await update.message.reply_text(f"📊 No transactions found for {date_str}")
        return
    
    report = f"📊 Daily Report - {date_str}\n\n"
    report += f"💰 Total: ${summary['total_amount']:.2f} USD\n"
    report += f"📝 Count: {summary['transaction_count']}\n\n"
    
    for i, t in enumerate(summary['transactions'], 1):
        report += f"{i}. ${t['amount']:.2f} - {t['payer']}\n"
    
    await update.message.reply_text(report)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    try:
        welcome_text = "👋 Welcome to Payment Bot!\n\n"
        welcome_text += "I track kb_prasac_merchant_payment notifications.\n\n"
        welcome_text += "Commands:\n"
        welcome_text += "/daily - Today's report\n"
        welcome_text += "/help - Show help"
        
        await update.message.reply_text(welcome_text)
        logger.info("Start command executed successfully")
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message."""
    try:
        help_text = "🤖 Payment Bot Commands\n\n"
        help_text += "/daily - Today's payment report\n"
        help_text += "/help - Show this help\n"
        help_text += "/start - Welcome message\n\n"
        help_text += "I automatically track kb_prasac_merchant_payment notifications."
        
        await update.message.reply_text(help_text)
        logger.info("Help command executed successfully")
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await update.message.reply_text("Bot is working! ✅")

def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Bot token not found! Check your .env file")
        return
    
    print("🚀 Starting Payment Bot...")
    
    # Create application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("daily", cmd_daily_report))
    app.add_handler(CommandHandler("help", cmd_help))
    
    print("✅ Bot is running! Send /help in your group to test.")
    
    # Start polling
    app.run_polling()

if __name__ == "__main__":
    main()

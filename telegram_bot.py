import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from payment_parser import PaymentParser
from transaction_storage import TransactionStorage
from config import TELEGRAM_BOT_TOKEN

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PaymentBot:
    def __init__(self):
        self.parser = PaymentParser()
        self.storage = TransactionStorage()
        self.app = None
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages and parse payment notifications."""
        if not update.message or not update.message.text:
            return
        
        message_text = update.message.text
        
        # Try to parse as payment notification
        transaction = self.parser.parse_payment(message_text)
        if transaction:
            success = self.storage.save_transaction(transaction)
            if success:
                logger.info(f"Saved transaction: {transaction['amount']} USD from {transaction['payer']}")
                # Optionally send confirmation (uncomment if needed)
                # await update.message.reply_text(f"✅ Payment recorded: ${transaction['amount']} from {transaction['payer']}")
    
    async def cmd_daily_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate daily report for today or specified date."""
        if context.args:
            try:
                # User specified a date
                date_str = context.args[0]
                datetime.strptime(date_str, '%Y-%m-%d')  # Validate format
            except (ValueError, IndexError):
                await update.message.reply_text("❌ Invalid date format. Use YYYY-MM-DD")
                return
        else:
            # Default to today
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        summary = self.storage.get_daily_summary(date_str)
        
        if summary['transaction_count'] == 0:
            await update.message.reply_text(f"📊 No transactions found for {date_str}")
            return
        
        report = f"📊 **Daily Report - {date_str}**\n\n"
        report += f"💰 Total Amount: ${summary['total_amount']:.2f} USD\n"
        report += f"📝 Transaction Count: {summary['transaction_count']}\n\n"
        report += "**Transactions:**\n"
        
        for i, transaction in enumerate(summary['transactions'], 1):
            report += f"{i}. ${transaction['amount']:.2f} - {transaction['payer']}\n"
        
        await update.message.reply_text(report, parse_mode='Markdown')
    
    async def cmd_weekly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate summary report for all transactions."""
        summary = self.storage.get_all_time_summary()
        
        if summary['transaction_count'] == 0:
            await update.message.reply_text("📊 No transactions found")
            return
        
        report = f"📊 **All-Time Summary**\n\n"
        report += f"💰 Total Amount: ${summary['total_amount']:.2f} USD\n"
        report += f"📝 Transaction Count: {summary['transaction_count']}\n\n"
        
        if summary['daily_totals']:
            report += "**Daily Breakdown:**\n"
            for date, total in sorted(summary['daily_totals'].items(), reverse=True)[:10]:  # Last 10 days
                report += f"{date}: ${total:.2f}\n"
        
        await update.message.reply_text(report, parse_mode='Markdown')
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message with available commands."""
        help_text = """
🤖 **Payment Bot Commands**

/daily - Today's payment report
/daily YYYY-MM-DD - Specific date report
/summary - All-time summary
/help - Show this help message

The bot automatically tracks payments from kb_prasac_merchant_payment notifications.
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    def run_bot(self):
        """Start the Telegram bot."""
        if not TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
            return
        
        # Create application
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.app.add_handler(CommandHandler("daily", self.cmd_daily_report))
        self.app.add_handler(CommandHandler("summary", self.cmd_weekly_report))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        
        logger.info("Starting Telegram Payment Bot...")
        
        # Start the bot
        self.app.run_polling()

if __name__ == "__main__":
    bot = PaymentBot()
    bot.run_bot()
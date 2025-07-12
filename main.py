#!/usr/bin/env python3
"""
Telegram Payment Bot - Main Entry Point

This bot monitors group chats for kb_prasac_merchant_payment notifications,
parses payment information, stores it in JSON, and provides reporting features.
"""

import logging
import sys
from telegram_bot import PaymentBot
from scheduler import DailyReportScheduler

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to start the payment bot."""
    logger.info("Starting Telegram Payment Bot...")
    
    try:
        # Create and start the bot
        bot = PaymentBot()
        
        # Optional: Start scheduler for daily reports
        # Uncomment and set group_chat_id to enable automatic daily reports
        # scheduler = DailyReportScheduler(group_chat_id="YOUR_GROUP_CHAT_ID")
        # scheduler.start_scheduler()
        
        # Start the bot (this will block)
        bot.run_bot()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
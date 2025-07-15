import asyncio
import threading
import time
from datetime import datetime

import schedule
from telegram import Bot

from config import DAILY_REPORT_TIME, TELEGRAM_BOT_TOKEN
from transaction_storage import TransactionStorage


class DailyReportScheduler:
    def __init__(self, group_chat_id: str = None):
        self.storage = TransactionStorage()
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
        self.group_chat_id = group_chat_id
        self.running = False

    def generate_daily_report(self):
        """Generate and send daily report."""
        if not self.bot or not self.group_chat_id:
            print("Bot token or group chat ID not configured for scheduled reports")
            return

        yesterday = datetime.now().strftime("%Y-%m-%d")
        summary = self.storage.get_daily_summary(yesterday)

        if summary["transaction_count"] == 0:
            report = f"📊 **Daily Report - {yesterday}**\n\nNo transactions recorded today."
        else:
            report = f"📊 **Daily Report - {yesterday}**\n\n"
            report += f"💰 Total Amount: ${summary['total_amount']:.2f} USD\n"
            report += f"📝 Transaction Count: {summary['transaction_count']}\n\n"
            report += "**Transactions:**\n"

            for i, transaction in enumerate(summary["transactions"], 1):
                report += f"{i}. ${transaction['amount']:.2f} - {transaction['payer']}\n"

        # Send the report
        asyncio.create_task(self.send_report(report))

    async def send_report(self, report: str):
        """Send report to the group chat."""
        try:
            await self.bot.send_message(
                chat_id=self.group_chat_id, text=report, parse_mode="Markdown"
            )
            print(f"Daily report sent at {datetime.now()}")
        except Exception as e:
            print(f"Error sending daily report: {e}")

    def schedule_daily_reports(self):
        """Schedule daily reports."""
        schedule.every().day.at(DAILY_REPORT_TIME).do(self.generate_daily_report)
        print(f"Daily reports scheduled for {DAILY_REPORT_TIME}")

    def start_scheduler(self):
        """Start the scheduler in a separate thread."""
        if self.running:
            return

        self.running = True
        self.schedule_daily_reports()

        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print("Scheduler started")

    def stop_scheduler(self):
        """Stop the scheduler."""
        self.running = False
        schedule.clear()
        print("Scheduler stopped")

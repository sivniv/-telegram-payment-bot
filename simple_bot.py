#!/usr/bin/env python3
"""
Payment Bot SaaS - Multi-tenant Telegram Payment Tracking Bot
Copyright (c) 2025 Sochetra. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution,
or use of this software is strictly prohibited.
"""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from admin_interface import (
    cmd_add_group,
    cmd_admin_help,
    cmd_client_info,
    cmd_create_client,
    cmd_list_clients,
    cmd_system_stats,
    cmd_upgrade_client,
)
from admin_utils import admin_only_command, get_user_info
from auth_middleware import AuthMiddleware, require_auth, require_feature
from client_manager import ClientManager
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
auth_middleware = AuthMiddleware()
client_manager = ClientManager()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and parse payment notifications."""
    if not update.message or not update.message.text:
        return

    # Authenticate the group first
    client = await auth_middleware.authenticate_group(update, context)
    if not client:
        return  # Unauthorized group or inactive subscription

    message_text = update.message.text
    group_id = str(update.effective_chat.id)

    # Try to parse as payment notification
    transaction = parser.parse_payment(message_text, group_id)
    if transaction:
        # Add client information to transaction
        transaction["client_id"] = client["client_id"]

        success = storage.save_transaction(transaction)
        if success:
            # Log transaction for billing
            auth_middleware.log_transaction(client, transaction)
            logger.info(
                f"💰 Payment recorded for client {client['client_id']}: ${transaction['amount']} from {transaction['payer']} via {transaction['source']}"
            )


@require_auth
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


@require_auth
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    try:
        user = update.effective_user
        user_info = f"@{user.username}" if user.username else f"{user.first_name}"

        welcome_text = "👋 Welcome to Payment Bot!\n\n"
        welcome_text += "I track kb_prasac_merchant_payment notifications.\n\n"
        welcome_text += "Commands:\n"
        welcome_text += "/daily - Today's report\n"
        welcome_text += "/help - Show help"

        await update.message.reply_text(welcome_text)
        logger.info(f"START command used by: {user_info} (ID: {user.id})")
    except Exception as e:
        logger.error(f"Error in start command: {e}")


@require_auth
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message."""
    try:
        user = update.effective_user
        user_info = f"@{user.username}" if user.username else f"{user.first_name}"

        help_text = "🤖 Payment Bot Commands\n\n"
        help_text += "📊 Reports:\n"
        help_text += "/daily - Today's payment report\n"
        help_text += "/start - Welcome message\n\n"
        help_text += "⚙️ Configuration (Admin only):\n"
        help_text += "/config - Show current settings\n"
        help_text += "/sources - List available payment sources\n"
        help_text += "/set_source <source> - Set payment source\n\n"
        help_text += "/help - Show this help\n\n"
        help_text += "I automatically track payment notifications from various sources."

        await update.message.reply_text(help_text)
        logger.info(f"HELP command used by: {user_info} (ID: {user.id})")
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await update.message.reply_text("Bot is working! ✅")


@require_auth
@require_feature("multi_payment_sources")
async def cmd_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current group configuration."""
    if not await admin_only_command(update, context):
        return

    try:
        group_id = str(update.effective_chat.id)
        user_info = get_user_info(update)

        settings = settings_manager.get_group_settings(group_id)
        config = settings_manager.get_payment_config(group_id)

        config_text = "⚙️ Current Configuration\n\n"
        config_text += f"💳 Payment Source: {config.get('name', 'Unknown')}\n"
        config_text += f"🔧 Identifier: {config.get('identifier', 'N/A')}\n"
        config_text += (
            f"📱 Status: {'✅ Enabled' if settings.get('enabled', True) else '❌ Disabled'}\n"
        )
        config_text += f"👑 Admin Only Config: {'Yes' if settings.get('admin_only_config', True) else 'No'}\n\n"
        config_text += f"Description: {config.get('description', 'No description available')}"

        await update.message.reply_text(config_text)
        logger.info(f"CONFIG command used by: {user_info['display_name']} (ID: {user_info['id']})")

    except Exception as e:
        logger.error(f"Error in config command: {e}")
        await update.message.reply_text("❌ Error retrieving configuration.")


@require_auth
@require_feature("multi_payment_sources")
async def cmd_sources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List available payment sources."""
    if not await admin_only_command(update, context):
        return

    try:
        user_info = get_user_info(update)
        sources = settings_manager.get_available_sources()

        sources_text = "💳 Available Payment Sources\n\n"
        for key, source in sources.items():
            sources_text += f"🔹 {source['name']}\n"
            sources_text += f"   Command: /set_source {key}\n"
            sources_text += f"   {source['description']}\n\n"

        sources_text += "💡 Usage: /set_source <source_key>"

        await update.message.reply_text(sources_text)
        logger.info(f"SOURCES command used by: {user_info['display_name']} (ID: {user_info['id']})")

    except Exception as e:
        logger.error(f"Error in sources command: {e}")
        await update.message.reply_text("❌ Error retrieving payment sources.")


@require_auth
@require_feature("multi_payment_sources")
async def cmd_set_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set payment source for the group."""
    if not await admin_only_command(update, context):
        return

    try:
        group_id = str(update.effective_chat.id)
        user_info = get_user_info(update)

        if not context.args:
            await update.message.reply_text(
                "❌ Please specify a payment source.\nUsage: /set_source <source>\n\nUse /sources to see available options."
            )
            return

        source_key = context.args[0].lower()
        available_sources = settings_manager.get_available_sources()

        if source_key not in available_sources:
            await update.message.reply_text(
                f"❌ Unknown payment source: {source_key}\n\nUse /sources to see available options."
            )
            return

        success = settings_manager.set_payment_source(group_id, source_key)

        if success:
            source_info = available_sources[source_key]
            success_text = f"✅ Payment source updated!\n\n"
            success_text += f"💳 Now tracking: {source_info['name']}\n"
            success_text += f"🔧 Identifier: {source_info['identifier']}\n"
            success_text += f"📝 Description: {source_info['description']}"

            await update.message.reply_text(success_text)
            logger.info(
                f"SET_SOURCE command used by: {user_info['display_name']} - Changed to {source_key}"
            )
        else:
            await update.message.reply_text("❌ Failed to update payment source.")

    except Exception as e:
        logger.error(f"Error in set_source command: {e}")
        await update.message.reply_text("❌ Error updating payment source.")


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
    app.add_handler(CommandHandler("config", cmd_config))
    app.add_handler(CommandHandler("sources", cmd_sources))
    app.add_handler(CommandHandler("set_source", cmd_set_source))

    # Admin commands
    app.add_handler(CommandHandler("admin_help", cmd_admin_help))
    app.add_handler(CommandHandler("admin_create_client", cmd_create_client))
    app.add_handler(CommandHandler("admin_list_clients", cmd_list_clients))
    app.add_handler(CommandHandler("admin_client_info", cmd_client_info))
    app.add_handler(CommandHandler("admin_upgrade_client", cmd_upgrade_client))
    app.add_handler(CommandHandler("admin_add_group", cmd_add_group))
    app.add_handler(CommandHandler("admin_stats", cmd_system_stats))

    print("✅ Bot is running! Send /help in your group to test.")

    # Start polling
    app.run_polling()


if __name__ == "__main__":
    main()

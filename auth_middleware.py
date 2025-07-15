"""
Authentication Middleware for Payment Bot SaaS
Copyright (c) 2025 Sochetra. All rights reserved.
"""

import logging
from typing import Any, Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes

from client_manager import ClientManager

logger = logging.getLogger(__name__)


class AuthMiddleware:
    def __init__(self):
        self.client_manager = ClientManager()

    async def authenticate_group(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Authenticate group and return client data if valid."""
        if not update.effective_chat:
            return None

        group_id = str(update.effective_chat.id)

        # Find client that owns this group
        client = self.client_manager.get_client_by_group(group_id)

        if not client:
            logger.warning(f"Unauthorized group access attempt: {group_id}")
            return None

        # Check if client is active
        if client.get("status") != "active":
            logger.warning(f"Inactive client attempted access: {client.get('client_id')}")
            await self._send_subscription_message(update)
            return None

        # Check usage limits
        usage_check = self.client_manager.check_usage_limits(client["client_id"])
        if not usage_check["allowed"]:
            logger.warning(f"Usage limit exceeded for client: {client.get('client_id')}")
            await self._send_limit_exceeded_message(update, usage_check["reason"])
            return None

        return client

    async def _send_subscription_message(self, update: Update):
        """Send message about inactive subscription."""
        message = """
🚫 **Subscription Inactive**

Your Payment Bot subscription is currently inactive. Please contact your administrator to renew your subscription.

For support: support@paymentbot.com
        """
        try:
            await update.message.reply_text(message, parse_mode="Markdown")
        except:
            pass

    async def _send_limit_exceeded_message(self, update: Update, reason: str):
        """Send message about usage limits."""
        message = f"""
⚠️ **Usage Limit Reached**

{reason}

Please upgrade your plan or wait for the next billing cycle.

Contact support: support@paymentbot.com
        """
        try:
            await update.message.reply_text(message, parse_mode="Markdown")
        except:
            pass

    def check_feature_access(self, client: Dict[str, Any], feature: str) -> bool:
        """Check if client has access to a specific feature."""
        if not client:
            return False

        plan = client.get("plan", "free")
        plan_features = self.client_manager.plans.get(plan, {}).get("features", [])

        return feature in plan_features or "unlimited_everything" in plan_features

    def log_transaction(self, client: Dict[str, Any], transaction_data: Dict[str, Any]):
        """Log transaction for billing and analytics."""
        if client:
            client_id = client.get("client_id")
            self.client_manager.increment_usage(client_id, 1)

            # Log transaction details for analytics
            logger.info(
                f"Transaction recorded for client {client_id}: ${transaction_data.get('amount')} from {transaction_data.get('payer')}"
            )


def require_auth(func):
    """Decorator to require authentication for bot commands."""

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        auth = AuthMiddleware()
        client = await auth.authenticate_group(update, context)

        if not client:
            return  # Authentication failed, message already sent

        # Add client data to context for use in the command
        context.user_data["client"] = client

        return await func(update, context, *args, **kwargs)

    return wrapper


def require_feature(feature_name: str):
    """Decorator to require specific feature access."""

    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            auth = AuthMiddleware()
            client = context.user_data.get("client")

            if not client:
                # Try to authenticate first
                client = await auth.authenticate_group(update, context)
                if not client:
                    return

            if not auth.check_feature_access(client, feature_name):
                await update.message.reply_text(
                    f"❌ This feature ({feature_name}) is not available in your current plan. Please upgrade to access this feature."
                )
                return

            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator

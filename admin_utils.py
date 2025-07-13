from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin in the current chat."""
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Get chat administrators
        admins = await context.bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in admins]
        
        return user_id in admin_ids
    
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def admin_only_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Decorator-like function to check admin permissions before command execution."""
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ This command is only available to group administrators.")
        return False
    return True

def get_user_info(update: Update) -> dict:
    """Get user information from update."""
    user = update.effective_user
    return {
        'id': user.id,
        'username': f"@{user.username}" if user.username else None,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'display_name': f"@{user.username}" if user.username else user.first_name
    }
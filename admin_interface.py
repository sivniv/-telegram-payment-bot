"""
Admin Interface for Payment Bot SaaS Management
Copyright (c) 2025 Sochetra. All rights reserved.
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from client_manager import ClientManager
from auth_middleware import AuthMiddleware

logger = logging.getLogger(__name__)

class AdminInterface:
    def __init__(self, admin_user_ids: list = None):
        self.client_manager = ClientManager()
        self.auth_middleware = AuthMiddleware()
        # Add your Telegram user ID here for admin access
        self.admin_user_ids = admin_user_ids or []  # Add your user ID: [123456789]
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin."""
        return user_id in self.admin_user_ids
    
    async def cmd_admin_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin commands."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        help_text = """
🔧 **Admin Commands**

**Client Management:**
/admin_create_client <email> <company> [plan] - Create new client
/admin_list_clients - List all clients
/admin_client_info <client_id> - Get client details
/admin_upgrade_client <client_id> <plan> - Upgrade client plan
/admin_suspend_client <client_id> - Suspend client
/admin_activate_client <client_id> - Activate client

**Group Management:**
/admin_add_group <client_id> <group_id> <group_name> - Add group to client
/admin_remove_group <client_id> <group_id> - Remove group from client

**Analytics:**
/admin_stats - Show system statistics
/admin_usage <client_id> - Show client usage

**Plans:**
• free: $0/month, 1,000 transactions, 1 group
• basic: $4.99/month, 3,000 transactions, 1 group  
• premium: $9.99/month, 10,000 transactions, 3 groups
• enterprise: $19.99/month, 100,000 transactions, 10 groups
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def cmd_create_client(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a new client account."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /admin_create_client <email> <company> [plan]")
            return
        
        email = context.args[0]
        company = context.args[1]
        plan = context.args[2] if len(context.args) > 2 else 'free'
        
        if plan not in self.client_manager.plans:
            await update.message.reply_text(f"❌ Invalid plan. Available: {', '.join(self.client_manager.plans.keys())}")
            return
        
        try:
            result = self.client_manager.create_client(email, company, plan)
            
            response = f"""
✅ **Client Created Successfully**

🆔 Client ID: `{result['client_id']}`
🔑 API Key: `{result['api_key']}`
📧 Email: {email}
🏢 Company: {company}
📊 Plan: {plan}

⚠️ **Important:** Save the API key securely. It won't be shown again.
            """
            
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"Admin {update.effective_user.id} created client: {email}")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error creating client: {str(e)}")
            logger.error(f"Error creating client: {e}")
    
    async def cmd_list_clients(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all clients."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        try:
            clients = self.client_manager.list_clients()
            
            if not clients:
                await update.message.reply_text("📭 No clients found.")
                return
            
            response = "👥 **All Clients**\n\n"
            
            for client in clients[:10]:  # Show first 10
                response += f"🏢 {client['company_name']}\n"
                response += f"   📧 {client['email']}\n"
                response += f"   🆔 `{client['client_id'][:8]}...`\n"
                response += f"   📊 {client['plan'].title()} Plan\n"
                response += f"   📱 {client['status'].title()}\n"
                response += f"   🏘️ {client['groups_count']} groups\n"
                response += f"   📊 {client['monthly_transactions']} transactions\n\n"
            
            if len(clients) > 10:
                response += f"... and {len(clients) - 10} more clients"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error listing clients: {str(e)}")
    
    async def cmd_client_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get detailed client information."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /admin_client_info <client_id>")
            return
        
        client_id = context.args[0]
        client = self.client_manager.get_client(client_id)
        
        if not client:
            await update.message.reply_text("❌ Client not found.")
            return
        
        plan_info = self.client_manager.plans[client['plan']]
        usage = client.get('monthly_usage', {})
        
        response = f"""
👤 **Client Details**

🏢 **Company:** {client['company_name']}
📧 **Email:** {client['email']}
🆔 **Client ID:** `{client['client_id']}`
📊 **Plan:** {plan_info['name']} (${plan_info['price']}/month)
📱 **Status:** {client['status'].title()}
📅 **Created:** {client['created_at'][:10]}

📊 **Usage This Month:**
• Transactions: {usage.get('transactions', 0)}/{plan_info['monthly_transactions'] if plan_info['monthly_transactions'] != -1 else '∞'}
• Groups: {len(client.get('groups', []))}/{plan_info['groups_limit'] if plan_info['groups_limit'] != -1 else '∞'}

🏘️ **Groups:**
        """
        
        for group in client.get('groups', []):
            response += f"• {group['group_name']} (`{group['group_id']}`)\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def cmd_upgrade_client(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Upgrade client plan."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if len(context.args) != 2:
            await update.message.reply_text("Usage: /admin_upgrade_client <client_id> <new_plan>")
            return
        
        client_id, new_plan = context.args
        
        if new_plan not in self.client_manager.plans:
            await update.message.reply_text(f"❌ Invalid plan. Available: {', '.join(self.client_manager.plans.keys())}")
            return
        
        success = self.client_manager.upgrade_plan(client_id, new_plan)
        
        if success:
            plan_info = self.client_manager.plans[new_plan]
            await update.message.reply_text(f"✅ Client upgraded to {plan_info['name']}")
            logger.info(f"Admin {update.effective_user.id} upgraded client {client_id} to {new_plan}")
        else:
            await update.message.reply_text("❌ Failed to upgrade client.")
    
    async def cmd_add_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add group to client."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if len(context.args) != 3:
            await update.message.reply_text("Usage: /admin_add_group <client_id> <group_id> <group_name>")
            return
        
        client_id, group_id, group_name = context.args
        
        success = self.client_manager.add_group_to_client(client_id, group_id, group_name)
        
        if success:
            await update.message.reply_text(f"✅ Group '{group_name}' added to client.")
            logger.info(f"Admin {update.effective_user.id} added group {group_id} to client {client_id}")
        else:
            await update.message.reply_text("❌ Failed to add group. Check client exists and group limit.")
    
    async def cmd_system_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system statistics."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        try:
            clients = self.client_manager.list_clients()
            
            total_clients = len(clients)
            active_clients = len([c for c in clients if c['status'] == 'active'])
            total_groups = sum(c['groups_count'] for c in clients)
            total_transactions = sum(c['monthly_transactions'] for c in clients)
            
            plan_distribution = {}
            for client in clients:
                plan = client['plan']
                plan_distribution[plan] = plan_distribution.get(plan, 0) + 1
            
            response = f"""
📊 **System Statistics**

👥 **Clients:**
• Total: {total_clients}
• Active: {active_clients}
• Inactive: {total_clients - active_clients}

🏘️ **Groups:** {total_groups}
💰 **Transactions This Month:** {total_transactions}

📊 **Plan Distribution:**
            """
            
            for plan, count in plan_distribution.items():
                plan_name = self.client_manager.plans[plan]['name']
                response += f"• {plan_name}: {count}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting stats: {str(e)}")

# Admin command handlers for the main bot
admin_interface = AdminInterface()

# Export functions for main bot
cmd_admin_help = admin_interface.cmd_admin_help
cmd_create_client = admin_interface.cmd_create_client
cmd_list_clients = admin_interface.cmd_list_clients
cmd_client_info = admin_interface.cmd_client_info
cmd_upgrade_client = admin_interface.cmd_upgrade_client
cmd_add_group = admin_interface.cmd_add_group
cmd_system_stats = admin_interface.cmd_system_stats
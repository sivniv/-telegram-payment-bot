"""
Client Management System for Payment Bot SaaS
Copyright (c) 2025 Sochetra. All rights reserved.
"""

import json
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import secrets

class ClientManager:
    def __init__(self, clients_file: str = 'clients.json'):
        self.clients_file = clients_file
        self._ensure_file_exists()
        
        # Subscription plans
        self.plans = {
            'free': {
                'name': 'Free Plan',
                'price': 0,
                'monthly_transactions': 1000,
                'groups_limit': 1,
                'features': ['basic_payment_tracking', 'daily_reports']
            },
            'basic': {
                'name': 'Basic Plan',
                'price': 4.99,
                'monthly_transactions': 3000,
                'groups_limit': 1,
                'features': ['multi_payment_sources', 'daily_reports', 'weekly_reports', 'user_tracking']
            },
            'premium': {
                'name': 'Premium Plan',
                'price': 9.99,
                'monthly_transactions': 10000,
                'groups_limit': 3,
                'features': ['all_payment_sources', 'custom_patterns', 'analytics', 'priority_support', 'api_access']
            },
            'enterprise': {
                'name': 'Enterprise Plan',
                'price': 19.99,
                'monthly_transactions': 100000,
                'groups_limit': 10,
                'features': ['unlimited_everything', 'custom_integrations', 'dedicated_support', 'white_label']
            }
        }
    
    def _ensure_file_exists(self):
        """Create clients file if it doesn't exist."""
        if not os.path.exists(self.clients_file):
            with open(self.clients_file, 'w') as f:
                json.dump({}, f)
    
    def load_clients(self) -> Dict[str, Any]:
        """Load all clients from JSON file."""
        try:
            with open(self.clients_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_clients(self, clients: Dict[str, Any]) -> bool:
        """Save clients to JSON file."""
        try:
            with open(self.clients_file, 'w') as f:
                json.dump(clients, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving clients: {e}")
            return False
    
    def generate_api_key(self) -> str:
        """Generate a secure API key for client."""
        return f"pb_{secrets.token_urlsafe(32)}"
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def create_client(self, email: str, company_name: str, plan: str = 'free') -> Dict[str, Any]:
        """Create a new client account."""
        clients = self.load_clients()
        
        client_id = str(uuid.uuid4())
        api_key = self.generate_api_key()
        
        client_data = {
            'client_id': client_id,
            'email': email,
            'company_name': company_name,
            'plan': plan,
            'api_key_hash': self.hash_api_key(api_key),
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'groups': [],
            'monthly_usage': {
                'transactions': 0,
                'reset_date': (datetime.now() + timedelta(days=30)).isoformat()
            },
            'billing': {
                'next_billing_date': (datetime.now() + timedelta(days=30)).isoformat(),
                'payment_method': None,
                'invoices': []
            }
        }
        
        clients[client_id] = client_data
        self.save_clients(clients)
        
        return {
            'client_id': client_id,
            'api_key': api_key,  # Return plain key only once
            'plan': plan,
            'status': 'active'
        }
    
    def authenticate_client(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Authenticate client by API key."""
        clients = self.load_clients()
        api_key_hash = self.hash_api_key(api_key)
        
        for client_id, client_data in clients.items():
            if client_data.get('api_key_hash') == api_key_hash:
                if client_data.get('status') == 'active':
                    return client_data
        return None
    
    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client data by ID."""
        clients = self.load_clients()
        return clients.get(client_id)
    
    def update_client(self, client_id: str, updates: Dict[str, Any]) -> bool:
        """Update client data."""
        clients = self.load_clients()
        if client_id in clients:
            clients[client_id].update(updates)
            return self.save_clients(clients)
        return False
    
    def add_group_to_client(self, client_id: str, group_id: str, group_name: str) -> bool:
        """Add a Telegram group to client's account."""
        client = self.get_client(client_id)
        if not client:
            return False
        
        plan_limits = self.plans[client['plan']]
        current_groups = len(client.get('groups', []))
        
        # Check group limit
        if plan_limits['groups_limit'] != -1 and current_groups >= plan_limits['groups_limit']:
            return False
        
        group_data = {
            'group_id': group_id,
            'group_name': group_name,
            'added_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        if 'groups' not in client:
            client['groups'] = []
        
        client['groups'].append(group_data)
        return self.update_client(client_id, {'groups': client['groups']})
    
    def check_usage_limits(self, client_id: str) -> Dict[str, Any]:
        """Check if client is within usage limits."""
        client = self.get_client(client_id)
        if not client:
            return {'allowed': False, 'reason': 'Client not found'}
        
        plan_limits = self.plans[client['plan']]
        usage = client.get('monthly_usage', {})
        
        # Check transaction limit
        if plan_limits['monthly_transactions'] != -1:
            if usage.get('transactions', 0) >= plan_limits['monthly_transactions']:
                return {'allowed': False, 'reason': 'Monthly transaction limit exceeded'}
        
        # Check if usage period has reset
        reset_date = datetime.fromisoformat(usage.get('reset_date', datetime.now().isoformat()))
        if datetime.now() > reset_date:
            # Reset monthly usage
            new_usage = {
                'transactions': 0,
                'reset_date': (datetime.now() + timedelta(days=30)).isoformat()
            }
            self.update_client(client_id, {'monthly_usage': new_usage})
        
        return {'allowed': True, 'remaining': plan_limits['monthly_transactions'] - usage.get('transactions', 0)}
    
    def increment_usage(self, client_id: str, transactions: int = 1) -> bool:
        """Increment client's usage counters."""
        client = self.get_client(client_id)
        if not client:
            return False
        
        usage = client.get('monthly_usage', {'transactions': 0})
        usage['transactions'] += transactions
        
        return self.update_client(client_id, {'monthly_usage': usage})
    
    def upgrade_plan(self, client_id: str, new_plan: str) -> bool:
        """Upgrade client's subscription plan."""
        if new_plan not in self.plans:
            return False
        
        client = self.get_client(client_id)
        if not client:
            return False
        
        updates = {
            'plan': new_plan,
            'upgraded_at': datetime.now().isoformat()
        }
        
        return self.update_client(client_id, updates)
    
    def get_client_by_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Find client that owns a specific group."""
        clients = self.load_clients()
        
        for client_id, client_data in clients.items():
            for group in client_data.get('groups', []):
                if group['group_id'] == group_id:
                    return client_data
        return None
    
    def list_clients(self) -> List[Dict[str, Any]]:
        """List all clients with summary information."""
        clients = self.load_clients()
        summary = []
        
        for client_id, client_data in clients.items():
            summary.append({
                'client_id': client_id,
                'email': client_data.get('email'),
                'company_name': client_data.get('company_name'),
                'plan': client_data.get('plan'),
                'status': client_data.get('status'),
                'groups_count': len(client_data.get('groups', [])),
                'monthly_transactions': client_data.get('monthly_usage', {}).get('transactions', 0),
                'created_at': client_data.get('created_at')
            })
        
        return summary
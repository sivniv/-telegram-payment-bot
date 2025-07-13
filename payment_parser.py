"""
Payment Parser for Payment Bot SaaS
Copyright (c) 2025 Sochetra. All rights reserved.
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any
from group_settings import GroupSettingsManager

class PaymentParser:
    def __init__(self):
        self.settings_manager = GroupSettingsManager()
        
    def is_payment_message(self, message_text: str, group_id: str) -> bool:
        """Check if the message is a payment notification based on group configuration."""
        config = self.settings_manager.get_payment_config(group_id)
        identifier = config.get('identifier', 'kb_prasac_merchant_payment')
        return identifier in message_text
    
    def parse_payment(self, message_text: str, group_id: str) -> Optional[Dict[str, Any]]:
        """Parse payment notification and extract amount and payer name using group-specific patterns."""
        if not self.is_payment_message(message_text, group_id):
            return None
        
        config = self.settings_manager.get_payment_config(group_id)
        amount_pattern = config.get('amount_pattern')
        payer_pattern = config.get('payer_pattern')
        
        if not amount_pattern or not payer_pattern:
            return None
        
        # Extract amount
        amount_match = re.search(amount_pattern, message_text, re.IGNORECASE)
        if not amount_match:
            return None
        
        # Extract payer name
        payer_match = re.search(payer_pattern, message_text, re.IGNORECASE)
        if not payer_match:
            return None
        
        try:
            amount = float(amount_match.group(1))
            payer = payer_match.group(1).strip()
            
            now = datetime.now()
            source_name = config.get('name', 'Unknown Source')
            
            return {
                "date": now.strftime("%Y-%m-%d"),
                "timestamp": now.isoformat(),
                "amount": amount,
                "payer": payer,
                "type": "income",
                "source": source_name,
                "group_id": str(group_id)
            }
        except (ValueError, AttributeError):
            return None
    
    def test_patterns(self, message_text: str, amount_pattern: str, payer_pattern: str) -> Dict[str, Any]:
        """Test custom patterns against a message."""
        result = {
            'amount_match': None,
            'payer_match': None,
            'success': False
        }
        
        try:
            # Test amount pattern
            amount_match = re.search(amount_pattern, message_text, re.IGNORECASE)
            if amount_match:
                result['amount_match'] = amount_match.group(1)
            
            # Test payer pattern
            payer_match = re.search(payer_pattern, message_text, re.IGNORECASE)
            if payer_match:
                result['payer_match'] = payer_match.group(1).strip()
            
            result['success'] = bool(amount_match and payer_match)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
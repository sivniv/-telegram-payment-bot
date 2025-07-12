import re
from datetime import datetime
from typing import Optional, Dict, Any
from config import PAYMENT_SYSTEM_IDENTIFIER

class PaymentParser:
    def __init__(self):
        # RegEx patterns for parsing payment notifications
        self.amount_pattern = r'Received Payment Amount\s+([\d.]+)\s+USD'
        self.payer_pattern = r'- Paid by:\s+([^/]+)\s+/'
        
    def is_payment_message(self, message_text: str) -> bool:
        """Check if the message is a payment notification from kb_prasac_merchant_payment."""
        return PAYMENT_SYSTEM_IDENTIFIER in message_text
    
    def parse_payment(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Parse payment notification and extract amount and payer name."""
        if not self.is_payment_message(message_text):
            return None
        
        # Extract amount
        amount_match = re.search(self.amount_pattern, message_text)
        if not amount_match:
            return None
        
        # Extract payer name
        payer_match = re.search(self.payer_pattern, message_text)
        if not payer_match:
            return None
        
        try:
            amount = float(amount_match.group(1))
            payer = payer_match.group(1).strip()
            
            now = datetime.now()
            
            return {
                "date": now.strftime("%Y-%m-%d"),
                "timestamp": now.isoformat(),
                "amount": amount,
                "payer": payer,
                "type": "income"
            }
        except (ValueError, AttributeError):
            return None
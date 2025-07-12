#!/usr/bin/env python3
"""
Test script for payment parser functionality
"""

from payment_parser import PaymentParser
from transaction_storage import TransactionStorage

def test_payment_parsing():
    """Test payment message parsing."""
    parser = PaymentParser()
    
    # Sample payment message
    sample_message = """
kb_prasac_merchant_payment
Payment Notification
Received Payment Amount 4.50 USD
- Paid by: JOHN DOE / Bank Transfer
Transaction ID: 12345
    """
    
    print("Testing payment parser...")
    print(f"Sample message:\n{sample_message}")
    
    # Test if message is recognized as payment
    is_payment = parser.is_payment_message(sample_message)
    print(f"Is payment message: {is_payment}")
    
    # Test parsing
    transaction = parser.parse_payment(sample_message)
    print(f"Parsed transaction: {transaction}")
    
    if transaction:
        # Test storage
        storage = TransactionStorage()
        success = storage.save_transaction(transaction)
        print(f"Transaction saved: {success}")
        
        # Test daily summary
        summary = storage.get_daily_summary(transaction['date'])
        print(f"Daily summary: {summary}")

if __name__ == "__main__":
    test_payment_parsing()
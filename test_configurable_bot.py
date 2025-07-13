#!/usr/bin/env python3
"""
Test script for the configurable payment bot
"""

from payment_parser import PaymentParser
from group_settings import GroupSettingsManager
from transaction_storage import TransactionStorage

def test_configurable_parser():
    """Test the configurable payment parser with different sources."""
    parser = PaymentParser()
    settings_manager = GroupSettingsManager()
    storage = TransactionStorage()
    
    # Test group IDs
    group1 = "test_group_1"
    group2 = "test_group_2"
    
    print("🧪 Testing Configurable Payment Bot\n")
    
    # Test 1: Default KB Prasac configuration
    print("1️⃣ Testing KB Prasac (default)")
    kb_message = """
kb_prasac_merchant_payment
Payment Notification
Received Payment Amount 15.50 USD
- Paid by: JOHN DOE / Bank Transfer
Transaction ID: 12345
    """
    
    transaction = parser.parse_payment(kb_message, group1)
    print(f"   Result: {transaction}")
    print(f"   Success: {'✅' if transaction else '❌'}\n")
    
    # Test 2: Configure group2 for ABA Bank
    print("2️⃣ Testing ABA Bank configuration")
    settings_manager.set_payment_source(group2, 'aba_bank')
    
    aba_message = """
ABA Bank Transfer Notification
Amount: USD 25.75
From: Jane Smith
Reference: TXN789456
    """
    
    transaction = parser.parse_payment(aba_message, group2)
    print(f"   Result: {transaction}")
    print(f"   Success: {'✅' if transaction else '❌'}\n")
    
    # Test 3: Test Wing Money
    print("3️⃣ Testing Wing Money configuration")
    settings_manager.set_payment_source(group1, 'wing_money')
    
    wing_message = """
Wing Money Transfer
Received 30.00 USD
From: Bob Wilson
Transaction completed successfully
    """
    
    transaction = parser.parse_payment(wing_message, group1)
    print(f"   Result: {transaction}")
    print(f"   Success: {'✅' if transaction else '❌'}\n")
    
    # Test 4: Check settings
    print("4️⃣ Testing settings retrieval")
    config1 = settings_manager.get_payment_config(group1)
    config2 = settings_manager.get_payment_config(group2)
    
    print(f"   Group1 config: {config1['name']}")
    print(f"   Group2 config: {config2['name']}")
    
    # Test 5: List all available sources
    print("\n5️⃣ Available payment sources:")
    sources = settings_manager.get_available_sources()
    for key, source in sources.items():
        print(f"   🔹 {key}: {source['name']}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_configurable_parser()
import json
import os
from typing import List, Dict, Any
from datetime import datetime
from config import TRANSACTIONS_FILE

class TransactionStorage:
    def __init__(self):
        self.file_path = TRANSACTIONS_FILE
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create transactions file if it doesn't exist."""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)
    
    def load_transactions(self) -> List[Dict[str, Any]]:
        """Load all transactions from JSON file."""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Save a new transaction to the JSON file."""
        try:
            transactions = self.load_transactions()
            transactions.append(transaction)
            
            with open(self.file_path, 'w') as f:
                json.dump(transactions, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving transaction: {e}")
            return False
    
    def get_transactions_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Get all transactions for a specific date (YYYY-MM-DD)."""
        transactions = self.load_transactions()
        return [t for t in transactions if t.get('date') == date]
    
    def get_daily_summary(self, date: str) -> Dict[str, Any]:
        """Get daily summary for a specific date."""
        daily_transactions = self.get_transactions_by_date(date)
        
        total_amount = sum(t.get('amount', 0) for t in daily_transactions)
        transaction_count = len(daily_transactions)
        
        return {
            'date': date,
            'total_amount': total_amount,
            'transaction_count': transaction_count,
            'transactions': daily_transactions
        }
    
    def get_all_time_summary(self) -> Dict[str, Any]:
        """Get summary of all transactions."""
        transactions = self.load_transactions()
        
        total_amount = sum(t.get('amount', 0) for t in transactions)
        transaction_count = len(transactions)
        
        # Group by date for daily breakdown
        daily_totals = {}
        for transaction in transactions:
            date = transaction.get('date')
            if date:
                if date not in daily_totals:
                    daily_totals[date] = 0
                daily_totals[date] += transaction.get('amount', 0)
        
        return {
            'total_amount': total_amount,
            'transaction_count': transaction_count,
            'daily_totals': daily_totals,
            'transactions': transactions
        }
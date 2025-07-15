import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from config import TRANSACTIONS_FILE
from encryption_manager import EncryptionManager

logger = logging.getLogger(__name__)


class TransactionStorage:
    def __init__(self, use_encryption: bool = True):
        self.file_path = TRANSACTIONS_FILE
        self.use_encryption = use_encryption
        self.encryption_manager = EncryptionManager() if use_encryption else None

        # Fields to encrypt for privacy
        self.sensitive_fields = ["payer", "group_id"]

        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create transactions file if it doesn't exist."""
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def load_transactions(self) -> List[Dict[str, Any]]:
        """Load all transactions from JSON file."""
        try:
            with open(self.file_path, "r") as f:
                transactions = json.load(f)

            # Decrypt sensitive fields if encryption is enabled
            if self.use_encryption and self.encryption_manager:
                decrypted_transactions = []
                for transaction in transactions:
                    try:
                        decrypted_transaction = self.encryption_manager.decrypt_sensitive_fields(
                            transaction, self.sensitive_fields
                        )
                        decrypted_transactions.append(decrypted_transaction)
                    except Exception as e:
                        logger.warning(f"Could not decrypt transaction: {e}")
                        # Keep original transaction if decryption fails
                        decrypted_transactions.append(transaction)

                return decrypted_transactions

            return transactions

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load transactions: {e}")
            return []

    def save_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Save a new transaction to the JSON file."""
        try:
            # Load existing transactions (will be decrypted automatically)
            transactions = self.load_transactions()

            # Prepare transaction for storage
            transaction_to_save = transaction.copy()

            # Encrypt sensitive fields if encryption is enabled
            if self.use_encryption and self.encryption_manager:
                transaction_to_save = self.encryption_manager.encrypt_sensitive_fields(
                    transaction_to_save, self.sensitive_fields
                )

            transactions.append(transaction_to_save)

            # Save to file
            with open(self.file_path, "w") as f:
                json.dump(transactions, f, indent=2)

            logger.info(f"Transaction saved successfully (encrypted: {self.use_encryption})")
            return True

        except Exception as e:
            logger.error(f"Error saving transaction: {e}")
            return False

    def get_transactions_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Get all transactions for a specific date (YYYY-MM-DD)."""
        transactions = self.load_transactions()
        return [t for t in transactions if t.get("date") == date]

    def get_daily_summary(self, date: str) -> Dict[str, Any]:
        """Get daily summary for a specific date."""
        daily_transactions = self.get_transactions_by_date(date)

        total_amount = sum(t.get("amount", 0) for t in daily_transactions)
        transaction_count = len(daily_transactions)

        return {
            "date": date,
            "total_amount": total_amount,
            "transaction_count": transaction_count,
            "transactions": daily_transactions,
        }

    def get_all_time_summary(self) -> Dict[str, Any]:
        """Get summary of all transactions."""
        transactions = self.load_transactions()

        total_amount = sum(t.get("amount", 0) for t in transactions)
        transaction_count = len(transactions)

        # Group by date for daily breakdown
        daily_totals = {}
        for transaction in transactions:
            date = transaction.get("date")
            if date:
                if date not in daily_totals:
                    daily_totals[date] = 0
                daily_totals[date] += transaction.get("amount", 0)

        return {
            "total_amount": total_amount,
            "transaction_count": transaction_count,
            "daily_totals": daily_totals,
            "transactions": transactions,
        }

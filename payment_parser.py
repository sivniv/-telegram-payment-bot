"""
Payment Parser for Payment Bot SaaS
Copyright (c) 2025 Sochetra. All rights reserved.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

from group_settings import GroupSettingsManager
from security_validator import SecurityValidator

logger = logging.getLogger(__name__)


class PaymentParser:
    def __init__(self):
        self.settings_manager = GroupSettingsManager()

    def is_payment_message(self, message_text: str, group_id: str) -> bool:
        """Check if the message is a payment notification based on group configuration."""
        # Security validation first
        validation = SecurityValidator.validate_message_input(message_text, group_id)
        if not validation["valid"]:
            logger.warning(f"Invalid message input: {validation['errors']}")
            return False

        config = self.settings_manager.get_payment_config(group_id)
        identifier = config.get("identifier", "kb_prasac_merchant_payment")

        # Use sanitized message for checking
        sanitized_message = validation["sanitized_message"]
        return identifier in sanitized_message

    def parse_payment(self, message_text: str, group_id: str) -> Optional[Dict[str, Any]]:
        """Parse payment notification and extract amount and payer name using group-specific patterns."""
        # Rate limiting check
        rate_check = SecurityValidator.check_rate_limit(group_id, "parse_payment")
        if not rate_check["allowed"]:
            logger.warning(f"Rate limit exceeded for group {group_id}: {rate_check}")
            SecurityValidator.log_security_event(
                "rate_limit_exceeded", {"group_id": group_id, "action": "parse_payment"}, "WARNING"
            )
            return None

        # Validate input first
        validation = SecurityValidator.validate_message_input(message_text, group_id)
        if not validation["valid"]:
            logger.error(f"Security validation failed: {validation['errors']}")
            return None

        # Use sanitized inputs
        sanitized_message = validation["sanitized_message"]
        sanitized_group_id = validation["sanitized_group_id"]

        if not self.is_payment_message(message_text, group_id):
            return None

        config = self.settings_manager.get_payment_config(sanitized_group_id)
        amount_pattern = config.get("amount_pattern")
        payer_pattern = config.get("payer_pattern")

        if not amount_pattern or not payer_pattern:
            return None

        # Validate patterns before use
        amount_pattern_validation = SecurityValidator.validate_regex_pattern(
            amount_pattern, "amount"
        )
        payer_pattern_validation = SecurityValidator.validate_regex_pattern(payer_pattern, "payer")

        if not amount_pattern_validation["valid"] or not payer_pattern_validation["valid"]:
            logger.error(f"Invalid regex patterns detected for group {sanitized_group_id}")
            SecurityValidator.log_security_event(
                "invalid_regex_pattern",
                {
                    "group_id": sanitized_group_id,
                    "amount_errors": amount_pattern_validation.get("errors", []),
                    "payer_errors": payer_pattern_validation.get("errors", []),
                },
                "ERROR",
            )
            return None

        try:
            # Extract amount using validated pattern
            amount_match = re.search(amount_pattern, sanitized_message, re.IGNORECASE)
            if not amount_match:
                return None

            # Validate extracted amount
            amount_validation = SecurityValidator.validate_amount(amount_match.group(1))
            if not amount_validation["valid"]:
                logger.warning(f"Invalid amount extracted: {amount_validation['errors']}")
                return None

            # Extract payer name using validated pattern
            payer_match = re.search(payer_pattern, sanitized_message, re.IGNORECASE)
            if not payer_match:
                return None

            # Validate extracted payer name
            payer_validation = SecurityValidator.validate_payer_name(payer_match.group(1))
            if not payer_validation["valid"]:
                logger.warning(f"Invalid payer name extracted: {payer_validation['errors']}")
                return None

            # Use validated and sanitized data
            amount = amount_validation["sanitized_amount"]
            payer = payer_validation["sanitized_name"]

            now = datetime.now()
            source_name = config.get("name", "Unknown Source")

            transaction = {
                "date": now.strftime("%Y-%m-%d"),
                "timestamp": now.isoformat(),
                "amount": amount,
                "payer": payer,
                "type": "income",
                "source": source_name,
                "group_id": sanitized_group_id,
            }

            # Log successful parsing (with hashed sensitive data)
            SecurityValidator.log_security_event(
                "payment_parsed",
                {
                    "group_id": sanitized_group_id,
                    "amount": amount,
                    "payer_hash": SecurityValidator.hash_sensitive_data(payer),
                    "source": source_name,
                },
                "INFO",
            )

            return transaction

        except (ValueError, AttributeError, re.error) as e:
            logger.error(f"Error parsing payment: {str(e)}")
            SecurityValidator.log_security_event(
                "parsing_error", {"group_id": sanitized_group_id, "error": str(e)}, "ERROR"
            )
            return None

    def test_patterns(
        self, message_text: str, amount_pattern: str, payer_pattern: str
    ) -> Dict[str, Any]:
        """Test custom patterns against a message with security validation."""
        result = {
            "amount_match": None,
            "payer_match": None,
            "success": False,
            "errors": [],
            "warnings": [],
        }

        # Rate limiting for pattern testing
        rate_check = SecurityValidator.check_rate_limit("test_patterns", "pattern_test")
        if not rate_check["allowed"]:
            result["errors"].append("Rate limit exceeded for pattern testing")
            return result

        # Validate input message
        message_validation = SecurityValidator.validate_message_input(message_text, "test")
        if not message_validation["valid"]:
            result["errors"].extend(message_validation["errors"])
            return result

        # Validate patterns
        amount_validation = SecurityValidator.validate_regex_pattern(amount_pattern, "amount")
        payer_validation = SecurityValidator.validate_regex_pattern(payer_pattern, "payer")

        if not amount_validation["valid"]:
            result["errors"].extend(
                [f"Amount pattern: {err}" for err in amount_validation["errors"]]
            )

        if not payer_validation["valid"]:
            result["errors"].extend([f"Payer pattern: {err}" for err in payer_validation["errors"]])

        # Collect warnings
        result["warnings"].extend(message_validation.get("warnings", []))
        result["warnings"].extend(
            [f"Amount pattern: {warn}" for warn in amount_validation.get("warnings", [])]
        )
        result["warnings"].extend(
            [f"Payer pattern: {warn}" for warn in payer_validation.get("warnings", [])]
        )

        if result["errors"]:
            return result

        try:
            sanitized_message = message_validation["sanitized_message"]

            # Test amount pattern
            amount_match = re.search(amount_pattern, sanitized_message, re.IGNORECASE)
            if amount_match:
                amount_str = amount_match.group(1)
                amount_check = SecurityValidator.validate_amount(amount_str)
                if amount_check["valid"]:
                    result["amount_match"] = amount_check["sanitized_amount"]
                else:
                    result["warnings"].extend(
                        [f"Amount value: {err}" for err in amount_check["errors"]]
                    )

            # Test payer pattern
            payer_match = re.search(payer_pattern, sanitized_message, re.IGNORECASE)
            if payer_match:
                payer_str = payer_match.group(1).strip()
                payer_check = SecurityValidator.validate_payer_name(payer_str)
                if payer_check["valid"]:
                    result["payer_match"] = payer_check["sanitized_name"]
                else:
                    result["warnings"].extend(
                        [f"Payer name: {err}" for err in payer_check["errors"]]
                    )

            result["success"] = bool(
                amount_match and payer_match and result["amount_match"] and result["payer_match"]
            )

            # Log pattern testing
            SecurityValidator.log_security_event(
                "pattern_test",
                {
                    "success": result["success"],
                    "warnings_count": len(result["warnings"]),
                    "amount_pattern_hash": SecurityValidator.hash_sensitive_data(amount_pattern),
                    "payer_pattern_hash": SecurityValidator.hash_sensitive_data(payer_pattern),
                },
                "INFO",
            )

        except Exception as e:
            result["errors"].append(f"Pattern testing error: {str(e)}")
            SecurityValidator.log_security_event("pattern_test_error", {"error": str(e)}, "ERROR")

        return result

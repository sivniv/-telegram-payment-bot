"""
Security Validator for Payment Bot SaaS
Copyright (c) 2025 Sochetra. All rights reserved.

This module provides input validation and sanitization to prevent:
- RegEx injection attacks
- Code injection
- Data corruption
- Malicious pattern execution
"""

import hashlib
import html
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Comprehensive security validation for payment bot."""

    # Rate limiting storage
    _rate_limits = defaultdict(list)

    # Allowed RegEx metacharacters for payment patterns
    SAFE_REGEX_CHARS = set(r"[](){}*+?|^$.\d\w\s-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:/_\\ ")

    # Maximum limits
    MAX_MESSAGE_LENGTH = 5000
    MAX_PATTERN_LENGTH = 500
    MAX_GROUP_ID_LENGTH = 50
    MAX_PAYER_NAME_LENGTH = 100
    MAX_AMOUNT = 999999.99
    MIN_AMOUNT = 0.01

    # Rate limits (requests per minute)
    RATE_LIMITS = {"parse_payment": 100, "admin_command": 20, "pattern_test": 10}

    @classmethod
    def validate_message_input(cls, message_text: str, group_id: str) -> Dict[str, Any]:
        """Validate and sanitize message input."""
        errors = []
        warnings = []

        # Basic input validation
        if not isinstance(message_text, str):
            errors.append("Message must be a string")
            return {"valid": False, "errors": errors}

        if not isinstance(group_id, str):
            errors.append("Group ID must be a string")
            return {"valid": False, "errors": errors}

        # Length validation
        if len(message_text) > cls.MAX_MESSAGE_LENGTH:
            errors.append(f"Message too long (max {cls.MAX_MESSAGE_LENGTH} chars)")

        if len(group_id) > cls.MAX_GROUP_ID_LENGTH:
            errors.append(f"Group ID too long (max {cls.MAX_GROUP_ID_LENGTH} chars)")

        # Sanitize inputs
        sanitized_message = cls._sanitize_message(message_text)
        sanitized_group_id = cls._sanitize_group_id(group_id)

        # Check for suspicious content
        if cls._contains_suspicious_content(message_text):
            warnings.append("Message contains potentially suspicious content")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized_message": sanitized_message,
            "sanitized_group_id": sanitized_group_id,
        }

    @classmethod
    def validate_regex_pattern(cls, pattern: str, pattern_type: str = "generic") -> Dict[str, Any]:
        """Validate RegEx pattern for security and correctness."""
        errors = []
        warnings = []

        if not isinstance(pattern, str):
            errors.append("Pattern must be a string")
            return {"valid": False, "errors": errors}

        # Length check
        if len(pattern) > cls.MAX_PATTERN_LENGTH:
            errors.append(f"Pattern too long (max {cls.MAX_PATTERN_LENGTH} chars)")

        # Character whitelist validation
        pattern_chars = set(pattern)
        unsafe_chars = pattern_chars - cls.SAFE_REGEX_CHARS
        if unsafe_chars:
            errors.append(f"Unsafe characters in pattern: {sorted(unsafe_chars)}")

        # Test pattern compilation
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)

            # Check for catastrophic backtracking (basic detection)
            if cls._has_potential_backtracking(pattern):
                warnings.append("Pattern may cause performance issues")

        except re.error as e:
            errors.append(f"Invalid RegEx pattern: {str(e)}")
            return {"valid": False, "errors": errors}

        # Pattern-specific validation
        if pattern_type == "amount":
            if not cls._validate_amount_pattern(pattern):
                warnings.append("Amount pattern may not capture decimal numbers correctly")

        elif pattern_type == "payer":
            if not cls._validate_payer_pattern(pattern):
                warnings.append("Payer pattern may be too permissive")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "compiled_pattern": compiled_pattern if len(errors) == 0 else None,
        }

    @classmethod
    def validate_amount(cls, amount_str: str) -> Dict[str, Any]:
        """Validate extracted amount value."""
        errors = []

        try:
            amount = float(amount_str)

            if amount < cls.MIN_AMOUNT:
                errors.append(f"Amount too small (min ${cls.MIN_AMOUNT})")

            if amount > cls.MAX_AMOUNT:
                errors.append(f"Amount too large (max ${cls.MAX_AMOUNT})")

            # Check for reasonable decimal places (max 2 for currency)
            if len(amount_str.split(".")[-1]) > 2 if "." in amount_str else False:
                errors.append("Too many decimal places for currency")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "sanitized_amount": round(amount, 2),
            }

        except (ValueError, TypeError):
            return {"valid": False, "errors": ["Invalid amount format"], "sanitized_amount": None}

    @classmethod
    def validate_payer_name(cls, payer_name: str) -> Dict[str, Any]:
        """Validate and sanitize payer name."""
        errors = []
        warnings = []

        if not isinstance(payer_name, str):
            errors.append("Payer name must be a string")
            return {"valid": False, "errors": errors}

        # Length validation
        if len(payer_name) > cls.MAX_PAYER_NAME_LENGTH:
            errors.append(f"Payer name too long (max {cls.MAX_PAYER_NAME_LENGTH} chars)")

        # Sanitize
        sanitized_name = cls._sanitize_payer_name(payer_name)

        # Check for suspicious patterns
        if cls._contains_suspicious_content(payer_name):
            warnings.append("Payer name contains suspicious content")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized_name": sanitized_name,
        }

    @classmethod
    def check_rate_limit(cls, identifier: str, action: str) -> Dict[str, Any]:
        """Check if request is within rate limits."""
        now = datetime.now()
        key = f"{identifier}:{action}"

        # Clean old entries (older than 1 minute)
        cls._rate_limits[key] = [
            timestamp
            for timestamp in cls._rate_limits[key]
            if now - timestamp < timedelta(minutes=1)
        ]

        # Check current count
        current_count = len(cls._rate_limits[key])
        limit = cls.RATE_LIMITS.get(action, 50)  # Default limit

        if current_count >= limit:
            return {
                "allowed": False,
                "current_count": current_count,
                "limit": limit,
                "reset_time": 60 - (now - min(cls._rate_limits[key])).seconds,
            }

        # Add current request
        cls._rate_limits[key].append(now)

        return {
            "allowed": True,
            "current_count": current_count + 1,
            "limit": limit,
            "remaining": limit - current_count - 1,
        }

    @classmethod
    def _sanitize_message(cls, message: str) -> str:
        """Sanitize message content."""
        # HTML escape
        sanitized = html.escape(message)

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Normalize whitespace
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        return sanitized

    @classmethod
    def _sanitize_group_id(cls, group_id: str) -> str:
        """Sanitize group ID."""
        # Remove non-alphanumeric characters except hyphens and underscores
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", str(group_id))
        return sanitized

    @classmethod
    def _sanitize_payer_name(cls, name: str) -> str:
        """Sanitize payer name."""
        # HTML escape
        sanitized = html.escape(name)

        # Remove control characters
        sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", sanitized)

        # Normalize whitespace
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        # Remove leading/trailing special characters
        sanitized = re.sub(r"^[^\w]+|[^\w]+$", "", sanitized)

        return sanitized

    @classmethod
    def _contains_suspicious_content(cls, text: str) -> bool:
        """Check for suspicious content patterns."""
        suspicious_patterns = [
            r"<script",  # Script tags
            r"javascript:",  # JavaScript protocols
            r"eval\(",  # Eval functions
            r"exec\(",  # Exec functions
            r"import\s+os",  # OS imports
            r"import\s+subprocess",  # Subprocess imports
            r"__import__",  # Dynamic imports
            r"\$\{.*\}",  # Template injection
            r"#{.*}",  # Template injection
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    @classmethod
    def _has_potential_backtracking(cls, pattern: str) -> bool:
        """Basic check for catastrophic backtracking patterns."""
        # Look for nested quantifiers and alternations
        dangerous_patterns = [
            r"\*.*\*",  # Nested *
            r"\+.*\+",  # Nested +
            r"\*.*\+",  # * followed by +
            r"\+.*\*",  # + followed by *
            r"\(.*\|.*\)\*",  # Alternation with *
            r"\(.*\|.*\)\+",  # Alternation with +
        ]

        for dangerous in dangerous_patterns:
            if re.search(dangerous, pattern):
                return True

        return False

    @classmethod
    def _validate_amount_pattern(cls, pattern: str) -> bool:
        """Validate that amount pattern can capture decimal numbers."""
        # Should contain digit capture group and optional decimal
        has_digits = r"\d" in pattern or r"[\d" in pattern
        has_capture = "(" in pattern and ")" in pattern
        return has_digits and has_capture

    @classmethod
    def _validate_payer_pattern(cls, pattern: str) -> bool:
        """Validate that payer pattern is not too permissive."""
        # Should not match everything
        overly_permissive = [
            r".*",
            r".+",
            r"[\s\S]*",
            r"[\s\S]+",
        ]

        return pattern not in overly_permissive

    @classmethod
    def hash_sensitive_data(cls, data: str, salt: str = "") -> str:
        """Hash sensitive data for logging/storage."""
        hasher = hashlib.sha256()
        hasher.update((data + salt).encode("utf-8"))
        return hasher.hexdigest()

    @classmethod
    def log_security_event(cls, event_type: str, details: Dict[str, Any], severity: str = "INFO"):
        """Log security-related events."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "details": details,
        }

        if severity == "ERROR":
            logger.error(f"Security Event: {log_entry}")
        elif severity == "WARNING":
            logger.warning(f"Security Event: {log_entry}")
        else:
            logger.info(f"Security Event: {log_entry}")

    @classmethod
    def validate_input(cls, input_data: str, field_name: str) -> Dict[str, Any]:
        """Validate general input data."""
        errors = []
        warnings = []
        
        if not isinstance(input_data, str):
            errors.append(f"{field_name} must be a string")
            return {"valid": False, "errors": errors}
        
        # Basic length validation
        if len(input_data) > cls.MAX_MESSAGE_LENGTH:
            errors.append(f"{field_name} too long (max {cls.MAX_MESSAGE_LENGTH} chars)")
        
        # Sanitize the input
        sanitized = html.escape(input_data)
        
        # Check for suspicious content
        if cls._contains_suspicious_content(input_data):
            warnings.append(f"{field_name} contains potentially suspicious content")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized": sanitized
        }

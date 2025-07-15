import json
import os
from typing import Any, Dict, Optional


class GroupSettingsManager:
    def __init__(self, settings_file: str = "group_settings.json"):
        self.settings_file = settings_file
        self._ensure_file_exists()

        # Default payment source configurations
        self.default_sources = {
            "kb_prasac_merchant_payment": {
                "identifier": "Received Payment Amount",
                "name": "KB Prasac Merchant Payment",
                "amount_pattern": r"Received Payment Amount\s+([\d.]+)\s+USD",
                "payer_pattern": r"- Paid by:\s+([^/]+)\s+/",
                "description": "KB Prasac merchant payment notifications",
            },
            "aba_bank": {
                "identifier": "ABA",
                "name": "ABA Bank Transfer",
                "amount_pattern": r"Amount:\s*USD\s*([\d.]+)",
                "payer_pattern": r"From:\s*([^,\n]+)",
                "description": "ABA Bank transfer notifications",
            },
            "wing_money": {
                "identifier": "Wing",
                "name": "Wing Money Transfer",
                "amount_pattern": r"Received\s+([\d.]+)\s+USD",
                "payer_pattern": r"From:\s*([^,\n]+)",
                "description": "Wing Money transfer notifications",
            },
            "acleda_bank": {
                "identifier": "ACLEDA",
                "name": "ACLEDA Bank",
                "amount_pattern": r"Amount:\s*([\d.]+)\s*USD",
                "payer_pattern": r"Sender:\s*([^,\n]+)",
                "description": "ACLEDA Bank payment notifications",
            },
        }

    def _ensure_file_exists(self):
        """Create settings file if it doesn't exist."""
        if not os.path.exists(self.settings_file):
            with open(self.settings_file, "w") as f:
                json.dump({}, f)

    def load_settings(self) -> Dict[str, Any]:
        """Load all group settings from JSON file."""
        try:
            with open(self.settings_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save group settings to JSON file."""
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get_group_settings(self, group_id: str) -> Dict[str, Any]:
        """Get settings for a specific group."""
        all_settings = self.load_settings()
        return all_settings.get(str(group_id), self._get_default_group_settings())

    def _get_default_group_settings(self) -> Dict[str, Any]:
        """Get default settings for a new group."""
        return {
            "payment_source": "kb_prasac_merchant_payment",
            "custom_patterns": None,
            "enabled": True,
            "admin_only_config": True,
        }

    def update_group_settings(self, group_id: str, new_settings: Dict[str, Any]) -> bool:
        """Update settings for a specific group."""
        all_settings = self.load_settings()
        group_id_str = str(group_id)

        if group_id_str not in all_settings:
            all_settings[group_id_str] = self._get_default_group_settings()

        all_settings[group_id_str].update(new_settings)
        return self.save_settings(all_settings)

    def set_payment_source(self, group_id: str, source_key: str) -> bool:
        """Set the payment source for a group."""
        if source_key not in self.default_sources:
            return False

        return self.update_group_settings(group_id, {"payment_source": source_key})

    def set_custom_patterns(
        self, group_id: str, amount_pattern: str, payer_pattern: str, identifier: str
    ) -> bool:
        """Set custom patterns for a group."""
        custom_patterns = {
            "identifier": identifier,
            "amount_pattern": amount_pattern,
            "payer_pattern": payer_pattern,
            "name": "Custom Pattern",
            "description": "User-defined custom pattern",
        }

        return self.update_group_settings(
            group_id, {"payment_source": "custom", "custom_patterns": custom_patterns}
        )

    def get_payment_config(self, group_id: str) -> Dict[str, Any]:
        """Get the current payment configuration for a group."""
        settings = self.get_group_settings(group_id)
        source_key = settings.get("payment_source", "kb_prasac_merchant_payment")

        if source_key == "custom" and settings.get("custom_patterns"):
            return settings["custom_patterns"]

        return self.default_sources.get(
            source_key, self.default_sources["kb_prasac_merchant_payment"]
        )

    def get_available_sources(self) -> Dict[str, Dict[str, Any]]:
        """Get all available payment sources."""
        return self.default_sources

    def is_admin_only_config(self, group_id: str) -> bool:
        """Check if configuration is restricted to admins."""
        settings = self.get_group_settings(group_id)
        return settings.get("admin_only_config", True)

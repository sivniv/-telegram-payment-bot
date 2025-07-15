"""
Encryption Manager for Payment Bot SaaS
Copyright (c) 2025 Sochetra. All rights reserved.

This module provides AES encryption for sensitive data storage.
"""

import base64
import hashlib
import json
import logging
import os
from typing import Any, Dict, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manages encryption/decryption for sensitive data storage."""

    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize encryption manager with key."""
        self.encryption_key = encryption_key or self._get_or_create_key()
        self.fernet = self._create_fernet()

    def _get_or_create_key(self) -> str:
        """Get existing encryption key or create a new one."""
        key_file = ".encryption_key"

        # Try to load existing key
        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning(f"Could not read encryption key: {e}")

        # Generate new key
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()

        try:
            with open(key_file, "w") as f:
                f.write(key)

            # Set restrictive permissions (owner read-only)
            os.chmod(key_file, 0o600)
            logger.info("Generated new encryption key")

        except Exception as e:
            logger.error(f"Could not save encryption key: {e}")
            # Use in-memory key if file save fails

        return key

    def _create_fernet(self) -> Fernet:
        """Create Fernet cipher from the encryption key."""
        try:
            # Derive key using PBKDF2
            salt = b"payment_bot_salt_2025"  # Fixed salt for consistency
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )

            key_bytes = self.encryption_key.encode()
            derived_key = base64.urlsafe_b64encode(kdf.derive(key_bytes))

            return Fernet(derived_key)

        except Exception as e:
            logger.error(f"Failed to create encryption cipher: {e}")
            raise

    def encrypt_data(self, data: Union[str, Dict, Any]) -> str:
        """Encrypt data and return base64 encoded string."""
        try:
            # Convert to JSON string if not already a string
            if not isinstance(data, str):
                data_str = json.dumps(data, ensure_ascii=False)
            else:
                data_str = data

            # Encrypt the data
            encrypted_bytes = self.fernet.encrypt(data_str.encode("utf-8"))

            # Return base64 encoded string
            return base64.urlsafe_b64encode(encrypted_bytes).decode("ascii")

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt_data(self, encrypted_data: str, return_json: bool = False) -> Union[str, Dict, Any]:
        """Decrypt base64 encoded encrypted data."""
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode("ascii"))

            # Decrypt the data
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            decrypted_str = decrypted_bytes.decode("utf-8")

            # Return as JSON object if requested
            if return_json:
                return json.loads(decrypted_str)

            return decrypted_str

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> bool:
        """Encrypt a file and save to output path."""
        try:
            # Read the file
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            # Encrypt the content
            encrypted_content = self.encrypt_data(file_content)

            # Determine output path
            if output_path is None:
                output_path = f"{file_path}.encrypted"

            # Write encrypted file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(encrypted_content)

            logger.info(f"File encrypted: {file_path} -> {output_path}")
            return True

        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            return False

    def decrypt_file(self, encrypted_file_path: str, output_path: Optional[str] = None) -> bool:
        """Decrypt a file and save to output path."""
        try:
            # Read the encrypted file
            with open(encrypted_file_path, "r", encoding="utf-8") as f:
                encrypted_content = f.read()

            # Decrypt the content
            decrypted_content = self.decrypt_data(encrypted_content)

            # Determine output path
            if output_path is None:
                if encrypted_file_path.endswith(".encrypted"):
                    output_path = encrypted_file_path[:-10]  # Remove .encrypted
                else:
                    output_path = f"{encrypted_file_path}.decrypted"

            # Write decrypted file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(decrypted_content)

            logger.info(f"File decrypted: {encrypted_file_path} -> {output_path}")
            return True

        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            return False

    def encrypt_sensitive_fields(
        self, data: Dict[str, Any], sensitive_fields: list
    ) -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary."""
        encrypted_data = data.copy()

        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field] is not None:
                try:
                    encrypted_data[field] = self.encrypt_data(str(encrypted_data[field]))
                    # Mark field as encrypted
                    encrypted_data[f"{field}_encrypted"] = True
                except Exception as e:
                    logger.error(f"Failed to encrypt field {field}: {e}")

        return encrypted_data

    def decrypt_sensitive_fields(
        self, data: Dict[str, Any], sensitive_fields: list
    ) -> Dict[str, Any]:
        """Decrypt specific fields in a dictionary."""
        decrypted_data = data.copy()

        for field in sensitive_fields:
            if f"{field}_encrypted" in decrypted_data and decrypted_data.get(f"{field}_encrypted"):
                try:
                    if field in decrypted_data:
                        decrypted_data[field] = self.decrypt_data(decrypted_data[field])
                        # Remove encryption marker
                        del decrypted_data[f"{field}_encrypted"]
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field}: {e}")

        return decrypted_data

    def hash_data(self, data: str, salt: Optional[str] = None) -> str:
        """Create a hash of sensitive data for indexing/comparison."""
        if salt is None:
            salt = "payment_bot_hash_salt_2025"

        hasher = hashlib.sha256()
        hasher.update((data + salt).encode("utf-8"))
        return hasher.hexdigest()

    def secure_compare(self, value1: str, value2_hash: str, salt: Optional[str] = None) -> bool:
        """Securely compare a value with its hash."""
        value1_hash = self.hash_data(value1, salt)
        return value1_hash == value2_hash

    @staticmethod
    def generate_random_key() -> str:
        """Generate a new random encryption key."""
        return base64.urlsafe_b64encode(os.urandom(32)).decode()

    def rotate_key(self, new_key: Optional[str] = None) -> str:
        """Rotate the encryption key."""
        old_fernet = self.fernet

        # Generate new key if not provided
        if new_key is None:
            new_key = self.generate_random_key()

        # Create new Fernet with new key
        old_encryption_key = self.encryption_key
        self.encryption_key = new_key
        self.fernet = self._create_fernet()

        logger.info("Encryption key rotated")

        return old_encryption_key  # Return old key for data migration

    def migrate_encrypted_data(self, old_encrypted_data: str, old_key: str) -> str:
        """Migrate data from old encryption key to current key."""
        try:
            # Create temporary Fernet with old key
            old_encryption_key = self.encryption_key
            self.encryption_key = old_key
            old_fernet = self._create_fernet()

            # Decrypt with old key
            decrypted_data = self.decrypt_data(old_encrypted_data)

            # Restore current key
            self.encryption_key = old_encryption_key
            self.fernet = self._create_fernet()

            # Encrypt with new key
            return self.encrypt_data(decrypted_data)

        except Exception as e:
            logger.error(f"Data migration failed: {e}")
            raise

"""End-to-End Encryption Service

Provides field-level encryption for sensitive data like safe contact details,
classified intelligence, and personnel medical information.
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os
import logging
from typing import Optional, Dict
import json

logger = logging.getLogger(__name__)


class EncryptionService:
    """Manages encryption and decryption of sensitive data"""

    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption service

        Args:
            master_key: Master encryption key (from environment or key management)
        """
        self.master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY')

        if not self.master_key:
            raise ValueError("ENCRYPTION_MASTER_KEY not configured")

        # Derive encryption key from master key
        self.fernet = self._create_fernet()

    def _create_fernet(self) -> Fernet:
        """Create Fernet cipher from master key"""
        # Derive a key using PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'watchkeeper_salt',  # In production, use unique salt per installation
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext data

        Args:
            plaintext: Data to encrypt

        Returns:
            Base64-encoded encrypted data
        """
        if not plaintext:
            return ""

        try:
            encrypted = self.fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt encrypted data

        Args:
            ciphertext: Base64-encoded encrypted data

        Returns:
            Decrypted plaintext
        """
        if not ciphertext:
            return ""

        try:
            decrypted = self.fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise

    def encrypt_dict(self, data: Dict) -> str:
        """Encrypt a dictionary as JSON

        Args:
            data: Dictionary to encrypt

        Returns:
            Encrypted JSON string
        """
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, ciphertext: str) -> Dict:
        """Decrypt JSON dictionary

        Args:
            ciphertext: Encrypted JSON string

        Returns:
            Decrypted dictionary
        """
        json_str = self.decrypt(ciphertext)
        return json.loads(json_str)

    def encrypt_safe_contact(self, contact_data: Dict) -> Dict:
        """Encrypt sensitive safe contact information

        Args:
            contact_data: Safe contact data with sensitive fields

        Returns:
            Contact data with encrypted sensitive fields
        """
        sensitive_fields = [
            'phone', 'alternate_phone', 'email',
            'address', 'access_code', 'notes'
        ]

        encrypted_data = contact_data.copy()
        encrypted_details = {}

        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_details[field] = encrypted_data[field]
                del encrypted_data[field]

        # Encrypt all sensitive fields together
        if encrypted_details:
            encrypted_data['encrypted_details'] = self.encrypt_dict(encrypted_details)

        return encrypted_data

    def decrypt_safe_contact(self, contact_data: Dict) -> Dict:
        """Decrypt safe contact information

        Args:
            contact_data: Contact data with encrypted fields

        Returns:
            Fully decrypted contact data
        """
        decrypted_data = contact_data.copy()

        if 'encrypted_details' in decrypted_data and decrypted_data['encrypted_details']:
            encrypted_details = self.decrypt_dict(decrypted_data['encrypted_details'])
            decrypted_data.update(encrypted_details)
            del decrypted_data['encrypted_details']

        return decrypted_data

    def encrypt_personnel_medical(self, medical_info: Dict) -> str:
        """Encrypt personnel medical information

        Args:
            medical_info: Medical information dictionary

        Returns:
            Encrypted medical info
        """
        return self.encrypt_dict(medical_info)

    def decrypt_personnel_medical(self, encrypted_medical: str) -> Dict:
        """Decrypt personnel medical information

        Args:
            encrypted_medical: Encrypted medical info

        Returns:
            Decrypted medical information
        """
        return self.decrypt_dict(encrypted_medical)

    def encrypt_classified_intelligence(self, content: str, classification: str = 'classified') -> Dict:
        """Encrypt classified intelligence content

        Args:
            content: Intelligence content to encrypt
            classification: Classification level

        Returns:
            Dictionary with encrypted content and metadata
        """
        return {
            'encrypted_content': self.encrypt(content),
            'classification': classification,
            'encrypted_at': datetime.utcnow().isoformat()
        }

    def decrypt_classified_intelligence(self, encrypted_data: Dict) -> str:
        """Decrypt classified intelligence

        Args:
            encrypted_data: Dictionary with encrypted content

        Returns:
            Decrypted intelligence content
        """
        return self.decrypt(encrypted_data['encrypted_content'])

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key

        Returns:
            Base64-encoded key suitable for use as ENCRYPTION_MASTER_KEY
        """
        return Fernet.generate_key().decode()

    def rotate_key(self, new_master_key: str):
        """Rotate encryption keys

        This should be called during a maintenance window to re-encrypt
        all encrypted data with a new key.

        Args:
            new_master_key: New master key to use
        """
        # Store old fernet for decryption
        old_fernet = self.fernet

        # Create new fernet with new key
        self.master_key = new_master_key
        self.fernet = self._create_fernet()

        logger.info("Encryption key rotated successfully")

        return old_fernet  # Return for re-encryption operations


# Singleton instance
_encryption_service = None


def get_encryption_service() -> EncryptionService:
    """Get singleton encryption service instance"""
    global _encryption_service

    if _encryption_service is None:
        _encryption_service = EncryptionService()

    return _encryption_service


# Utility functions for common operations
def encrypt_field(plaintext: str) -> str:
    """Quick encrypt a single field"""
    return get_encryption_service().encrypt(plaintext)


def decrypt_field(ciphertext: str) -> str:
    """Quick decrypt a single field"""
    return get_encryption_service().decrypt(ciphertext)


from datetime import datetime

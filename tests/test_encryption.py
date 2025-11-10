"""Tests for Encryption Service"""

import pytest
from app.services.encryption_service import EncryptionService
import os


class TestEncryptionService:
    """Test encryption service functionality"""

    @pytest.fixture
    def encryption_service(self):
        """Create encryption service for testing"""
        os.environ['ENCRYPTION_MASTER_KEY'] = 'test_master_key_for_testing_only'
        return EncryptionService()

    def test_encrypt_decrypt_string(self, encryption_service):
        """Test basic string encryption and decryption"""
        plaintext = "This is sensitive information"
        encrypted = encryption_service.encrypt(plaintext)

        assert encrypted != plaintext
        assert len(encrypted) > 0

        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_decrypt_dict(self, encryption_service):
        """Test dictionary encryption"""
        data = {
            "name": "John Doe",
            "phone": "+1234567890",
            "email": "john@example.com"
        }

        encrypted = encryption_service.encrypt_dict(data)
        assert isinstance(encrypted, str)

        decrypted = encryption_service.decrypt_dict(encrypted)
        assert decrypted == data

    def test_encrypt_safe_contact(self, encryption_service):
        """Test safe contact encryption"""
        contact = {
            "name": "Safe House Alpha",
            "phone": "+1234567890",
            "email": "contact@safehouse.org",
            "address": "123 Secret St",
            "access_code": "CODE123",
            "trust_level": 9
        }

        encrypted = encryption_service.encrypt_safe_contact(contact)

        # Sensitive fields should be removed
        assert 'phone' not in encrypted
        assert 'email' not in encrypted
        assert 'address' not in encrypted

        # Non-sensitive fields should remain
        assert encrypted['name'] == "Safe House Alpha"
        assert encrypted['trust_level'] == 9

        # Should have encrypted_details
        assert 'encrypted_details' in encrypted

        # Decrypt and verify
        decrypted = encryption_service.decrypt_safe_contact(encrypted)
        assert decrypted['phone'] == contact['phone']
        assert decrypted['email'] == contact['email']

    def test_empty_string_encryption(self, encryption_service):
        """Test encryption of empty strings"""
        encrypted = encryption_service.encrypt("")
        assert encrypted == ""

        decrypted = encryption_service.decrypt("")
        assert decrypted == ""

    def test_generate_key(self):
        """Test key generation"""
        key = EncryptionService.generate_key()
        assert isinstance(key, str)
        assert len(key) > 0

        # Should be able to create service with generated key
        os.environ['ENCRYPTION_MASTER_KEY'] = key
        service = EncryptionService()
        assert service is not None

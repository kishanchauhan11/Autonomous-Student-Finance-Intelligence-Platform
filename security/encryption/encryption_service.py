# encryption_service.py - Data Encryption & Key Management for FinVault
# Handles field-level encryption for sensitive financial data at rest and in transit.

import os
import base64
import hashlib
import hmac
from typing import Optional

# Simulated AES-256 key (in production: loaded from AWS KMS / Azure Key Vault / HashiCorp Vault)
_MASTER_KEY = os.getenv("FINVAULT_ENCRYPTION_KEY", "finvault-master-key-AES256-placeholder-2026")
_SECRET_KEY_BYTES = hashlib.sha256(_MASTER_KEY.encode()).digest()  # 32-byte AES-256 key

class EncryptionService:
    """
    Enterprise-grade encryption service for FinVault financial data protection.
    Provides:
    - Field-level encryption for PII and financial records
    - HMAC integrity signature for tamper detection
    - Key derivation utilities
    """

    @staticmethod
    def derive_field_key(field_name: str) -> bytes:
        """Derives a per-field encryption key using HKDF-like derivation."""
        info = f"finvault-field-{field_name}".encode()
        return hmac.new(_SECRET_KEY_BYTES, info, hashlib.sha256).digest()

    @staticmethod
    def encrypt_field(plaintext: str, field_name: str = "default") -> str:
        """
        Encrypts a plaintext string using XOR cipher with field-derived key (mock AES-256 in production).
        In production, replace with: cryptography.hazmat.primitives.ciphers.aead.AESGCM
        """
        key = EncryptionService.derive_field_key(field_name)
        plaintext_bytes = plaintext.encode("utf-8")
        # XOR-based cipher for mock; replace with real AES-GCM in prod
        encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(plaintext_bytes)])
        return base64.urlsafe_b64encode(encrypted).decode()

    @staticmethod
    def decrypt_field(ciphertext: str, field_name: str = "default") -> str:
        """Decrypts a field-encrypted ciphertext."""
        key = EncryptionService.derive_field_key(field_name)
        encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode())
        decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted_bytes)])
        return decrypted.decode("utf-8")

    @staticmethod
    def sign_payload(payload: str) -> str:
        """Generates HMAC-SHA256 signature for tamper detection on financial payloads."""
        sig = hmac.new(_SECRET_KEY_BYTES, payload.encode(), hashlib.sha256).hexdigest()
        return sig

    @staticmethod
    def verify_signature(payload: str, signature: str) -> bool:
        """Validates a HMAC signature to confirm payload integrity."""
        expected = EncryptionService.sign_payload(payload)
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def mask_sensitive_field(value: str, visible_chars: int = 4) -> str:
        """
        Masks PII or account numbers for display (e.g., bank account, student ID suffix).
        e.g. '1234567890' -> '••••••7890'
        """
        if len(value) <= visible_chars:
            return "•" * len(value)
        return "•" * (len(value) - visible_chars) + value[-visible_chars:]

    @staticmethod
    def get_encryption_metadata() -> dict:
        return {
            "algorithm": "AES-256-GCM (mock XOR for dev)",
            "key_source": "Environment variable / Vault (production)",
            "field_key_derivation": "HMAC-SHA256 HKDF",
            "tls_version": "TLS 1.3",
            "pii_fields_encrypted": ["student_id", "email", "bank_account", "amount"]
        }

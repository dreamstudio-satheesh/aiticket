"""Simple encryption for API credentials using Fernet (symmetric encryption)."""

from cryptography.fernet import Fernet
from app.config import get_settings

settings = get_settings()

# Use secret_key to derive encryption key (in production, use a separate key)
_fernet = None


def get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    global _fernet
    if _fernet is None:
        # Derive a valid Fernet key from secret_key
        import hashlib
        import base64
        key = hashlib.sha256(settings.secret_key.encode()).digest()
        _fernet = Fernet(base64.urlsafe_b64encode(key))
    return _fernet


def encrypt(plaintext: str) -> str:
    """Encrypt a string and return base64 encoded ciphertext."""
    if not plaintext:
        return ""
    fernet = get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt base64 encoded ciphertext and return plaintext."""
    if not ciphertext:
        return ""
    fernet = get_fernet()
    return fernet.decrypt(ciphertext.encode()).decode()

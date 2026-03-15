# src/encryption.py
"""
Secure Vault - Модуль шифрования
================================
AES-256 шифрование через Fernet, PBKDF2-HMAC-SHA256 для ключей.
"""

import os
import base64
import hashlib
import hmac
import json
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureVaultCrypto:
    """
    Класс для управления шифрованием Secure Vault.
    """
    
    SALT_LENGTH = 32
    KEY_LENGTH = 32
    ITERATIONS = 480_000
    HASH_ALGORITHM = hashes.SHA256()
    
    def __init__(self):
        self._salt: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None
    
    def generate_salt(self) -> bytes:
        """Генерирует криптографически безопасную случайную соль."""
        return os.urandom(self.SALT_LENGTH)
    
    def derive_key(self, master_password: str, salt: bytes) -> bytes:
        """Выводит ключ шифрования из мастер-пароля."""
        kdf = PBKDF2HMAC(
            algorithm=self.HASH_ALGORITHM,
            length=self.KEY_LENGTH,
            salt=salt,
            iterations=self.ITERATIONS,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode('utf-8')))
        return key
    
    def initialize(self, master_password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Инициализирует систему шифрования.
        Возвращает salt (новый или существующий).
        """
        if salt is None:
            self._salt = self.generate_salt()
        else:
            self._salt = salt
        
        key = self.derive_key(master_password, self._salt)
        self._fernet = Fernet(key)
        
        return self._salt
    
    def verify_master_password(self, master_password: str, salt: bytes, 
                               verification_hash: bytes) -> bool:
        """Проверяет мастер-пароль."""
        try:
            key = self.derive_key(master_password, salt)
            fernet = Fernet(key)
            decrypted = fernet.decrypt(verification_hash)
            return hmac.compare_digest(decrypted, b"secure_vault_verified")
        except (InvalidToken, Exception):
            return False
    
    def create_verification_hash(self) -> bytes:
        """Создает хэш для проверки мастер-пароля."""
        if not self._fernet:
            raise RuntimeError("Crypto not initialized")
        return self._fernet.encrypt(b"secure_vault_verified")
    
    def encrypt(self, plaintext: str) -> bytes:
        """Шифрует строку."""
        if not self._fernet:
            raise RuntimeError("Crypto not initialized")
        return self._fernet.encrypt(plaintext.encode('utf-8'))
    
    def decrypt(self, ciphertext: bytes) -> str:
        """Расшифровывает данные."""
        if not self._fernet:
            raise RuntimeError("Crypto not initialized")
        return self._fernet.decrypt(ciphertext).decode('utf-8')
    
    def encrypt_json(self, data: Dict[str, Any]) -> bytes:
        """Шифрует словарь в JSON и возвращает bytes."""
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt(json_str)
    
    def decrypt_json(self, ciphertext: bytes) -> Dict[str, Any]:
        """Расшифровывает bytes в словарь."""
        json_str = self.decrypt(ciphertext)
        return json.loads(json_str)
    
    def is_initialized(self) -> bool:
        """Проверяет, инициализирован ли крипто-модуль."""
        return self._fernet is not None


class SecurityError(Exception):
    """Исключение для ошибок безопасности."""
    pass


class InvalidPasswordError(SecurityError):
    """Неверный мастер-пароль."""
    pass
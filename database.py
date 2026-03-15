# src/database.py
"""
Secure Vault - База данных
==========================
SQLite с полным шифрованием чувствительных полей.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
from encryption import SecureVaultCrypto, SecurityError
from config import DATABASE_PATH
from typing import List, Dict, Optional, Any, Tuple


class Database:
    """
    Управление базой данных паролей.
    Все чувствительные данные шифруются перед сохранением.
    """
    
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self.crypto: Optional[SecureVaultCrypto] = None
        self._init_db()
    
    def _init_db(self):
        """Создает таблицы если не существуют."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица метаданных (соль, проверочный хэш)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vault_meta (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    salt BLOB NOT NULL,
                    verification_hash BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    last_access TEXT
                )
            ''')
            
            # Таблица аккаунтов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    service BLOB NOT NULL,      -- зашифровано
                    username BLOB NOT NULL,     -- зашифровано
                    password BLOB NOT NULL,     -- зашифровано
                    url BLOB,                   -- зашифровано
                    notes BLOB,                 -- зашифровано
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Контекстный менеджер для соединений."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def setup_new_vault(self, master_password: str) -> bool:
        """
        Создает новое хранилище с мастер-паролем.
        """
        try:
            self.crypto = SecureVaultCrypto()
            salt = self.crypto.initialize(master_password)
            verification_hash = self.crypto.create_verification_hash()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute('''
                    INSERT INTO vault_meta (id, salt, verification_hash, created_at, last_access)
                    VALUES (1, ?, ?, ?, ?)
                ''', (salt, verification_hash, now, now))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Error setting up vault: {e}")
            return False
    
    def unlock(self, master_password: str) -> bool:
        """
        Разблокирует хранилище.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT salt, verification_hash FROM vault_meta WHERE id = 1')
                row = cursor.fetchone()
                
                if not row:
                    return False
                
                salt, verification_hash = row['salt'], row['verification_hash']
                
                # Проверяем пароль
                temp_crypto = SecureVaultCrypto()
                if not temp_crypto.verify_master_password(master_password, salt, verification_hash):
                    return False
                
                # Инициализируем крипто-модуль
                self.crypto = SecureVaultCrypto()
                self.crypto.initialize(master_password, salt)
                
                # Обновляем last_access
                cursor.execute('UPDATE vault_meta SET last_access = ? WHERE id = 1',
                             (datetime.now().isoformat(),))
                conn.commit()
                
                return True
                
        except Exception as e:
            print(f"Unlock error: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """Проверяет, существует ли хранилище."""
        return self.db_path.exists() and self.db_path.stat().st_size > 0
    
    def needs_setup(self) -> bool:
        """Проверяет, нужна ли первоначальная настройка."""
        if not self.is_initialized():
            return True
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM vault_meta')
                return cursor.fetchone()[0] == 0
        except:
            return True
    
    def add_account(self, category: str, service: str, username: str,
                    password: str, url: str = "", notes: str = "") -> bool:
        """Добавляет новый аккаунт."""
        if not self.crypto:
            raise SecurityError("Vault not unlocked")
        
        try:
            encrypted_service = self.crypto.encrypt(service)
            encrypted_username = self.crypto.encrypt(username)
            encrypted_password = self.crypto.encrypt(password)
            encrypted_url = self.crypto.encrypt(url) if url else b''
            encrypted_notes = self.crypto.encrypt(notes) if notes else b''
            
            now = datetime.now().isoformat()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO accounts 
                    (category, service, username, password, url, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (category, encrypted_service, encrypted_username, 
                      encrypted_password, encrypted_url, encrypted_notes, now, now))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Error adding account: {e}")
            return False
    
    def get_accounts(self, category: Optional[str] = None, 
                     search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получает список аккаунтов с расшифровкой."""
        if not self.crypto:
            raise SecurityError("Vault not unlocked")
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if category:
                    cursor.execute('''
                        SELECT * FROM accounts WHERE category = ? ORDER BY created_at DESC
                    ''', (category,))
                else:
                    cursor.execute('SELECT * FROM accounts ORDER BY created_at DESC')
                
                rows = cursor.fetchall()
                accounts = []
                
                for row in rows:
                    try:
                        account = {
                            'id': row['id'],
                            'category': row['category'],
                            'service': self.crypto.decrypt(row['service']),
                            'username': self.crypto.decrypt(row['username']),
                            'password': self.crypto.decrypt(row['password']),
                            'url': self.crypto.decrypt(row['url']) if row['url'] else '',
                            'notes': self.crypto.decrypt(row['notes']) if row['notes'] else '',
                            'created_at': row['created_at'],
                            'updated_at': row['updated_at']
                        }
                        
                        # Фильтрация по поиску
                        if search:
                            search_lower = search.lower()
                            if (search_lower in account['service'].lower() or 
                                search_lower in account['username'].lower() or
                                search_lower in account['url'].lower()):
                                accounts.append(account)
                        else:
                            accounts.append(account)
                            
                    except Exception as e:
                        print(f"Error decrypting account {row['id']}: {e}")
                        continue
                
                return accounts
                
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return []
    
    def update_account(self, account_id: int, **kwargs) -> bool:
        """Обновляет аккаунт."""
        if not self.crypto:
            raise SecurityError("Vault not unlocked")
        
        try:
            updates = []
            values = []
            
            encrypt_fields = ['service', 'username', 'password', 'url', 'notes']
            
            for key, value in kwargs.items():
                if key in encrypt_fields:
                    updates.append(f"{key} = ?")
                    values.append(self.crypto.encrypt(value))
            
            if not updates:
                return False
            
            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(account_id)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE accounts SET {', '.join(updates)} WHERE id = ?
                ''', values)
                conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error updating account: {e}")
            return False
    
    def delete_account(self, account_id: int) -> bool:
        """Удаляет аккаунт."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting account: {e}")
            return False
    
    def get_categories_count(self) -> Dict[str, int]:
        """Возвращает количество аккаунтов по категориям."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT category, COUNT(*) as count 
                    FROM accounts 
                    GROUP BY category
                ''')
                return {row['category']: row['count'] for row in cursor.fetchall()}
        except:
            return {}
    
    def export_encrypted(self, export_path: Path) -> bool:
        """
        Экспортирует базу в зашифрованный JSON.
        """
        if not self.crypto:
            raise SecurityError("Vault not unlocked")
        
        try:
            accounts = self.get_accounts()
            export_data = {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'accounts': accounts
            }
            
            encrypted_data = self.crypto.encrypt_json(export_data)
            
            with open(export_path, 'wb') as f:
                f.write(encrypted_data)
            
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def import_encrypted(self, import_path: Path, merge: bool = False) -> Tuple[bool, str]:
        """
        Импортирует зашифрованный JSON.
        
        Args:
            import_path: Путь к файлу
            merge: Если True - добавляет к существующим, False - заменяет
        
        Returns:
            (успех, сообщение)
        """
        if not self.crypto:
            raise SecurityError("Vault not unlocked")
        
        try:
            with open(import_path, 'rb') as f:
                encrypted_data = f.read()
            
            data = self.crypto.decrypt_json(encrypted_data)
            accounts = data.get('accounts', [])
            
            if not merge:
                # Очищаем существующие
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM accounts')
                    conn.commit()
            
            imported = 0
            for acc in accounts:
                if self.add_account(
                    category=acc['category'],
                    service=acc['service'],
                    username=acc['username'],
                    password=acc['password'],
                    url=acc.get('url', ''),
                    notes=acc.get('notes', '')
                ):
                    imported += 1
            
            return True, f"Импортировано {imported} аккаунтов"
            
        except Exception as e:
            return False, f"Ошибка импорта: {e}"
    
    def lock(self):
        """Блокирует доступ к данным."""
        self.crypto = None
    
    def change_master_password(self, new_password: str) -> bool:
        """Меняет мастер-пароль (перешифровывает все данные)."""
        if not self.crypto:
            raise SecurityError("Vault not unlocked")
        
        try:
            # Получаем все аккаунты
            accounts = self.get_accounts()
            
            # Создаем новый ключ
            new_crypto = SecureVaultCrypto()
            new_salt = new_crypto.generate_salt()
            new_crypto.initialize(new_password, new_salt)
            
            # Обновляем метаданные
            new_verification = new_crypto.create_verification_hash()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE vault_meta 
                    SET salt = ?, verification_hash = ? 
                    WHERE id = 1
                ''', (new_salt, new_verification))
                
                # Перешифровываем все аккаунты
                for acc in accounts:
                    enc_service = new_crypto.encrypt(acc['service'])
                    enc_username = new_crypto.encrypt(acc['username'])
                    enc_password = new_crypto.encrypt(acc['password'])
                    enc_url = new_crypto.encrypt(acc['url']) if acc['url'] else b''
                    enc_notes = new_crypto.encrypt(acc['notes']) if acc['notes'] else b''
                    
                    cursor.execute('''
                        UPDATE accounts 
                        SET service = ?, username = ?, password = ?, url = ?, notes = ?
                        WHERE id = ?
                    ''', (enc_service, enc_username, enc_password, 
                          enc_url, enc_notes, acc['id']))
                
                conn.commit()
            
            # Применяем новый ключ
            self.crypto = new_crypto
            return True
            
        except Exception as e:
            print(f"Error changing password: {e}")
            return False
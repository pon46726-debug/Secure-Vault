# main.py
"""
Secure Vault - Точка входа
==========================
Запуск приложения.
"""

import sys
from pathlib import Path

# Добавляем src в путь
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from gui import SecureVaultGUI


def main():
    """Главная функция."""
    app = SecureVaultGUI()
    app.run()


if __name__ == "__main__":
    main()
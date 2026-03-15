# src/config.py
"""
Secure Vault - Конфигурация
===========================
Все настройки, пути и константы проекта.
"""

import os
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).parent.parent.absolute()
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"

# Создаем папку данных если нет
DATA_DIR.mkdir(exist_ok=True)

# Пути к файлам
DATABASE_PATH = DATA_DIR / "vault.db"
EXPORT_PATH = DATA_DIR / "exports"
EXPORT_PATH.mkdir(exist_ok=True)

# Настройки безопасности
AUTO_LOCK_MINUTES = 5
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_DURATION = 300  # 5 минут блокировки после неудачных попыток

# Настройки генератора паролей
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 15
PASSWORD_DEFAULT_LENGTH = 14

# Настройки UI
THEME_COLOR = "dark-blue"
ACCENT_COLOR = "#00BFFF"  # Неоновый синий
SUCCESS_COLOR = "#00FF7F"  # Неоновый зеленый
WARNING_COLOR = "#FFD700"  # Золотой
DANGER_COLOR = "#FF4444"  # Красный
BG_COLOR = "#1a1a1a"
CARD_BG = "#2d2d2d"

# Категории с иконками
CATEGORIES = {
    "Соцсети": "🌐",
    "Работа": "💼",
    "Финансы": "💳",
    "Игры": "🎮",
    "Почта": "📧",
    "Облако": "☁️",
    "Другое": "📁"
}

# Версия
VERSION = "1.0.0"
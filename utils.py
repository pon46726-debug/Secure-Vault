# src/utils.py
"""
Secure Vault - Утилиты
======================
Генератор паролей, оценка сложности, вспомогательные функции.
"""

import re
import secrets
import string
from typing import Tuple
from config import (
    PASSWORD_MIN_LENGTH, 
    PASSWORD_MAX_LENGTH, 
    PASSWORD_DEFAULT_LENGTH
)


class PasswordGenerator:
    """
    Генератор криптографически безопасных паролей.
    Использует secrets вместо random (защита от предсказуемости).
    """
    
    def __init__(self):
        self.lowercase = string.ascii_lowercase
        self.uppercase = string.ascii_uppercase
        self.digits = string.digits
        self.special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        self.all_chars = self.lowercase + self.uppercase + self.digits + self.special
    
    def generate(self, length: int = PASSWORD_DEFAULT_LENGTH) -> str:
        """
        Генерирует пароль с гарантированным наличием всех типов символов.
        
        Args:
            length: Длина пароля (12-15)
        
        Returns:
            Сгенерированный пароль
        """
        if not PASSWORD_MIN_LENGTH <= length <= PASSWORD_MAX_LENGTH:
            length = PASSWORD_DEFAULT_LENGTH
        
        # Гарантируем минимум по одному символу каждого типа
        password = [
            secrets.choice(self.lowercase),
            secrets.choice(self.uppercase),
            secrets.choice(self.digits),
            secrets.choice(self.special),
        ]
        
        # Оставшиеся символы - случайные
        for _ in range(length - 4):
            password.append(secrets.choice(self.all_chars))
        
        # Перемешиваем
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def generate_custom(self, length: int, 
                       use_upper: bool = True,
                       use_lower: bool = True,
                       use_digits: bool = True,
                       use_special: bool = True) -> str:
        """Генерирует пароль с кастомными настройками."""
        chars = ""
        password = []
        
        if use_lower:
            chars += self.lowercase
            password.append(secrets.choice(self.lowercase))
        if use_upper:
            chars += self.uppercase
            password.append(secrets.choice(self.uppercase))
        if use_digits:
            chars += self.digits
            password.append(secrets.choice(self.digits))
        if use_special:
            chars += self.special
            password.append(secrets.choice(self.special))
        
        if not chars:
            return self.generate(length)
        
        for _ in range(length - len(password)):
            password.append(secrets.choice(chars))
        
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)


class PasswordStrengthChecker:
    """Проверяет сложность пароля."""
    
    @staticmethod
    def check(password: str) -> Tuple[int, str, str]:
        """
        Оценивает сложность пароля.
        
        Returns:
            (score 0-100, уровень, цвет)
        """
        score = 0
        checks = {
            'length': len(password) >= 12,
            'upper': bool(re.search(r'[A-Z]', password)),
            'lower': bool(re.search(r'[a-z]', password)),
            'digit': bool(re.search(r'\d', password)),
            'special': bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password)),
        }
        
        # Базовые баллы
        score += len(password) * 4  # До 60 баллов за длину
        score += sum(checks.values()) * 10  # 50 баллов за разнообразие
        
        # Бонусы
        if len(password) >= 14:
            score += 10
        if all(checks.values()):
            score += 10
        
        score = min(100, score)
        
        # Определяем уровень
        if score >= 80:
            return score, "Очень сильный", "#00FF7F"  # Зеленый
        elif score >= 60:
            return score, "Сильный", "#7FFF00"  # Светло-зеленый
        elif score >= 40:
            return score, "Средний", "#FFD700"  # Желтый
        else:
            return score, "Слабый", "#FF4444"  # Красный
    
    @staticmethod
    def get_requirements_text() -> str:
        """Возвращает требования к паролю."""
        return "• 12-15 символов\n• Верхний и нижний регистр\n• Цифры\n• Спецсимволы"


def format_timestamp(timestamp: str) -> str:
    """Форматирует timestamp для отображения."""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return timestamp


def truncate_text(text: str, max_length: int = 30) -> str:
    """Обрезает текст с многоточием."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
# src/gui.py
"""
Secure Vault — Premium UI
=========================
Glassmorphism, анимации, плавные переходы, интегрированные формы.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import threading
import subprocess
import time
import pyperclip

from config import (
    THEME_COLOR, ACCENT_COLOR, SUCCESS_COLOR, WARNING_COLOR, 
    DANGER_COLOR, BG_COLOR, CARD_BG, CATEGORIES, AUTO_LOCK_MINUTES,
    EXPORT_PATH, PASSWORD_DEFAULT_LENGTH
)
from database import Database
from utils import PasswordGenerator, PasswordStrengthChecker, truncate_text


def copy_to_clipboard(text):
    """Кроссплатформенное копирование с fallback."""
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        # Fallback для Windows через clip
        try:
            subprocess.run(['clip'], input=text.strip(), text=True, 
                         check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except Exception:
            # Последний fallback — через powershell
            try:
                cmd = f'Set-Clipboard -Value "{text.replace('"', '`"')}"'
                subprocess.run(['powershell', '-Command', cmd], 
                             check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                return True
            except:
                return False


class ModernButton(ctk.CTkButton):
    """Кнопка с hover-эффектами."""
    
    def __init__(self, *args, glow=False, **kwargs):
        self.glow = glow
        super().__init__(*args, **kwargs)
        
        if glow:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, e=None):
        self.configure(border_color=ACCENT_COLOR, border_width=2)
    
    def _on_leave(self, e=None):
        self.configure(border_color="#3d3d5c", border_width=0)


class CategorySidebar(ctk.CTkFrame):
    """Боковая панель с раскрывающимися категориями."""
    
    def __init__(self, parent, on_select, **kwargs):
        super().__init__(parent, width=280, fg_color="#1a1a2e", corner_radius=0, **kwargs)
        self.on_select = on_select
        self.selected = "Все"
        self.expanded = True
        
        self._build_ui()
    
    def _build_ui(self):
        # Лого с glow эффектом
        logo_frame = ctk.CTkFrame(self, fg_color="#1a1a2e", height=100)
        logo_frame.pack(fill="x", padx=20, pady=30)
        logo_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            logo_frame, text="🔐", font=("Segoe UI Emoji", 48)
        ).pack()
        
        ctk.CTkLabel(
            logo_frame, text="SECURE VAULT", 
            font=("Roboto", 20, "bold"), text_color=ACCENT_COLOR
        ).pack()
        
        ctk.CTkLabel(
            logo_frame, text="v2.0 Premium", 
            font=("Roboto", 10), text_color="gray"
        ).pack()
        
        # Разделитель с градиентом
        sep = ctk.CTkFrame(self, height=2, fg_color=ACCENT_COLOR)
        sep.pack(fill="x", padx=30, pady=10)
        
        # Секция категорий
        ctk.CTkLabel(
            self, text="КАТЕГОРИИ", font=("Roboto", 11, "bold"),
            text_color="gray"
        ).pack(anchor="w", padx=30, pady=(20, 10))
        
        # Кнопка "Все"
        self._create_cat_button("📁", "Все", True)
        
        # Раскрывающийся список категорий
        self.cat_container = ctk.CTkFrame(self, fg_color="#1a1a2e")
        self.cat_container.pack(fill="x", padx=20)
        
        for cat, icon in CATEGORIES.items():
            self._create_cat_button(icon, cat, False, self.cat_container)
        
        # Разделитель
        ctk.CTkFrame(self, height=2, fg_color="#2d2d44").pack(
            fill="x", padx=30, pady=20
        )
        
        # Быстрые действия
        ctk.CTkLabel(
            self, text="ДЕЙСТВИЯ", font=("Roboto", 11, "bold"),
            text_color="gray"
        ).pack(anchor="w", padx=30, pady=(10, 10))
        
        actions = [
            ("➕ Новый аккаунт", self._on_add, ACCENT_COLOR),
            ("💾 Экспорт", self._on_export, "#7B68EE"),
            ("📥 Импорт", self._on_import, "#7B68EE"),
        ]
        
        for text, cmd, color in actions:
            btn = ctk.CTkButton(
                self, text=text, command=cmd,
                fg_color="#1a1a2e", hover_color="#2d2d44",
                anchor="w", height=45, font=("Roboto", 12),
                text_color=color, corner_radius=10
            )
            btn.pack(fill="x", padx=20, pady=3)
        
        # Нижняя панель — блокировка
        bottom = ctk.CTkFrame(self, fg_color="#1a1a2e")
        bottom.pack(side="bottom", fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            bottom, text="🔒 Блокировать", command=self._on_lock,
            fg_color=DANGER_COLOR, hover_color="#CC3333",
            height=45, font=("Roboto", 12, "bold"), corner_radius=12
        ).pack(fill="x")
    
    def _create_cat_button(self, icon, text, is_active, parent=None):
        """Создает кнопку категории с hover-эффектом."""
        target = parent or self
        
        btn = ctk.CTkButton(
            target, text=f"{icon}  {text}",
            command=lambda t=text: self._select(t),
            fg_color=ACCENT_COLOR if is_active else "#1a1a2e",
            hover_color="#2d2d44",
            anchor="w", height=40,
            font=("Roboto", 13, "bold" if is_active else "normal"),
            text_color="white" if is_active else "gray",
            corner_radius=10
        )
        btn.pack(fill="x", padx=10 if parent else 20, pady=2)
        
        if is_active:
            self.active_btn = btn
        
        return btn
    
    def _select(self, category):
        """Обработка выбора категории."""
        self.selected = category
        self.on_select(category)
        
        # Обновляем визуал
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkButton) and "категор" not in widget.cget("text").lower():
                is_active = category in widget.cget("text")
                widget.configure(
                    fg_color=ACCENT_COLOR if is_active else "#1a1a2e",
                    text_color="white" if is_active else "gray",
                    font=("Roboto", 13, "bold" if is_active else "normal")
                )
    
    def _on_add(self):
        self.on_select("__ADD__")
    
    def _on_export(self):
        self.on_select("__EXPORT__")
    
    def _on_import(self):
        self.on_select("__IMPORT__")
    
    def _on_lock(self):
        self.on_select("__LOCK__")


class AccountCard(ctk.CTkFrame):
    """Карточка аккаунта с анимациями."""
    
    def __init__(self, parent, account, on_copy, on_edit, on_delete, **kwargs):
        super().__init__(
            parent, fg_color="#252538", corner_radius=16,
            border_width=1, border_color="#3d3d5c",
            **kwargs
        )
        self.account = account
        self.on_copy = on_copy
        self.on_edit = on_edit
        self.on_delete = on_delete
        
        self._build_ui()
        self._bind_hover()
    
    def _build_ui(self):
        # Градиентный индикатор слева
        indicator = ctk.CTkFrame(self, width=4, fg_color=ACCENT_COLOR, corner_radius=2)
        indicator.pack(side="left", fill="y", padx=0, pady=0)
        
        # Контент
        content = ctk.CTkFrame(self, fg_color="#252538")
        content.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        
        # Верхняя строка: иконка + сервис + категория
        header = ctk.CTkFrame(content, fg_color="#252538")
        header.pack(fill="x")
        
        icon = CATEGORIES.get(self.account['category'], '📁')
        ctk.CTkLabel(
            header, text=icon, font=("Segoe UI Emoji", 28)
        ).pack(side="left")
        
        service_frame = ctk.CTkFrame(header, fg_color="#252538")
        service_frame.pack(side="left", padx=(15, 0))
        
        ctk.CTkLabel(
            service_frame, text=self.account['service'],
            font=("Roboto", 18, "bold"), text_color="white"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            service_frame, 
            text=f"{self.account['category']} • {self.account['username']}",
            font=("Roboto", 12), text_color="gray"
        ).pack(anchor="w")
        
        # URL если есть
        if self.account.get('url'):
            ctk.CTkLabel(
                content, text=f"🌐 {truncate_text(self.account['url'], 50)}",
                font=("Roboto", 11), text_color="#7B68EE"
            ).pack(anchor="w", pady=(10, 0))
        
        # Кнопки действий справа
        actions = ctk.CTkFrame(self, fg_color="#252538")
        actions.pack(side="right", padx=20, pady=20)
        
        # Копировать с glow
        copy_btn = ModernButton(
            actions, text="📋", width=50, height=50,
            command=self._copy_action,
            fg_color="#2d2d44", hover_color=SUCCESS_COLOR,
            font=("Segoe UI Emoji", 20), corner_radius=12,
            glow=True
        )
        copy_btn.pack(pady=5)
        
        # Редактировать
        edit_btn = ctk.CTkButton(
            actions, text="✏️", width=50, height=50,
            command=self.on_edit,
            fg_color="#2d2d44", hover_color=ACCENT_COLOR,
            font=("Segoe UI Emoji", 18), corner_radius=12
        )
        edit_btn.pack(pady=5)
        
        # Удалить
        del_btn = ctk.CTkButton(
            actions, text="🗑️", width=50, height=50,
            command=self._delete_action,
            fg_color="#2d2d44", hover_color=DANGER_COLOR,
            font=("Segoe UI Emoji", 18), corner_radius=12
        )
        del_btn.pack(pady=5)
    
    def _bind_hover(self):
        """Привязывает hover-эффекты."""
        def on_enter(e):
            self.configure(border_color=ACCENT_COLOR, fg_color="#2d2d44")
        
        def on_leave(e):
            self.configure(border_color="#3d3d5c", fg_color="#252538")
        
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)
    
    def _copy_action(self):
        """Копирование с анимацией."""
        if copy_to_clipboard(self.account['password']):
            # Анимация успеха
            original = self.cget("border_color")
            self.configure(border_color=SUCCESS_COLOR)
            self.after(300, lambda: self.configure(border_color=original))
    
    def _delete_action(self):
        """Удаление с подтверждением."""
        if messagebox.askyesno(
            "⚠️ Подтверждение удаления",
            f"Удалить аккаунт '{self.account['service']}'?\n\n"
            f"Логин: {self.account['username']}\n\n"
            f"Это действие нельзя отменить!",
            icon='warning'
        ):
            self.on_delete()


class InlineForm(ctk.CTkFrame):
    """Встроенная форма добавления/редактирования."""
    
    def __init__(self, parent, on_save, on_cancel, account=None, **kwargs):
        super().__init__(
            parent, fg_color="#1e1e2e", corner_radius=20,
            border_width=2, border_color=ACCENT_COLOR,
            **kwargs
        )
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.account = account
        self.is_edit = account is not None
        
        self._build_ui()
    
    def _build_ui(self):
        # Заголовок
        title = "✏️ Редактирование" if self.is_edit else "➕ Новый аккаунт"
        ctk.CTkLabel(
            self, text=title, font=("Roboto", 24, "bold"),
            text_color=ACCENT_COLOR
        ).pack(pady=30)
        
        # Форма в две колонки
        form = ctk.CTkFrame(self, fg_color="#1e1e2e")
        form.pack(fill="x", padx=40)
        form.grid_columnconfigure(1, weight=1)
        
        # Поля формы
        fields = [
            ("Категория", "category", "combo", list(CATEGORIES.keys())),
            ("Название сервиса", "service", "entry", None),
            ("Логин / Email", "username", "entry", None),
            ("Пароль", "password", "password", None),
            ("URL (опционально)", "url", "entry", None),
        ]
        
        self.inputs = {}
        
        for i, (label, key, type_, extra) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            
            # Лейбл
            ctk.CTkLabel(
                form, text=label, font=("Roboto", 12),
                text_color="gray"
            ).grid(row=row*2, column=col, sticky="w", padx=10, pady=(20, 5))
            
            # Поле ввода
            if type_ == "combo":
                widget = ctk.CTkComboBox(
                    form, values=extra, width=300, height=45,
                    font=("Roboto", 13), dropdown_font=("Roboto", 12),
                    button_color=ACCENT_COLOR, border_color="#3d3d5c",
                    fg_color="#252538"
                )
                if self.is_edit:
                    widget.set(self.account.get(key, extra[0]))
                else:
                    widget.set(extra[-1])  # "Другое"
            
            elif type_ == "password":
                widget = ctk.CTkFrame(form, fg_color="#1e1e2e")
                
                entry = ctk.CTkEntry(
                    widget, width=240, height=45, show="•",
                    font=("Roboto", 13), border_color="#3d3d5c",
                    fg_color="#252538"
                )
                entry.pack(side="left")
                
                # Кнопка генерации
                gen_btn = ctk.CTkButton(
                    widget, text="🎲", width=45, height=45,
                    command=self._generate_password,
                    fg_color=ACCENT_COLOR, hover_color="#0099CC",
                    font=("Segoe UI Emoji", 16)
                )
                gen_btn.pack(side="left", padx=5)
                
                # Индикатор сложности под полем
                self.strength_bar = ctk.CTkProgressBar(
                    form, width=300, height=6, progress_color=DANGER_COLOR
                )
                self.strength_bar.grid(row=row*2+1, column=col+1, sticky="w", padx=10, pady=(5, 0))
                self.strength_bar.set(0)
                
                entry.bind('<KeyRelease>', self._check_strength)
                
                if self.is_edit:
                    entry.insert(0, self.account.get(key, ""))
                
                self.inputs[key] = entry
                widget.grid(row=row*2+1, column=col, padx=10, pady=5, sticky="w")
                continue
            
            else:  # entry
                widget = ctk.CTkEntry(
                    form, width=300, height=45,
                    font=("Roboto", 13), border_color="#3d3d5c",
                    fg_color="#252538"
                )
                if self.is_edit:
                    widget.insert(0, self.account.get(key, ""))
            
            widget.grid(row=row*2+1, column=col, padx=10, pady=5, sticky="w")
            self.inputs[key] = widget
        
        # Заметки (полная ширина)
        notes_row = len(fields)
        ctk.CTkLabel(
            form, text="Заметки", font=("Roboto", 12),
            text_color="gray"
        ).grid(row=notes_row*2, column=0, sticky="w", padx=10, pady=(20, 5))
        
        self.notes = ctk.CTkTextbox(
            form, width=640, height=100,
            font=("Roboto", 12), border_color="#3d3d5c",
            fg_color="#252538", wrap="word"
        )
        self.notes.grid(row=notes_row*2+1, column=0, columnspan=4, 
                       padx=10, pady=5, sticky="ew")
        
        if self.is_edit:
            self.notes.insert("1.0", self.account.get('notes', ''))
        
        # Кнопки
        btn_frame = ctk.CTkFrame(self, fg_color="#1e1e2e")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(
            btn_frame, text="💾 Сохранить", command=self._save,
            fg_color=SUCCESS_COLOR, hover_color="#00CC66",
            text_color="black", width=180, height=50,
            font=("Roboto", 14, "bold"), corner_radius=12
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, text="❌ Отмена", command=self.on_cancel,
            fg_color="#1e1e2e", border_color="#3d3d5c",
            border_width=2, width=180, height=50,
            font=("Roboto", 14), corner_radius=12
        ).pack(side="left", padx=10)
    
    def _generate_password(self):
        """Генерация пароля."""
        gen = PasswordGenerator()
        pwd = gen.generate(PASSWORD_DEFAULT_LENGTH)
        
        self.inputs['password'].delete(0, 'end')
        self.inputs['password'].insert(0, pwd)
        self._check_strength()
    
    def _check_strength(self, event=None):
        """Обновление индикатора сложности."""
        pwd = self.inputs['password'].get()
        checker = PasswordStrengthChecker()
        score, level, color = checker.check(pwd)
        
        self.strength_bar.set(score / 100)
        self.strength_bar.configure(progress_color=color)
    
    def _save(self):
        """Сохранение данных."""
        data = {
            'category': self.inputs['category'].get(),
            'service': self.inputs['service'].get().strip(),
            'username': self.inputs['username'].get().strip(),
            'password': self.inputs['password'].get(),
            'url': self.inputs['url'].get().strip(),
            'notes': self.notes.get("1.0", "end-1c").strip()
        }
        
        if not data['service'] or not data['username']:
            messagebox.showerror("Ошибка", "Заполните название сервиса и логин!")
            return
        
        if not data['password']:
            messagebox.showerror("Ошибка", "Введите пароль!")
            return
        
        self.on_save(data, self.is_edit, self.account['id'] if self.is_edit else None)


class SearchBar(ctk.CTkFrame):
    """Поисковая строка с иконкой."""
    
    def __init__(self, parent, on_search, **kwargs):
        super().__init__(
            parent, fg_color="#252538", corner_radius=15,
            height=60, **kwargs
        )
        self.on_search = on_search
        
        ctk.CTkLabel(
            self, text="🔍", font=("Segoe UI Emoji", 20)
        ).pack(side="left", padx=20)
        
        self.entry = ctk.CTkEntry(
            self, placeholder_text="Поиск по сервису, логину или URL...",
            font=("Roboto", 14), border_width=0, fg_color="#252538"
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=10)
        self.entry.bind('<KeyRelease>', lambda e: on_search(self.entry.get()))
        
        # Очистка
        self.clear_btn = ctk.CTkButton(
            self, text="✕", width=30, height=30,
            command=self._clear,
            fg_color="#252538", hover_color="#3d3d5c",
            font=("Roboto", 14)
        )
        self.clear_btn.pack(side="right", padx=15)
    
    def _clear(self):
        self.entry.delete(0, 'end')
        self.on_search("")


class SecureVaultGUI:
    """Главный класс приложения."""
    
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme(THEME_COLOR)
        
        self.db = Database()
        self.pwd_gen = PasswordGenerator()
        
        self.root = ctk.CTk()
        self.root.title("Secure Vault 🔐")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        self.root.configure(fg_color=BG_COLOR)
        
        # Таймеры
        self.last_activity = datetime.now()
        self.lock_timer = None
        self.is_locked = False
        
        self.current_view = "list"  # list, add, edit
        self.selected_account = None
        self.accounts = []
        
        self._bind_activity()
        self._start_lock_timer()
        
        if self.db.needs_setup():
            self.show_setup()
        else:
            self.show_login()
    
    def _bind_activity(self):
        """Отслеживание активности."""
        for event in ['<Key>', '<Button>', '<Motion>']:
            self.root.bind_all(event, self._reset_timer)
    
    def _reset_timer(self, event=None):
        self.last_activity = datetime.now()
    
    def _start_lock_timer(self):
        def check():
            if (self.db.crypto and self.db.crypto.is_initialized() and 
                not self.is_locked):
                if datetime.now() - self.last_activity > timedelta(minutes=AUTO_LOCK_MINUTES):
                    self._auto_lock()
            self.lock_timer = self.root.after(10000, check)
        self.lock_timer = self.root.after(10000, check)
    
    def _auto_lock(self):
        self.is_locked = True
        self.db.lock()
        self.show_login("🔒 Автоматическая блокировка")
    
    def clear(self):
        """Очистка окна."""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_setup(self):
        """Экран первоначальной настройки."""
        self.clear()
        
        # Центральная карточка
        card = ctk.CTkFrame(
            self.root, fg_color="#1e1e2e", corner_radius=25,
            width=500, height=600
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(
            card, text="🔐", font=("Segoe UI Emoji", 64)
        ).pack(pady=30)
        
        ctk.CTkLabel(
            card, text="Добро пожаловать",
            font=("Roboto", 28, "bold"), text_color="white"
        ).pack()
        
        ctk.CTkLabel(
            card, text="Создайте мастер-пароль для защиты данных",
            font=("Roboto", 14), text_color="gray"
        ).pack(pady=10)
        
        # Поля
        self.setup_pwd = ctk.CTkEntry(
            card, placeholder_text="Мастер-пароль", show="•",
            width=400, height=55, font=("Roboto", 14),
            border_color="#3d3d5c", fg_color="#252538",
            corner_radius=12
        )
        self.setup_pwd.pack(pady=20)
        
        self.setup_confirm = ctk.CTkEntry(
            card, placeholder_text="Подтвердите пароль", show="•",
            width=400, height=55, font=("Roboto", 14),
            border_color="#3d3d5c", fg_color="#252538",
            corner_radius=12
        )
        self.setup_confirm.pack(pady=10)
        
        # Индикатор сложности
        self.setup_strength = ctk.CTkProgressBar(
            card, width=400, height=8, progress_color=DANGER_COLOR
        )
        self.setup_strength.pack(pady=10)
        self.setup_strength.set(0)
        
        self.setup_strength_label = ctk.CTkLabel(
            card, text="Введите пароль", font=("Roboto", 12),
            text_color="gray"
        )
        self.setup_strength_label.pack()
        
        self.setup_pwd.bind('<KeyRelease>', self._check_setup_strength)
        
        # Требования
        ctk.CTkLabel(
            card, text="Минимум 8 символов, верхний/нижний регистр, цифры",
            font=("Roboto", 11), text_color="gray"
        ).pack(pady=20)
        
        # Кнопка
        ctk.CTkButton(
            card, text="Создать хранилище", command=self._do_setup,
            fg_color=ACCENT_COLOR, hover_color="#0099CC",
            height=55, width=400, font=("Roboto", 16, "bold"),
            corner_radius=12
        ).pack(pady=30)
    
    def _check_setup_strength(self, event=None):
        pwd = self.setup_pwd.get()
        score, level, color = PasswordStrengthChecker().check(pwd)
        self.setup_strength.set(score / 100)
        self.setup_strength.configure(progress_color=color)
        self.setup_strength_label.configure(text=level, text_color=color)
    
    def _do_setup(self):
        pwd = self.setup_pwd.get()
        confirm = self.setup_confirm.get()
        
        if len(pwd) < 8:
            messagebox.showerror("Ошибка", "Пароль слишком короткий!")
            return
        
        if pwd != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают!")
            return
        
        if self.db.setup_new_vault(pwd):
            messagebox.showinfo("Успех", "Хранилище создано!")
            self.show_main()
        else:
            messagebox.showerror("Ошибка", "Не удалось создать хранилище")
    
    def show_login(self, msg=""):
        """Экран входа."""
        self.clear()
        self.is_locked = False
        
        card = ctk.CTkFrame(
            self.root, fg_color="#1e1e2e", corner_radius=25,
            width=450, height=500
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(
            card, text="🔐", font=("Segoe UI Emoji", 64)
        ).pack(pady=40)
        
        ctk.CTkLabel(
            card, text="Secure Vault",
            font=("Roboto", 32, "bold"), text_color=ACCENT_COLOR
        ).pack()
        
        if msg:
            ctk.CTkLabel(
                card, text=msg, font=("Roboto", 12),
                text_color=WARNING_COLOR
            ).pack(pady=10)
        
        self.login_entry = ctk.CTkEntry(
            card, placeholder_text="Мастер-пароль", show="•",
            width=350, height=55, font=("Roboto", 14),
            border_color="#3d3d5c", fg_color="#252538",
            corner_radius=12
        )
        self.login_entry.pack(pady=30)
        self.login_entry.bind('<Return>', lambda e: self._do_login())
        
        ctk.CTkButton(
            card, text="Разблокировать", command=self._do_login,
            fg_color=SUCCESS_COLOR, hover_color="#00CC66",
            text_color="black", height=55, width=350,
            font=("Roboto", 16, "bold"), corner_radius=12
        ).pack(pady=20)
        
        self.login_entry.focus()
    
    def _do_login(self):
        pwd = self.login_entry.get()
        if self.db.unlock(pwd):
            self.show_main()
        else:
            messagebox.showerror("Ошибка", "Неверный пароль!")
            self.login_entry.delete(0, 'end')
    
    def show_main(self):
        """Главный экран."""
        self.clear()
        self.current_view = "list"
        
        # Layout
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = CategorySidebar(
            self.root, on_select=self._on_sidebar_action
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Main content
        self.content = ctk.CTkFrame(self.root, fg_color=BG_COLOR)
        self.content.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)
        
        # Header
        header = ctk.CTkFrame(self.content, fg_color=BG_COLOR)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header, text="Мои пароли",
            font=("Roboto", 32, "bold"), text_color="white"
        ).grid(row=0, column=0, sticky="w")
        
        # Статистика
        stats = self.db.get_categories_count()
        total = sum(stats.values())
        ctk.CTkLabel(
            header, text=f"Всего: {total} | Категорий: {len(stats)}",
            font=("Roboto", 12), text_color="gray"
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        # Поиск
        self.search_bar = SearchBar(self.content, on_search=self._on_search)
        self.search_bar.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Список аккаунтов
        self.list_container = ctk.CTkScrollableFrame(
            self.content, fg_color=BG_COLOR
        )
        self.list_container.grid(row=2, column=0, sticky="nsew")
        self.list_container.grid_columnconfigure(0, weight=1)
        
        self.load_accounts()
    
    def _on_sidebar_action(self, action):
        """Обработка действий sidebar."""
        if action == "__ADD__":
            self.show_inline_form()
        elif action == "__EXPORT__":
            self.export_data()
        elif action == "__IMPORT__":
            self.import_data()
        elif action == "__LOCK__":
            self._auto_lock()
        else:
            self.sidebar.selected = action
            self.load_accounts(category=action)
    
    def show_inline_form(self, account=None):
        """Показывает встроенную форму."""
        # Скрываем список
        self.list_container.grid_forget()
        self.search_bar.grid_forget()
        
        # Показываем форму
        self.inline_form = InlineForm(
            self.content,
            on_save=self._on_form_save,
            on_cancel=self._on_form_cancel,
            account=account
        )
        self.inline_form.grid(row=2, column=0, sticky="nsew")
        self.current_view = "edit" if account else "add"
        self.selected_account = account
    
    def _on_form_save(self, data, is_edit, account_id):
        """Сохранение из формы."""
        if is_edit:
            success = self.db.update_account(account_id, **data)
        else:
            success = self.db.add_account(**data)
        
        if success:
            self._on_form_cancel()
            self.load_accounts()
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить")
    
    def _on_form_cancel(self):
        """Отмена формы."""
        self.inline_form.destroy()
        self.search_bar.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        self.list_container.grid(row=2, column=0, sticky="nsew")
        self.current_view = "list"
        self.selected_account = None
    
    def load_accounts(self, category=None, search=""):
        """Загрузка списка аккаунтов."""
        # Очищаем
        for widget in self.list_container.winfo_children():
            widget.destroy()
        
        # Получаем данные
        cat = category if category and category != "Все" else None
        self.accounts = self.db.get_accounts(category=cat, search=search if search else None)
        
        if not self.accounts:
            empty = ctk.CTkFrame(
                self.list_container, fg_color=BG_COLOR
            )
            empty.pack(expand=True, pady=100)
            
            ctk.CTkLabel(
                empty, text="📭", font=("Segoe UI Emoji", 64)
            ).pack()
            
            ctk.CTkLabel(
                empty, text="Нет записей",
                font=("Roboto", 20), text_color="gray"
            ).pack(pady=10)
            
            ctk.CTkButton(
                empty, text="Добавить первый аккаунт",
                command=lambda: self.show_inline_form(),
                fg_color=ACCENT_COLOR, hover_color="#0099CC",
                height=45, font=("Roboto", 14)
            ).pack(pady=20)
            return
        
        # Появление карточек
        for i, acc in enumerate(self.accounts):
            card = AccountCard(
                self.list_container, acc,
                on_copy=self._copy_password,
                on_edit=lambda a=acc: self.show_inline_form(a),
                on_delete=lambda a=acc: self._delete_account(a)
            )
            card.pack(fill="x", pady=8)
    
    def _copy_password(self, password):
        """Копирование пароля."""
        if copy_to_clipboard(password):
            # Можно добавить визуальный фидбек — мигание экрана или тост
            pass
    
    def _delete_account(self, account):
        """Удаление аккаунта."""
        if self.db.delete_account(account['id']):
            self.load_accounts()
    
    def _on_search(self, query):
        """Поиск."""
        self.load_accounts(search=query)
    
    def export_data(self):
        """Экспорт."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".svault",
            filetypes=[("Secure Vault", "*.svault")],
            initialdir=EXPORT_PATH
        )
        if filename and self.db.export_encrypted(filename):
            messagebox.showinfo("Успех", "Бэкап создан!")
    
    def import_data(self):
        """Импорт."""
        filename = filedialog.askopenfilename(
            filetypes=[("Secure Vault", "*.svault")],
            initialdir=EXPORT_PATH
        )
        if filename:
            merge = messagebox.askyesno("Режим", "Объединить с текущими?")
            success, msg = self.db.import_encrypted(filename, merge)
            if success:
                messagebox.showinfo("Успех", msg)
                self.load_accounts()
            else:
                messagebox.showerror("Ошибка", msg)
    
    def run(self):
        self.root.mainloop()
        if self.lock_timer:
            self.root.after_cancel(self.lock_timer)
"""
Модуль графического интерфейса приложения CurRate.

Содержит классы для создания и управления GUI на базе Tkinter.
"""

import threading
import tkinter as tk
from typing import Optional
from datetime import datetime
from tkinter import ttk, messagebox

import pyperclip
from tkcalendar import Calendar

from .currency_converter import CurrencyConverter


class CurrencyConverterApp:
    """
    Главное окно приложения конвертера валют.

    Обеспечивает графический интерфейс для конвертации валют
    с использованием курсов ЦБ РФ.
    """

    def __init__(self, root: tk.Tk):
        """
        Инициализирует приложение.

        Args:
            root: Корневое окно Tkinter.
        """
        self.root = root
        self.converter = CurrencyConverter(use_cache=True)

        # Настройка окна
        self.root.title("Конвертер валют (с) BiV 2024 г.")
        self.root.minsize(340, 455)

        # Создание элементов интерфейса
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Создает все виджеты интерфейса."""
        self._create_date_widgets()
        self._create_calendar()
        self._create_currency_widgets()
        self._create_amount_widgets()
        self._create_buttons()
        self._create_result_label()

    def _create_date_widgets(self) -> None:
        """Создает виджеты для выбора даты."""
        tk.Label(self.root, text="Дата:").pack()

        self.date_entry = ttk.Entry(self.root)
        today_date = datetime.now().strftime('%d.%m.%Y')
        self.date_entry.insert(0, today_date)
        self.date_entry.pack()

    def _create_calendar(self) -> None:
        """Создает виджет календаря."""
        # Пытаемся установить русскую локаль, если не получается - используем по умолчанию
        try:
            self.calendar = Calendar(
                self.root,
                selectmode='day',
                locale='ru_RU',
                date_pattern='dd.mm.yyyy'
            )
        except Exception:
            # Если русская локаль недоступна, используем календарь без локали
            self.calendar = Calendar(
                self.root,
                selectmode='day',
                date_pattern='dd.mm.yyyy'
            )

        self.calendar.pack(pady=20)
        self.calendar.bind("<<CalendarSelected>>", lambda event: self._update_date_from_calendar())

    def _create_currency_widgets(self) -> None:
        """Создает виджеты для выбора валюты."""
        tk.Label(self.root, text="Выберите валюту:").pack()

        self.currency_var = tk.StringVar(value="USD")
        ttk.Radiobutton(
            self.root,
            text="USD",
            variable=self.currency_var,
            value="USD"
        ).pack()
        ttk.Radiobutton(
            self.root,
            text="EUR",
            variable=self.currency_var,
            value="EUR"
        ).pack()

    def _create_amount_widgets(self) -> None:
        """Создает виджеты для ввода суммы."""
        tk.Label(self.root, text="Введите сумму:").pack()

        self.amount_entry = ttk.Entry(self.root, width=27)
        self.amount_entry.pack()

    def _create_buttons(self) -> None:
        """Создает кнопки управления."""
        # Стиль для больших кнопок
        style = ttk.Style()
        style.configure("Large.TButton", font=("TkDefaultFont", 10), padding=10)

        # Кнопка конвертации
        self.convert_button = ttk.Button(
            self.root,
            text="Конвертировать",
            command=self._on_convert,
            style="Large.TButton"
        )
        self.convert_button.pack(pady=10)
        self.convert_button.config(width=20)

        # Кнопка копирования
        self.copy_button = ttk.Button(
            self.root,
            text="Копировать в буфер",
            command=self._copy_result,
            style="Large.TButton",
            state=tk.DISABLED  # Изначально неактивна
        )
        self.copy_button.pack(pady=10)
        self.copy_button.config(width=20)

    def _create_result_label(self) -> None:
        """Создает метку для отображения результата."""
        self.result_label = ttk.Label(
            self.root,
            text="Укажите дату и сумму конвертации",
            font=("TkDefaultFont", 10, "bold")
        )
        self.result_label.pack()

    def _update_date_from_calendar(self) -> None:
        """Обновляет поле даты при выборе в календаре."""
        selected_date = self.calendar.get_date()
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, selected_date)

    def _on_convert(self) -> None:
        """Обработчик нажатия кнопки конвертации."""
        # Получаем данные из полей
        date = self.date_entry.get()
        currency = self.currency_var.get().strip()
        normalized_currency = currency.upper()
        amount_str = self.amount_entry.get()

        amount = CurrencyConverter.parse_amount(amount_str)
        if amount is None:
            self._show_error("Некорректное значение суммы")
            return

        # Пока идет запрос, блокируем кнопку, чтобы не подвесить окно многократными вызовами
        self.copy_button.config(state=tk.DISABLED)
        self.convert_button.config(state=tk.DISABLED)
        self.result_label.config(text="Получаю курс...")

        worker = threading.Thread(
            target=self._perform_conversion,
            args=(amount, normalized_currency, date),
            daemon=True
        )
        worker.start()

    def _perform_conversion(self, amount: float, currency: str, date: str) -> None:
        """Выполняет конвертацию в фоновой нити, чтобы не блокировать GUI."""
        try:
            result, rate, error = self.converter.convert(amount, currency, date)
        except Exception as exc:  # Перехватываем неожиданные ошибки, чтобы не оставлять кнопку заблокированной
            error = f"Не удалось выполнить конвертацию: {exc}"
            result, rate = None, None

        self.root.after(
            0,
            lambda: self._finish_conversion(amount, currency, result, rate, error)
        )

    def _finish_conversion(
        self,
        amount: float,
        currency: str,
        result: Optional[float],
        rate: Optional[float],
        error: Optional[str]
    ) -> None:
        """Обновляет UI после завершения фонового запроса."""
        self.convert_button.config(state=tk.NORMAL)

        if error:
            self._show_error(error)
            return

        if result is not None and rate is not None:
            # Используем готовый result из convert(), чтобы избежать лишнего пересчёта
            formatted_result = self.converter.format_result(amount, rate, currency, result_in_rub=result)
            self.result_label.config(text=formatted_result)
            self.copy_button.config(state=tk.NORMAL)  # Активируем кнопку копирования

    def _copy_result(self) -> None:
        """Копирует результат в буфер обмена."""
        result_text = self.result_label.cget("text")
        try:
            pyperclip.copy(result_text)
            messagebox.showinfo("Успех", "Результат скопирован в буфер обмена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать в буфер: {e}")

    def _show_error(self, message: str) -> None:
        """
        Отображает сообщение об ошибке.

        Args:
            message: Текст сообщения об ошибке.
        """
        self.result_label.config(text=f"Ошибка: {message}")
        self.copy_button.config(state=tk.DISABLED)  # Деактивируем кнопку копирования

    def run(self) -> None:
        """Запускает главный цикл приложения."""
        self.root.mainloop()

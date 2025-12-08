"""
Модуль конвертации валют.

Обеспечивает конвертацию валют с использованием курсов ЦБ РФ
и кэширования для оптимизации производительности.
"""

from typing import Tuple, Optional
from datetime import datetime

from .cbr_parser import get_currency_rate, CBRParserError
from .cache import get_cache


class CurrencyConverter:
    """
    Конвертер валют с поддержкой кэширования.

    Использует курсы ЦБ РФ для конвертации USD и EUR в рубли.
    """

    SUPPORTED_CURRENCIES = ['USD', 'EUR']

    def __init__(self, use_cache: bool = True):
        """
        Инициализирует конвертер валют.

        Args:
            use_cache: Использовать кэширование курсов (по умолчанию True).
        """
        self._use_cache = use_cache
        self._cache = get_cache() if use_cache else None

    def convert(
        self,
        amount: float,
        from_currency: str,
        date: str
    ) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """
        Конвертирует валюту в рубли.

        Args:
            amount: Сумма для конвертации.
            from_currency: Исходная валюта (USD, EUR).
            date: Дата курса в формате DD.MM.YYYY.

        Returns:
            Tuple[float | None, float | None, str | None]:
                (результат в рублях, курс валюты, сообщение об ошибке).
                Если успешно - (результат, курс, None),
                если ошибка - (None, None, сообщение).
        """
        currency = self._normalize_currency(from_currency)

        # Валидация валюты
        if currency is None or currency not in self.SUPPORTED_CURRENCIES:
            return None, None, f"Неподдерживаемая валюта: {from_currency}"

        # Валидация суммы
        if amount <= 0:
            return None, None, "Сумма должна быть положительным числом"

        # Валидация даты
        validation_error = self._validate_date(date)
        if validation_error:
            return None, None, validation_error

        # Попытка получить курс из кэша
        rate = None
        if self._use_cache and self._cache is not None:
            rate = self._cache.get(currency, date)

        # Если в кэше нет, загружаем с сайта ЦБ РФ
        if rate is None:
            try:
                rate = get_currency_rate(currency, date)
                if rate is None:
                    return None, None, "Не удалось получить курс валюты"

                # Сохраняем в кэш
                if self._use_cache and self._cache is not None:
                    self._cache.set(currency, date, rate)

            except CBRParserError as e:
                return None, None, e.get_user_message()

        # Выполняем конвертацию
        result = amount * rate
        return result, rate, None

    def get_rate(
        self,
        currency: str,
        date: str
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Получает курс валюты на указанную дату.

        Args:
            currency: Код валюты (USD, EUR).
            date: Дата в формате DD.MM.YYYY.

        Returns:
            Tuple[float | None, str | None]: (курс, сообщение об ошибке).
        """
        normalized_currency = self._normalize_currency(currency)
        if normalized_currency is None or normalized_currency not in self.SUPPORTED_CURRENCIES:
            return None, f"Неподдерживаемая валюта: {currency}"

        validation_error = self._validate_date(date)
        if validation_error:
            return None, validation_error

        # Проверяем кэш
        rate = None
        if self._use_cache and self._cache is not None:
            rate = self._cache.get(normalized_currency, date)

        if rate is None:
            try:
                rate = get_currency_rate(normalized_currency, date)
                if rate is None:
                    return None, "Не удалось получить курс валюты"

                if self._use_cache and self._cache is not None:
                    self._cache.set(normalized_currency, date, rate)

            except CBRParserError as e:
                return None, e.get_user_message()

        return rate, None

    @staticmethod
    def _validate_date(date: str) -> Optional[str]:
        """
        Валидирует формат и значение даты.

        Args:
            date: Дата в формате DD.MM.YYYY.

        Returns:
            Optional[str]: Сообщение об ошибке или None, если дата валидна.
        """
        try:
            parsed_date = datetime.strptime(date, '%d.%m.%Y')

            # Проверяем, что дата не в будущем
            if parsed_date > datetime.now():
                return "Дата не может быть в будущем"

            return None

        except ValueError:
            return "Некорректный формат даты. Используйте DD.MM.YYYY"

    @staticmethod
    def format_result(
        amount: float,
        rate: float,
        currency: str
    ) -> str:
        """
        Форматирует результат конвертации для отображения.

        Args:
            amount: Исходная сумма.
            rate: Курс валюты.
            currency: Код валюты.

        Returns:
            str: Отформатированная строка результата.
        """
        result_in_rub = amount * rate
        normalized_currency = currency.upper()
        currency_symbol = "$" if normalized_currency == "USD" else "€"

        # Форматируем: разделитель тысяч - пробел, десятичный разделитель - запятая
        result_str = (
            f"{result_in_rub:,.2f} руб. "
            f"({currency_symbol}{amount:,.2f} по курсу {rate:,.4f})"
        )
        result_str = result_str.replace(',', ' ').replace('.', ',').replace(
            'руб,', 'руб.'
        )

        return result_str

    @staticmethod
    def parse_amount(amount_str: str) -> Optional[float]:
        """
        Нормализует строку суммы и преобразует ее в float.

        Убирает пробелы/неразрывные пробелы и разделители тысяч (пробел/точка/апостроф),
        заменяет запятую на точку. Если точек несколько, оставляет последнюю как
        десятичный разделитель.
        """
        if amount_str is None:
            return None

        cleaned = (
            amount_str.strip()
            .replace('\u00A0', '')
            .replace('\u202F', '')
            .replace(' ', '')
            .replace('_', '')
            .replace("'", '')
        )
        if not cleaned:
            return None

        cleaned = cleaned.replace(',', '.')
        if cleaned.count('.') > 1:
            parts = cleaned.split('.')
            cleaned = ''.join(parts[:-1]) + '.' + parts[-1]

        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _normalize_currency(currency: str) -> Optional[str]:
        """Возвращает код валюты в верхнем регистре или None, если строка пустая."""
        if currency is None:
            return None
        normalized = currency.strip().upper()
        return normalized if normalized else None

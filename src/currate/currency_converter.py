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
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Конвертирует валюту в рубли.

        Args:
            amount: Сумма для конвертации.
            from_currency: Исходная валюта (USD, EUR).
            date: Дата курса в формате DD.MM.YYYY.

        Returns:
            Tuple[float | None, str | None]: (результат в рублях, сообщение об ошибке).
            Если успешно - (результат, None), если ошибка - (None, сообщение).
        """
        # Валидация валюты
        if from_currency not in self.SUPPORTED_CURRENCIES:
            return None, f"Неподдерживаемая валюта: {from_currency}"

        # Валидация суммы
        if amount <= 0:
            return None, "Сумма должна быть положительным числом"

        # Валидация даты
        validation_error = self._validate_date(date)
        if validation_error:
            return None, validation_error

        # Попытка получить курс из кэша
        rate = None
        if self._use_cache:
            rate = self._cache.get(from_currency, date)

        # Если в кэше нет, загружаем с сайта ЦБ РФ
        if rate is None:
            try:
                rate = get_currency_rate(from_currency, date)
                if rate is None:
                    return None, "Не удалось получить курс валюты"

                # Сохраняем в кэш
                if self._use_cache:
                    self._cache.set(from_currency, date, rate)

            except CBRParserError as e:
                return None, str(e)

        # Выполняем конвертацию
        result = amount * rate
        return result, None

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
        if currency not in self.SUPPORTED_CURRENCIES:
            return None, f"Неподдерживаемая валюта: {currency}"

        validation_error = self._validate_date(date)
        if validation_error:
            return None, validation_error

        # Проверяем кэш
        rate = None
        if self._use_cache:
            rate = self._cache.get(currency, date)

        if rate is None:
            try:
                rate = get_currency_rate(currency, date)
                if rate is None:
                    return None, "Не удалось получить курс валюты"

                if self._use_cache:
                    self._cache.set(currency, date, rate)

            except CBRParserError as e:
                return None, str(e)

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
        currency_symbol = "$" if currency == "USD" else "€"

        # Форматируем: разделитель тысяч - пробел, десятичный разделитель - запятая
        result_str = f"{result_in_rub:,.2f} руб. ({currency_symbol}{amount:,.2f} по курсу {rate:,.4f})"
        result_str = result_str.replace(',', ' ').replace('.', ',').replace('руб,', 'руб.')

        return result_str

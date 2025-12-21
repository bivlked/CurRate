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

        # Нормализуем дату перед валидацией (удаляем пробелы)
        date = date.strip()
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

        # Нормализуем дату перед валидацией (удаляем пробелы)
        date = date.strip()
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
            date: Дата в формате DD.MM.YYYY. Пробелы автоматически удаляются.

        Returns:
            Optional[str]: Сообщение об ошибке или None, если дата валидна.
        """
        # Нормализуем дату: удаляем пробелы
        date = date.strip()
        
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
        currency: str,
        result_in_rub: Optional[float] = None
    ) -> str:
        """
        Форматирует результат конвертации для отображения.

        Форматирует числа отдельно, чтобы избежать проблем с глобальной заменой
        символов в тексте. Использует русский формат: пробел как разделитель тысяч,
        запятая как десятичный разделитель.

        Args:
            amount: Исходная сумма.
            rate: Курс валюты.
            currency: Код валюты.
            result_in_rub: Готовый результат конвертации в рублях (опционально).
                          Если не указан, вычисляется как amount * rate.

        Returns:
            str: Отформатированная строка результата.
        """
        if result_in_rub is None:
            result_in_rub = amount * rate
        
        normalized_currency = currency.upper()
        currency_symbol = "$" if normalized_currency == "USD" else "€"

        # Форматируем числа отдельно, чтобы не трогать текст
        def format_number(num: float, decimals: int = 2) -> str:
            """Форматирует число в русском формате: пробел - тысячи, запятая - десятичные."""
            # Форматируем с точкой как десятичным разделителем
            formatted = f"{num:,.{decimals}f}"
            # Заменяем запятую на пробел (разделитель тысяч)
            formatted = formatted.replace(',', ' ')
            # Заменяем точку на запятую (десятичный разделитель)
            formatted = formatted.replace('.', ',')
            return formatted

        result_in_rub_str = format_number(result_in_rub, decimals=2)
        amount_str = format_number(amount, decimals=2)
        rate_str = format_number(rate, decimals=4)

        # Собираем строку, форматируя только числа, текст остаётся без изменений
        result_str = (
            f"{result_in_rub_str} руб. "
            f"({currency_symbol}{amount_str} по курсу {rate_str})"
        )

        return result_str

    @staticmethod
    def parse_amount(amount_str: str) -> Optional[float]:
        """
        Нормализует строку суммы и преобразует ее в float.

        Убирает пробелы/неразрывные пробелы и разделители тысяч (пробел/точка/апостроф),
        заменяет запятую на точку. Определяет десятичный разделитель по правилу:
        десятичный разделитель - это тот, после которого меньше 3 цифр (обычно 2 для копеек).
        Все остальные разделители считаются разделителями тысяч и удаляются.

        Примеры:
        - "1.234.567" → 1234567 (все точки - разделители тысяч)
        - "1.234.567,89" → 1234567.89 (последняя запятая - десятичный разделитель)
        - "1,234,567.89" → 1234567.89 (последняя точка - десятичный разделитель)
        - "123 456 789,14" → 123456789.14 (последняя запятая - десятичный разделитель)
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

        # Определяем, какой разделитель используется как десятичный
        # Правило: десятичный разделитель - это тот, после которого меньше 3 цифр
        # Если после разделителя 3+ цифры, это разделитель тысяч
        last_comma_pos = cleaned.rfind(',')
        last_dot_pos = cleaned.rfind('.')
        
        # Определяем позицию последнего разделителя (запятая или точка)
        if last_comma_pos > last_dot_pos:
            # Запятая - последний разделитель
            after_comma = cleaned[last_comma_pos + 1:]
            if after_comma.isdigit() and len(after_comma) < 3:
                # Запятая - десятичный разделитель, точка - разделитель тысяч
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # Запятая - разделитель тысяч, удаляем все разделители
                cleaned = cleaned.replace(',', '').replace('.', '')
        elif last_dot_pos > last_comma_pos:
            # Точка - последний разделитель
            after_dot = cleaned[last_dot_pos + 1:]
            if after_dot.isdigit() and len(after_dot) < 3:
                # Точка - десятичный разделитель, запятая - разделитель тысяч
                cleaned = cleaned.replace(',', '')
            elif after_dot.isdigit() and len(after_dot) == 3:
                # После точки ровно 3 цифры - проверяем контекст
                if last_comma_pos != -1:
                    # Есть запятая - она может быть десятичным разделителем
                    after_comma = cleaned[last_comma_pos + 1:]
                    if after_comma.isdigit() and len(after_comma) < 3:
                        # Запятая - десятичный разделитель, точка - разделитель тысяч
                        cleaned = cleaned.replace('.', '').replace(',', '.')
                    else:
                        # Оба разделителя - разделители тысяч
                        cleaned = cleaned.replace(',', '').replace('.', '')
                else:
                    # Только точка, после неё 3 цифры - это разделитель тысяч (европейский формат)
                    cleaned = cleaned.replace('.', '')
            else:
                # После точки больше 3 цифр - это десятичный разделитель
                cleaned = cleaned.replace(',', '')
        else:
            # Нет разделителей или только один тип
            if ',' in cleaned and '.' not in cleaned:
                # Только запятая - заменяем на точку (десятичный разделитель)
                cleaned = cleaned.replace(',', '.')
            elif '.' in cleaned and ',' not in cleaned:
                # Только точка - проверяем количество цифр после неё
                parts = cleaned.split('.')
                if len(parts) == 2 and len(parts[1]) == 3 and parts[1].isdigit():
                    # Точка как разделитель тысяч (например, "1.234" = 1234)
                    cleaned = parts[0] + parts[1]
                # Иначе точка остаётся как десятичный разделитель

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

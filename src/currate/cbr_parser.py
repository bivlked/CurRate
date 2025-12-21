"""
Модуль для парсинга курсов валют с сайта ЦБ РФ.

Содержит функции для получения курсов валют с сайта cbr.ru
с поддержкой retry-логики и обработки ошибок.
Использует официальный XML API ЦБ РФ для получения данных.
"""

from typing import Optional
import xml.etree.ElementTree as ET
import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class CBRParserError(Exception):
    """Базовое исключение для ошибок парсера ЦБ РФ."""

    def __init__(self, message: str, technical_details: Optional[str] = None):
        """
        Инициализирует исключение.

        Args:
            message: Сообщение об ошибке.
            technical_details: Дополнительные технические детали (опционально).
        """
        self.message = message
        self.technical_details = technical_details
        super().__init__(self.message)

    def get_user_message(self) -> str:
        """
        Возвращает понятное сообщение для пользователя.

        Returns:
            str: Понятное сообщение об ошибке.
        """
        return self.message


class CBRConnectionError(CBRParserError):
    """Ошибка соединения с сайтом ЦБ РФ."""

    def get_user_message(self) -> str:
        """Возвращает понятное сообщение для пользователя."""
        if "Timeout" in self.message or "время ожидания" in self.message:
            return "Превышено время ожидания ответа от сервера. Проверьте подключение к интернету."
        if "ConnectionError" in self.message or "соединения" in self.message:
            return "Не удалось подключиться к серверу ЦБ РФ. Проверьте подключение к интернету."
        return "Ошибка соединения с сервером. Попробуйте позже."


class CBRParseError(CBRParserError):
    """Ошибка парсинга данных с сайта ЦБ РФ."""

    def get_user_message(self) -> str:
        """Возвращает понятное сообщение для пользователя."""
        if "не найдена" in self.message:
            return "Курс валюты не найден для указанной даты."
        return "Ошибка при обработке данных с сервера. Попробуйте другую дату."


def create_session_with_retry() -> requests.Session:
    """
    Создает сессию requests с настроенной retry-логикой.

    Returns:
        requests.Session: Сессия с автоматическими повторами при ошибках.
    """
    session = requests.Session()

    # Настройка retry-стратегии
    retry_strategy = Retry(
        total=3,  # Максимум 3 попытки
        backoff_factor=1,  # Экспоненциальная задержка: 1, 2, 4 секунды
        status_forcelist=[429, 500, 502, 503, 504],  # Коды для повтора
        allowed_methods=["GET"]  # Повторять только GET запросы
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


# Глобальная сессия для переиспользования соединений
_session: Optional[requests.Session] = None
_session_lock = threading.Lock()  # Блокировка для потокобезопасной инициализации


def get_session() -> requests.Session:
    """
    Получает глобальную HTTP сессию с ленивой инициализацией.

    Сессия создается один раз при первом вызове и переиспользуется
    для всех последующих запросов, что позволяет использовать
    HTTP keep-alive и connection pooling.

    Потокобезопасный метод: использует блокировку для предотвращения
    race condition при инициализации сессии в нескольких потоках.

    Returns:
        requests.Session: Сессия с настроенной retry-логикой.
    """
    global _session
    if _session is None:
        with _session_lock:
            # Двойная проверка для избежания повторной инициализации
            if _session is None:
                _session = create_session_with_retry()
    return _session


def reset_session() -> None:
    """
    Сбрасывает глобальную HTTP сессию.

    Полезно для тестирования или при необходимости принудительного
    пересоздания сессии с новыми параметрами.

    Потокобезопасный метод.
    """
    global _session
    with _session_lock:
        if _session is not None:
            _session.close()
            _session = None


def _convert_date_format(date_str: str) -> str:
    """
    Конвертирует дату из формата DD.MM.YYYY в DD/MM/YYYY для XML API.

    Args:
        date_str: Дата в формате DD.MM.YYYY

    Returns:
        str: Дата в формате DD/MM/YYYY
    """
    return date_str.replace('.', '/')


def get_currency_rate(currency: str, date: str, timeout: int = 10) -> float:
    """
    Получает курс валюты с сайта ЦБ РФ на указанную дату.

    Использует официальный XML API ЦБ РФ для получения данных.
    Курс рассчитывается за 1 единицу валюты с учетом номинала.
    Например, если в XML указан курс 100 HUF = 28.5 RUB,
    то функция вернет 0.285 (курс за 1 HUF).

    Args:
        currency: Код валюты (USD, EUR). Пробелы автоматически удаляются.
        date: Дата в формате DD.MM.YYYY. Пробелы автоматически удаляются.
        timeout: Таймаут запроса в секундах (по умолчанию 10).

    Returns:
        float: Курс валюты за 1 единицу.

    Raises:
        CBRConnectionError: При ошибке соединения с сайтом ЦБ РФ.
        CBRParseError: При ошибке парсинга данных или если валюта не найдена.
    """
    # Нормализуем входные данные: удаляем пробелы
    currency = currency.strip().upper()
    date = date.strip()
    
    # Конвертируем формат даты для XML API (DD.MM.YYYY -> DD/MM/YYYY)
    api_date = _convert_date_format(date)
    url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={api_date}"

    try:
        # Получаем глобальную сессию для переиспользования соединений
        session = get_session()

        # Выполняем запрос с таймаутом
        response = session.get(url, timeout=timeout)
        response.raise_for_status()

        # Парсим XML
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            raise CBRParseError(f"Ошибка парсинга XML ответа от ЦБ РФ: {e}") from e

        # Проверяем корневой элемент
        if root.tag != 'ValCurs':
            raise CBRParseError(
                f"Неожиданная структура XML: ожидался элемент ValCurs, получен {root.tag}"
            )

        # Ищем нужную валюту (currency уже нормализован выше)
        for valute in root.findall('Valute'):
            char_code_elem = valute.find('CharCode')
            if char_code_elem is None or char_code_elem.text is None:
                continue

            if char_code_elem.text.strip() == currency:
                try:
                    # Извлекаем номинал
                    nominal_elem = valute.find('Nominal')
                    if nominal_elem is None or nominal_elem.text is None:
                        raise CBRParseError(
                            f"Элемент Nominal не найден для валюты {currency}"
                        )
                    nominal = int(nominal_elem.text.strip())

                    # Извлекаем курс (заменяем запятую на точку для конвертации в float)
                    value_elem = valute.find('Value')
                    if value_elem is None or value_elem.text is None:
                        raise CBRParseError(
                            f"Элемент Value не найден для валюты {currency}"
                        )
                    value_str = value_elem.text.strip().replace(',', '.')
                    value = float(value_str)

                    # Возвращаем курс за 1 единицу валюты
                    return value / nominal
                except ValueError as e:
                    raise CBRParseError(
                        f"Ошибка парсинга курса валюты {currency}: {e}"
                    ) from e

        # Валюта не найдена
        raise CBRParseError(f"Валюта {currency} не найдена в XML данных")

    except requests.exceptions.Timeout as exc:
        raise CBRConnectionError(
            f"Превышено время ожидания ({timeout}с) при запросе к сайту ЦБ РФ"
        ) from exc

    except requests.exceptions.ConnectionError as exc:
        raise CBRConnectionError(
            "Ошибка соединения с сайтом ЦБ РФ. Проверьте подключение к интернету"
        ) from exc

    except requests.exceptions.HTTPError as e:
        # HTTP ошибки (4xx, 5xx) - это ошибки сервера/данных, а не соединения
        # Классифицируем как ошибку парсинга, так как сервер вернул ответ, но с ошибкой
        raise CBRParseError(f"HTTP ошибка при запросе к ЦБ РФ: {e}") from e

    except Exception as e:
        # Ловим все остальные исключения
        if isinstance(e, CBRParserError):
            raise
        raise CBRParseError(f"Неожиданная ошибка при получении курса: {e}") from e

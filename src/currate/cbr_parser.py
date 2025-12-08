"""
Модуль для парсинга курсов валют с сайта ЦБ РФ.

Содержит функции для получения курсов валют с сайта cbr.ru
с поддержкой retry-логики и обработки ошибок.
"""

from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from bs4 import BeautifulSoup, Tag


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


def get_session() -> requests.Session:
    """
    Получает глобальную HTTP сессию с ленивой инициализацией.

    Сессия создается один раз при первом вызове и переиспользуется
    для всех последующих запросов, что позволяет использовать
    HTTP keep-alive и connection pooling.

    Returns:
        requests.Session: Сессия с настроенной retry-логикой.
    """
    global _session
    if _session is None:
        _session = create_session_with_retry()
    return _session


def reset_session() -> None:
    """
    Сбрасывает глобальную HTTP сессию.

    Полезно для тестирования или при необходимости принудительного
    пересоздания сессии с новыми параметрами.
    """
    global _session
    if _session is not None:
        _session.close()
        _session = None


def get_currency_rate(currency: str, date: str, timeout: int = 10) -> Optional[float]:
    """
    Получает курс валюты с сайта ЦБ РФ на указанную дату.

    Курс рассчитывается за 1 единицу валюты с учетом номинала.
    Например, если на сайте ЦБ указан курс 100 HUF = 28.5 RUB,
    то функция вернет 0.285 (курс за 1 HUF).

    Args:
        currency: Код валюты (USD, EUR).
        date: Дата в формате DD.MM.YYYY.
        timeout: Таймаут запроса в секундах (по умолчанию 10).

    Returns:
        float: Курс валюты за 1 единицу или None при ошибке.

    Raises:
        CBRConnectionError: При ошибке соединения.
        CBRParseError: При ошибке парсинга данных.
    """
    url = f"https://cbr.ru/currency_base/daily/?UniDbQuery.Posted=True&UniDbQuery.To={date}"

    try:
        # Получаем глобальную сессию для переиспользования соединений
        session = get_session()

        # Выполняем запрос с таймаутом
        response = session.get(url, timeout=timeout)
        response.raise_for_status()

        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='data')

        if not table or not isinstance(table, Tag):
            raise CBRParseError(f"Таблица с курсами не найдена на странице для даты {date}")

        # Ищем нужную валюту
        for row in table.find_all('tr')[1:]:  # Пропускаем заголовок
            cols = row.find_all('td')
            if len(cols) < 5:
                continue

            currency_code = cols[1].text.strip()
            if currency_code == currency:
                try:
                    # Извлекаем номинал (столбец 3, индекс 2)
                    nominal_str = cols[2].text.strip()
                    nominal = int(nominal_str)

                    # Извлекаем курс (столбец 5, индекс 4)
                    rate_str = cols[4].text.strip().replace(',', '.')
                    rate = float(rate_str)

                    # Возвращаем курс за 1 единицу валюты
                    return rate / nominal
                except (ValueError, IndexError) as e:
                    raise CBRParseError(f"Ошибка парсинга курса валюты {currency}: {e}") from e

        # Валюта не найдена
        raise CBRParseError(f"Валюта {currency} не найдена в таблице курсов")

    except requests.exceptions.Timeout as exc:
        raise CBRConnectionError(
            f"Превышено время ожидания ({timeout}с) при запросе к сайту ЦБ РФ"
        ) from exc

    except requests.exceptions.ConnectionError as exc:
        raise CBRConnectionError(
            "Ошибка соединения с сайтом ЦБ РФ. Проверьте подключение к интернету"
        ) from exc

    except requests.exceptions.HTTPError as e:
        raise CBRConnectionError(f"HTTP ошибка при запросе к ЦБ РФ: {e}") from e

    except Exception as e:
        # Ловим все остальные исключения
        if isinstance(e, CBRParserError):
            raise
        raise CBRParseError(f"Неожиданная ошибка при получении курса: {e}") from e

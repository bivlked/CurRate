"""
Модуль для парсинга курсов валют с сайта ЦБ РФ.

Содержит функции для получения курсов валют с сайта cbr.ru
с поддержкой retry-логики и обработки ошибок.
"""

from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from bs4 import BeautifulSoup


class CBRParserError(Exception):
    """Базовое исключение для ошибок парсера ЦБ РФ."""
    pass


class CBRConnectionError(CBRParserError):
    """Ошибка соединения с сайтом ЦБ РФ."""
    pass


class CBRParseError(CBRParserError):
    """Ошибка парсинга данных с сайта ЦБ РФ."""
    pass


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


def get_currency_rate(currency: str, date: str, timeout: int = 10) -> Optional[float]:
    """
    Получает курс валюты с сайта ЦБ РФ на указанную дату.

    Args:
        currency: Код валюты (USD, EUR).
        date: Дата в формате DD.MM.YYYY.
        timeout: Таймаут запроса в секундах (по умолчанию 10).

    Returns:
        float: Курс валюты или None при ошибке.

    Raises:
        CBRConnectionError: При ошибке соединения.
        CBRParseError: При ошибке парсинга данных.
    """
    url = f"https://cbr.ru/currency_base/daily/?UniDbQuery.Posted=True&UniDbQuery.To={date}"

    try:
        # Создаем сессию с retry
        session = create_session_with_retry()

        # Выполняем запрос с таймаутом
        response = session.get(url, timeout=timeout)
        response.raise_for_status()

        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='data')

        if not table:
            raise CBRParseError(f"Таблица с курсами не найдена на странице для даты {date}")

        # Ищем нужную валюту
        for row in table.find_all('tr')[1:]:  # Пропускаем заголовок
            cols = row.find_all('td')
            if len(cols) < 5:
                continue

            currency_code = cols[1].text.strip()
            if currency_code == currency:
                try:
                    rate_str = cols[4].text.strip().replace(',', '.')
                    return float(rate_str)
                except (ValueError, IndexError) as e:
                    raise CBRParseError(f"Ошибка парсинга курса валюты {currency}: {e}")

        # Валюта не найдена
        raise CBRParseError(f"Валюта {currency} не найдена в таблице курсов")

    except requests.exceptions.Timeout:
        raise CBRConnectionError(f"Превышено время ожидания ({timeout}с) при запросе к сайту ЦБ РФ")

    except requests.exceptions.ConnectionError:
        raise CBRConnectionError("Ошибка соединения с сайтом ЦБ РФ. Проверьте подключение к интернету")

    except requests.exceptions.HTTPError as e:
        raise CBRConnectionError(f"HTTP ошибка при запросе к ЦБ РФ: {e}")

    except Exception as e:
        # Ловим все остальные исключения
        if isinstance(e, CBRParserError):
            raise
        raise CBRParseError(f"Неожиданная ошибка при получении курса: {e}")

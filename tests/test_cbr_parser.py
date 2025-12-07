"""Тесты для модуля парсинга курсов ЦБ РФ."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout, ConnectionError, HTTPError
from bs4 import BeautifulSoup

from src.currate.cbr_parser import (
    get_currency_rate,
    create_session_with_retry,
    CBRConnectionError,
    CBRParseError,
)


def test_create_session_with_retry():
    """Тест создания сессии с retry-логикой."""
    session = create_session_with_retry()
    
    assert session is not None
    # Проверяем, что адаптеры установлены
    assert 'http://' in session.adapters
    assert 'https://' in session.adapters


@patch('src.currate.cbr_parser.create_session_with_retry')
def test_get_currency_rate_success(mock_session):
    """Тест успешного получения курса валюты."""
    # Создаем мок ответа с HTML таблицей
    html_content = """
    <html>
        <body>
            <table class="data">
                <tr><th>Цифр. код</th><th>Букв. код</th><th>Единиц</th><th>Валюта</th><th>Курс</th></tr>
                <tr><td>840</td><td>USD</td><td>1</td><td>Доллар США</td><td>95,50</td></tr>
                <tr><td>978</td><td>EUR</td><td>1</td><td>Евро</td><td>105,20</td></tr>
            </table>
        </body>
    </html>
    """
    
    # Настраиваем мок сессии
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_session.return_value = mock_session_instance
    
    # Тестируем получение курса USD
    rate = get_currency_rate("USD", "01.12.2024")
    
    assert rate == 95.50
    mock_session_instance.get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


@patch('src.currate.cbr_parser.create_session_with_retry')
def test_get_currency_rate_eur(mock_session):
    """Тест получения курса EUR."""
    html_content = """
    <html>
        <body>
            <table class="data">
                <tr><th>Цифр. код</th><th>Букв. код</th><th>Единиц</th><th>Валюта</th><th>Курс</th></tr>
                <tr><td>978</td><td>EUR</td><td>1</td><td>Евро</td><td>105,20</td></tr>
            </table>
        </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_session.return_value = mock_session_instance
    
    rate = get_currency_rate("EUR", "01.12.2024")
    
    assert rate == 105.20


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_timeout(mock_get_session):
    """Тест обработки таймаута."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    mock_session_instance = Mock()
    mock_session_instance.get.side_effect = Timeout("Request timeout")
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRConnectionError) as exc_info:
        get_currency_rate("USD", "01.12.2024", timeout=5)
    
    assert "Превышено время ожидания" in str(exc_info.value)
    assert "5с" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_connection_error(mock_get_session):
    """Тест обработки ошибки соединения."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    mock_session_instance = Mock()
    mock_session_instance.get.side_effect = ConnectionError("Connection failed")
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRConnectionError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Ошибка соединения" in str(exc_info.value)
    assert "интернету" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_http_error(mock_get_session):
    """Тест обработки HTTP ошибки."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRConnectionError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "HTTP ошибка" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_no_table(mock_get_session):
    """Тест обработки отсутствия таблицы на странице."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    html_content = "<html><body><p>No table here</p></body></html>"
    
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Таблица с курсами не найдена" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_currency_not_found(mock_get_session):
    """Тест обработки случая, когда валюта не найдена в таблице."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    html_content = """
    <html>
        <body>
            <table class="data">
                <tr><th>Цифр. код</th><th>Букв. код</th><th>Единиц</th><th>Валюта</th><th>Курс</th></tr>
                <tr><td>978</td><td>EUR</td><td>1</td><td>Евро</td><td>105,20</td></tr>
            </table>
        </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Валюта USD не найдена" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_parse_error(mock_get_session):
    """Тест обработки ошибки парсинга курса."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    html_content = """
    <html>
        <body>
            <table class="data">
                <tr><th>Цифр. код</th><th>Букв. код</th><th>Единиц</th><th>Валюта</th><th>Курс</th></tr>
                <tr><td>840</td><td>USD</td><td>1</td><td>Доллар США</td><td>invalid_rate</td></tr>
            </table>
        </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Ошибка парсинга курса валюты" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_retry_logic(mock_get_session):
    """Тест retry-логики при временных ошибках.
    
    Примечание: Retry обрабатывается на уровне urllib3 адаптера,
    поэтому этот тест проверяет, что HTTPError правильно обрабатывается.
    """
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    # Тест проверяет, что HTTPError преобразуется в CBRConnectionError
    mock_response_error = Mock()
    mock_response_error.status_code = 503
    mock_response_error.raise_for_status.side_effect = HTTPError("503 Service Unavailable")
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response_error
    mock_get_session.return_value = mock_session_instance
    
    # Должно быть преобразовано в CBRConnectionError
    with pytest.raises(CBRConnectionError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "HTTP ошибка" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


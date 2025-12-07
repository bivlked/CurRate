"""Тесты для граничных случаев и непокрытых веток cbr_parser.py."""

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup, NavigableString
from src.currate.cbr_parser import (
    get_currency_rate,
    CBRConnectionError,
    CBRParseError,
    CBRParserError,
)


@patch('src.currate.cbr_parser.create_session_with_retry')
def test_get_currency_rate_table_is_navigable_string(mock_session):
    """Тест обработки случая, когда find возвращает NavigableString вместо Tag."""
    html_content = "<html><body>Some text</body></html>"
    
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_session.return_value = mock_session_instance
    
    # Мокаем BeautifulSoup, чтобы find вернул NavigableString
    with patch('src.currate.cbr_parser.BeautifulSoup') as mock_bs:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Создаем NavigableString вместо Tag
        soup.find = Mock(return_value=NavigableString("not a table"))
        mock_bs.return_value = soup
        
        with pytest.raises(CBRParseError) as exc_info:
            get_currency_rate("USD", "01.12.2024")
        
        assert "Таблица с курсами не найдена" in str(exc_info.value)


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_table_is_none(mock_get_session):
    """Тест обработки случая, когда таблица не найдена (None)."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    html_content = "<html><body><p>No table</p></body></html>"
    
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


@patch('src.currate.cbr_parser.create_session_with_retry')
def test_get_currency_rate_row_with_insufficient_columns(mock_session):
    """Тест обработки строки с недостаточным количеством колонок."""
    html_content = """
    <html>
        <body>
            <table class="data">
                <tr><th>Цифр. код</th><th>Букв. код</th><th>Единиц</th><th>Валюта</th><th>Курс</th></tr>
                <tr><td>840</td><td>USD</td></tr>
                <tr><td>840</td><td>USD</td><td>1</td><td>Доллар США</td><td>95,50</td></tr>
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
    
    # Должен найти USD во второй строке (первая пропущена из-за недостатка колонок)
    rate = get_currency_rate("USD", "01.12.2024")
    assert rate == 95.50


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_unexpected_exception(mock_get_session):
    """Тест обработки неожиданного исключения."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    mock_session_instance = Mock()
    mock_session_instance.get.side_effect = ValueError("Unexpected error")
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Неожиданная ошибка" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


def test_cbr_parser_error_chain():
    """Тест цепочки исключений (CBRParserError не перехватывается)."""
    error = CBRParseError("Ошибка парсинга")
    
    # Проверяем, что CBRParserError правильно обрабатывается
    with pytest.raises(CBRParseError):
        raise error


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_with_custom_timeout(mock_get_session):
    """Тест получения курса с кастомным таймаутом."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    html_content = """
    <html>
        <body>
            <table class="data">
                <tr><th>Цифр. код</th><th>Букв. код</th><th>Единиц</th><th>Валюта</th><th>Курс</th></tr>
                <tr><td>840</td><td>USD</td><td>1</td><td>Доллар США</td><td>95,50</td></tr>
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
    
    rate = get_currency_rate("USD", "01.12.2024", timeout=5)
    assert rate == 95.50
    # Проверяем, что таймаут передан в запрос
    mock_session_instance.get.assert_called_once()
    
    reset_session()  # Очистить после теста
    call_args = mock_session_instance.get.call_args
    assert call_args[1]['timeout'] == 5





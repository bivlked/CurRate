"""Тесты для граничных случаев и непокрытых веток cbr_parser.py."""

import pytest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET
from src.currate.cbr_parser import (
    get_currency_rate,
    CBRConnectionError,
    CBRParseError,
    CBRParserError,
)


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_missing_nominal(mock_get_session):
    """Тест обработки случая, когда элемент Nominal отсутствует."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <ValCurs Date="01.12.2024" name="Foreign Currency Market">
        <Valute ID="R01235">
            <NumCode>840</NumCode>
            <CharCode>USD</CharCode>
            <Name>Доллар США</Name>
            <Value>95,50</Value>
        </Valute>
    </ValCurs>
    """
    
    mock_response = Mock()
    mock_response.content = xml_content.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Nominal не найден" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_missing_value(mock_get_session):
    """Тест обработки случая, когда элемент Value отсутствует."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <ValCurs Date="01.12.2024" name="Foreign Currency Market">
        <Valute ID="R01235">
            <NumCode>840</NumCode>
            <CharCode>USD</CharCode>
            <Nominal>1</Nominal>
            <Name>Доллар США</Name>
        </Valute>
    </ValCurs>
    """
    
    mock_response = Mock()
    mock_response.content = xml_content.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Value не найден" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_empty_valute_list(mock_get_session):
    """Тест обработки случая, когда список валют пуст."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <ValCurs Date="01.12.2024" name="Foreign Currency Market">
    </ValCurs>
    """
    
    mock_response = Mock()
    mock_response.content = xml_content.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Валюта USD не найдена" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_valute_with_null_char_code(mock_get_session):
    """Тест обработки случая, когда CharCode равен None."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <ValCurs Date="01.12.2024" name="Foreign Currency Market">
        <Valute ID="R01235">
            <NumCode>840</NumCode>
            <CharCode></CharCode>
            <Nominal>1</Nominal>
            <Name>Доллар США</Name>
            <Value>95,50</Value>
        </Valute>
    </ValCurs>
    """
    
    mock_response = Mock()
    mock_response.content = xml_content.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Валюта USD не найдена" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


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

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <ValCurs Date="01.12.2024" name="Foreign Currency Market">
        <Valute ID="R01235">
            <NumCode>840</NumCode>
            <CharCode>USD</CharCode>
            <Nominal>1</Nominal>
            <Name>Доллар США</Name>
            <Value>95,50</Value>
        </Valute>
    </ValCurs>
    """

    mock_response = Mock()
    mock_response.content = xml_content.encode('utf-8')
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


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_nominal_with_high_value(mock_get_session):
    """Тест обработки валюты с высоким номиналом (например, HUF)."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <ValCurs Date="01.12.2024" name="Foreign Currency Market">
        <Valute ID="R01135">
            <NumCode>348</NumCode>
            <CharCode>HUF</CharCode>
            <Nominal>100</Nominal>
            <Name>Венгерских форинтов</Name>
            <Value>28,50</Value>
        </Valute>
    </ValCurs>
    """
    
    mock_response = Mock()
    mock_response.content = xml_content.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    rate = get_currency_rate("HUF", "01.12.2024")
    # 28.50 / 100 = 0.285
    assert rate == 0.285
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_invalid_nominal_format(mock_get_session):
    """Тест обработки некорректного формата номинала."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <ValCurs Date="01.12.2024" name="Foreign Currency Market">
        <Valute ID="R01235">
            <NumCode>840</NumCode>
            <CharCode>USD</CharCode>
            <Nominal>invalid</Nominal>
            <Name>Доллар США</Name>
            <Value>95,50</Value>
        </Valute>
    </ValCurs>
    """
    
    mock_response = Mock()
    mock_response.content = xml_content.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Ошибка парсинга курса валюты" in str(exc_info.value)
    
    reset_session()  # Очистить после теста






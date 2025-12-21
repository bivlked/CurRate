"""Тесты для модуля парсинга курсов ЦБ РФ."""

import pytest
from unittest.mock import Mock, patch
from requests.exceptions import Timeout, ConnectionError, HTTPError
import xml.etree.ElementTree as ET

from src.currate.cbr_parser import (
    get_currency_rate,
    create_session_with_retry,
    CBRConnectionError,
    CBRParseError,
    CBRParserError,
)


def test_create_session_with_retry():
    """Тест создания сессии с retry-логикой."""
    session = create_session_with_retry()
    
    assert session is not None
    # Проверяем, что адаптеры установлены
    assert 'http://' in session.adapters
    assert 'https://' in session.adapters


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_success(mock_get_session):
    """Тест успешного получения курса валюты."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    # Создаем мок ответа с XML данными
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <ValCurs Date="01.12.2024" name="Foreign Currency Market">
        <Valute ID="R01235">
            <NumCode>840</NumCode>
            <CharCode>USD</CharCode>
            <Nominal>1</Nominal>
            <Name>Доллар США</Name>
            <Value>95,50</Value>
        </Valute>
        <Valute ID="R01239">
            <NumCode>978</NumCode>
            <CharCode>EUR</CharCode>
            <Nominal>1</Nominal>
            <Name>Евро</Name>
            <Value>105,20</Value>
        </Valute>
    </ValCurs>
    """
    
    # Настраиваем мок сессии
    mock_response = Mock()
    mock_response.content = xml_content.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    # Тестируем получение курса USD
    rate = get_currency_rate("USD", "01.12.2024")
    
    assert rate == 95.50
    mock_session_instance.get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_eur(mock_get_session):
    """Тест получения курса EUR."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <ValCurs Date="01.12.2024" name="Foreign Currency Market">
        <Valute ID="R01239">
            <NumCode>978</NumCode>
            <CharCode>EUR</CharCode>
            <Nominal>1</Nominal>
            <Name>Евро</Name>
            <Value>105,20</Value>
        </Valute>
    </ValCurs>
    """
    
    mock_response = Mock()
    mock_response.content = xml_content.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    rate = get_currency_rate("EUR", "01.12.2024")
    
    assert rate == 105.20
    
    reset_session()  # Очистить после теста


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
def test_get_currency_rate_invalid_xml(mock_get_session):
    """Тест обработки некорректного XML."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    invalid_xml = "<invalid>Not a valid XML structure</invalid>"
    
    mock_response = Mock()
    mock_response.content = invalid_xml.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    # Некорректный XML обрабатывается как неправильный корневой элемент
    assert "Неожиданная структура XML" in str(exc_info.value) or "Ошибка парсинга XML" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_currency_not_found(mock_get_session):
    """Тест обработки случая, когда валюта не найдена в XML."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <ValCurs Date="01.12.2024" name="Foreign Currency Market">
        <Valute ID="R01239">
            <NumCode>978</NumCode>
            <CharCode>EUR</CharCode>
            <Nominal>1</Nominal>
            <Name>Евро</Name>
            <Value>105,20</Value>
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
def test_get_currency_rate_parse_error(mock_get_session):
    """Тест обработки ошибки парсинга курса."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <ValCurs Date="01.12.2024" name="Foreign Currency Market">
        <Valute ID="R01235">
            <NumCode>840</NumCode>
            <CharCode>USD</CharCode>
            <Nominal>1</Nominal>
            <Name>Доллар США</Name>
            <Value>invalid_rate</Value>
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


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_wrong_root_element(mock_get_session):
    """Тест обработки неправильного корневого элемента XML."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Сбросить глобальную сессию перед тестом
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <WrongRoot Date="01.12.2024">
        <Valute ID="R01235">
            <CharCode>USD</CharCode>
            <Nominal>1</Nominal>
            <Value>95,50</Value>
        </Valute>
    </WrongRoot>
    """
    
    mock_response = Mock()
    mock_response.content = xml_content.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Неожиданная структура XML" in str(exc_info.value)
    assert "ValCurs" in str(exc_info.value)
    
    reset_session()  # Очистить после теста


def test_cbr_parser_error_get_user_message():
    """Тест базового метода get_user_message() в CBRParserError."""
    error = CBRParserError("Тестовое сообщение")
    assert error.get_user_message() == "Тестовое сообщение"


def test_cbr_connection_error_get_user_message_timeout():
    """Тест get_user_message() для CBRConnectionError с таймаутом."""
    error = CBRConnectionError("Превышено время ожидания")
    message = error.get_user_message()
    assert "время ожидания" in message
    assert "интернету" in message


def test_cbr_connection_error_get_user_message_connection():
    """Тест get_user_message() для CBRConnectionError с ошибкой соединения."""
    error = CBRConnectionError("Ошибка соединения с сервером")
    message = error.get_user_message()
    assert "подключиться" in message
    assert "интернету" in message


def test_cbr_connection_error_get_user_message_generic():
    """Тест get_user_message() для CBRConnectionError с общей ошибкой."""
    # Создаем ошибку с сообщением, которое не попадает ни под одно условие
    # чтобы проверить строку 50 (return "Ошибка соединения с сервером. Попробуйте позже.")
    error = CBRConnectionError("HTTP 500 Internal Server Error")
    message = error.get_user_message()
    # Проверяем, что возвращается общее сообщение об ошибке соединения (строка 50)
    assert "Ошибка соединения с сервером" in message
    assert "позже" in message


def test_cbr_parse_error_get_user_message_not_found():
    """Тест get_user_message() для CBRParseError когда валюта не найдена."""
    error = CBRParseError("Валюта не найдена")
    message = error.get_user_message()
    assert "не найден" in message
    assert "даты" in message


def test_cbr_parse_error_get_user_message_generic():
    """Тест get_user_message() для CBRParseError с общей ошибкой."""
    error = CBRParseError("Ошибка обработки данных")
    message = error.get_user_message()
    assert "обработке данных" in message
    assert "другую дату" in message


def test_get_session_reuses_existing_session():
    """Тест, что get_session() переиспользует существующую сессию."""
    from src.currate.cbr_parser import reset_session, get_session
    reset_session()
    
    session1 = get_session()
    session2 = get_session()
    
    # Должна быть одна и та же сессия
    assert session1 is session2
    
    reset_session()


def test_reset_session_with_existing_session():
    """Тест reset_session() когда сессия существует."""
    from src.currate.cbr_parser import reset_session, get_session
    reset_session()
    
    session = get_session()
    assert session is not None
    
    reset_session()
    
    # После reset новая сессия должна быть создана
    new_session = get_session()
    assert new_session is not None
    assert new_session is not session
    
    reset_session()


def test_reset_session_without_session():
    """Тест reset_session() когда сессия не существует."""
    from src.currate.cbr_parser import reset_session
    reset_session()  # Убеждаемся, что сессии нет
    
    # Не должно быть ошибки
    reset_session()


def test_convert_date_format():
    """Тест функции _convert_date_format()."""
    from src.currate.cbr_parser import _convert_date_format
    
    assert _convert_date_format("01.12.2024") == "01/12/2024"
    assert _convert_date_format("31.12.2023") == "31/12/2023"
    assert _convert_date_format("15.01.2025") == "15/01/2025"


@patch('src.currate.cbr_parser.get_session')
def test_get_currency_rate_xml_parse_error(mock_get_session):
    """Тест обработки ET.ParseError при парсинге XML."""
    from src.currate.cbr_parser import reset_session
    reset_session()
    
    # Некорректный XML, который вызовет ParseError
    invalid_xml = b"<invalid>Not well-formed XML"
    
    mock_response = Mock()
    mock_response.content = invalid_xml
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_get_session.return_value = mock_session_instance
    
    with pytest.raises(CBRParseError) as exc_info:
        get_currency_rate("USD", "01.12.2024")
    
    assert "Ошибка парсинга XML" in str(exc_info.value)
    
    reset_session()

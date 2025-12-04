"""Тесты для проверки user-friendly сообщений об ошибках."""

import pytest
from src.currate.cbr_parser import (
    CBRParserError,
    CBRConnectionError,
    CBRParseError,
)


def test_cbr_parser_error_init():
    """Тест инициализации базового класса ошибки."""
    error = CBRParserError("Тестовая ошибка")
    assert error.message == "Тестовая ошибка"
    assert error.technical_details is None
    assert str(error) == "Тестовая ошибка"


def test_cbr_parser_error_init_with_details():
    """Тест инициализации с техническими деталями."""
    error = CBRParserError("Тестовая ошибка", technical_details="Детали")
    assert error.message == "Тестовая ошибка"
    assert error.technical_details == "Детали"


def test_cbr_parser_error_get_user_message():
    """Тест базового метода get_user_message."""
    error = CBRParserError("Тестовая ошибка")
    assert error.get_user_message() == "Тестовая ошибка"


def test_cbr_connection_error_timeout():
    """Тест user-friendly сообщения для таймаута."""
    error = CBRConnectionError("Превышено время ожидания (10с) при запросе")
    message = error.get_user_message()
    assert "время ожидания" in message
    assert "интернету" in message


def test_cbr_connection_error_connection():
    """Тест user-friendly сообщения для ошибки соединения."""
    error = CBRConnectionError("Ошибка соединения с сайтом ЦБ РФ")
    message = error.get_user_message()
    assert "подключиться" in message
    assert "интернету" in message


def test_cbr_connection_error_generic():
    """Тест user-friendly сообщения для общей ошибки соединения."""
    error = CBRConnectionError("HTTP ошибка при запросе")
    message = error.get_user_message()
    assert "соединения" in message or "сервером" in message
    assert "позже" in message


def test_cbr_parse_error_currency_not_found():
    """Тест user-friendly сообщения для не найденной валюты."""
    error = CBRParseError("Валюта USD не найдена в таблице курсов")
    message = error.get_user_message()
    assert "не найден" in message
    assert "даты" in message


def test_cbr_parse_error_generic():
    """Тест user-friendly сообщения для общей ошибки парсинга."""
    error = CBRParseError("Ошибка парсинга данных")
    message = error.get_user_message()
    assert "обработке данных" in message
    assert "другую дату" in message


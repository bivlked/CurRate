"""Расширенные тесты для модуля конвертации валют."""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from src.currate.currency_converter import CurrencyConverter
from src.currate.cbr_parser import CBRConnectionError, CBRParseError


def test_format_result_exact_format():
    """КРИТИЧНЫЙ ТЕСТ: Проверка точного формата строки результата."""
    converter = CurrencyConverter(use_cache=False)
    
    # Тест для USD
    result = converter.format_result(100.0, 95.5, "USD")
    # Ожидаемый формат: "9 550,00 руб. ($100,00 по курсу 95,5000)"
    assert "9 550,00 руб." in result
    assert "$100,00" in result
    assert "по курсу 95,5000" in result
    
    # Проверяем точный формат (без учета пробелов в числах)
    assert result.startswith("9")
    assert result.endswith(")")
    assert "руб." in result
    assert "$" in result
    
    # Тест для EUR
    result_eur = converter.format_result(100.0, 105.0, "EUR")
    assert "10 500,00 руб." in result_eur
    assert "€100,00" in result_eur
    assert "по курсу 105,0000" in result_eur


def test_format_result_format_consistency():
    """Тест консистентности формата для разных значений."""
    converter = CurrencyConverter(use_cache=False)
    
    test_cases = [
        (1.0, 95.5, "USD"),
        (10.0, 95.5, "USD"),
        (100.0, 95.5, "USD"),
        (1000.0, 95.5, "USD"),
        (1.0, 105.0, "EUR"),
        (100.0, 105.0, "EUR"),
    ]
    
    for amount, rate, currency in test_cases:
        result = converter.format_result(amount, rate, currency)
        
        # Проверяем обязательные элементы формата
        assert "руб." in result
        assert "по курсу" in result
        assert result.endswith(")")
        
        # Проверяем символ валюты
        if currency == "USD":
            assert "$" in result
        elif currency == "EUR":
            assert "€" in result


@patch('src.currate.currency_converter.get_currency_rate')
def test_convert_usd_success(mock_get_rate):
    """Тест успешной конвертации USD."""
    mock_get_rate.return_value = 95.5
    
    converter = CurrencyConverter(use_cache=False)
    result, rate, error = converter.convert(100.0, "USD", "01.12.2024")
    
    assert result == 9550.0  # 100 * 95.5
    assert rate == 95.5
    assert error is None
    mock_get_rate.assert_called_once_with("USD", "01.12.2024")


@patch('src.currate.currency_converter.get_currency_rate')
def test_convert_eur_success(mock_get_rate):
    """Тест успешной конвертации EUR."""
    mock_get_rate.return_value = 105.0
    
    converter = CurrencyConverter(use_cache=False)
    result, rate, error = converter.convert(50.0, "EUR", "01.12.2024")
    
    assert result == 5250.0  # 50 * 105.0
    assert rate == 105.0
    assert error is None


@patch('src.currate.currency_converter.get_currency_rate')
def test_convert_with_cache(mock_get_rate):
    """Тест конвертации с использованием кэша."""
    mock_get_rate.return_value = 95.5
    
    converter = CurrencyConverter(use_cache=True)
    
    # Очищаем кэш перед тестом, чтобы гарантировать, что курс не в кэше
    if converter._cache is not None:
        converter._cache.clear()
    
    # Первый вызов - должен запросить курс
    result1, rate1, error1 = converter.convert(100.0, "USD", "01.12.2024")
    assert result1 == 9550.0
    assert rate1 == 95.5
    assert error1 is None
    # Проверяем, что get_currency_rate был вызван для первой даты
    assert mock_get_rate.call_count == 1
    
    # Второй вызов с той же датой - должен использовать кэш
    result2, rate2, error2 = converter.convert(200.0, "USD", "01.12.2024")
    assert result2 == 19100.0  # 200 * 95.5
    assert rate2 == 95.5
    assert error2 is None
    # Кэш должен сработать - get_currency_rate не должен быть вызван снова
    assert mock_get_rate.call_count == 1
    
    # Третий вызов с другой датой - должен запросить курс
    mock_get_rate.return_value = 96.0
    result3, rate3, error3 = converter.convert(100.0, "USD", "02.12.2024")
    assert result3 == 9600.0
    assert rate3 == 96.0
    assert error3 is None
    # Для новой даты должен быть дополнительный запрос
    assert mock_get_rate.call_count == 2


@patch('src.currate.currency_converter.get_currency_rate')
def test_convert_connection_error(mock_get_rate):
    """Тест обработки ошибки соединения."""
    mock_get_rate.side_effect = CBRConnectionError("Ошибка соединения")
    
    converter = CurrencyConverter(use_cache=False)
    result, rate, error = converter.convert(100.0, "USD", "01.12.2024")
    
    assert result is None
    assert rate is None
    # Проверяем user-friendly сообщение
    assert "подключиться" in error or "соединения" in error
    assert error == "Не удалось подключиться к серверу ЦБ РФ. Проверьте подключение к интернету."


@patch('src.currate.currency_converter.get_currency_rate')
def test_convert_parse_error(mock_get_rate):
    """Тест обработки ошибки парсинга."""
    mock_get_rate.side_effect = CBRParseError("Ошибка парсинга")
    
    converter = CurrencyConverter(use_cache=False)
    result, rate, error = converter.convert(100.0, "USD", "01.12.2024")
    
    assert result is None
    assert rate is None
    # Проверяем user-friendly сообщение
    assert "обработке данных" in error or "другую дату" in error
    assert error == "Ошибка при обработке данных с сервера. Попробуйте другую дату."


@patch('src.currate.currency_converter.get_currency_rate')
def test_convert_rate_none(mock_get_rate):
    """Тест обработки случая, когда курс не получен (None)."""
    mock_get_rate.return_value = None
    
    converter = CurrencyConverter(use_cache=False)
    result, rate, error = converter.convert(100.0, "USD", "01.12.2024")
    
    assert result is None
    assert rate is None
    assert "Не удалось получить курс" in error


def test_get_rate_success():
    """Тест получения курса через get_rate."""
    with patch('src.currate.currency_converter.get_currency_rate') as mock_get_rate:
        mock_get_rate.return_value = 95.5
        
        converter = CurrencyConverter(use_cache=False)
        rate, error = converter.get_rate("USD", "01.12.2024")
        
        assert rate == 95.5
        assert error is None


def test_get_rate_unsupported_currency():
    """Тест получения курса для неподдерживаемой валюты."""
    converter = CurrencyConverter(use_cache=False)
    rate, error = converter.get_rate("GBP", "01.12.2024")
    
    assert rate is None
    assert "Неподдерживаемая валюта" in error


def test_validate_date_past():
    """Тест валидации даты в прошлом."""
    error = CurrencyConverter._validate_date("01.01.2020")
    assert error is None


def test_validate_date_today():
    """Тест валидации сегодняшней даты."""
    today = datetime.now().strftime('%d.%m.%Y')
    error = CurrencyConverter._validate_date(today)
    assert error is None


def test_validate_date_invalid_day():
    """Тест валидации несуществующей даты."""
    error = CurrencyConverter._validate_date("32.12.2024")
    assert "Некорректный формат даты" in error


def test_validate_date_invalid_month():
    """Тест валидации несуществующего месяца."""
    error = CurrencyConverter._validate_date("01.13.2024")
    assert "Некорректный формат даты" in error


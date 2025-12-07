"""Тесты для граничных случаев и непокрытых веток currency_converter.py."""

import pytest
from unittest.mock import patch, Mock
from src.currate.currency_converter import CurrencyConverter
from src.currate.cbr_parser import CBRParserError


def test_convert_with_validation_error_date():
    """Тест конвертации с ошибкой валидации даты."""
    converter = CurrencyConverter(use_cache=False)
    result, rate, error = converter.convert(100.0, "USD", "32.12.2024")
    
    assert result is None
    assert rate is None
    assert error is not None
    assert "формат даты" in error or "Некорректный формат" in error


def test_convert_with_validation_error_currency():
    """Тест конвертации с неподдерживаемой валютой."""
    converter = CurrencyConverter(use_cache=False)
    result, rate, error = converter.convert(100.0, "GBP", "01.12.2024")
    
    assert result is None
    assert rate is None
    assert "Неподдерживаемая валюта" in error


def test_convert_with_validation_error_amount():
    """Тест конвертации с отрицательной суммой."""
    converter = CurrencyConverter(use_cache=False)
    result, rate, error = converter.convert(-100.0, "USD", "01.12.2024")
    
    assert result is None
    assert rate is None
    assert "положительным числом" in error


@patch('src.currate.currency_converter.get_currency_rate')
def test_get_rate_with_validation_error_date(mock_get_rate):
    """Тест get_rate с ошибкой валидации даты."""
    converter = CurrencyConverter(use_cache=False)
    rate, error = converter.get_rate("USD", "32.12.2024")
    
    assert rate is None
    assert error is not None
    assert "формат даты" in error or "Некорректный формат" in error
    mock_get_rate.assert_not_called()


@patch('src.currate.currency_converter.get_currency_rate')
def test_get_rate_with_validation_error_currency(mock_get_rate):
    """Тест get_rate с неподдерживаемой валютой."""
    converter = CurrencyConverter(use_cache=False)
    rate, error = converter.get_rate("GBP", "01.12.2024")
    
    assert rate is None
    assert "Неподдерживаемая валюта" in error
    mock_get_rate.assert_not_called()


@patch('src.currate.currency_converter.get_currency_rate')
def test_get_rate_with_cache_hit(mock_get_rate):
    """Тест get_rate с попаданием в кэш."""
    mock_get_rate.return_value = 95.5
    
    converter = CurrencyConverter(use_cache=True)
    
    # Первый вызов - загружает в кэш
    rate1, error1 = converter.get_rate("USD", "01.12.2024")
    assert rate1 == 95.5
    assert error1 is None
    
    # Второй вызов - использует кэш
    mock_get_rate.reset_mock()
    rate2, error2 = converter.get_rate("USD", "01.12.2024")
    assert rate2 == 95.5
    assert error2 is None
    # get_currency_rate не должен быть вызван (кэш работает)
    assert mock_get_rate.call_count == 0


@patch('src.currate.currency_converter.get_currency_rate')
def test_get_rate_with_cache_miss(mock_get_rate):
    """Тест get_rate с промахом кэша."""
    mock_get_rate.return_value = 96.0
    
    converter = CurrencyConverter(use_cache=True)
    
    # Запрашиваем курс для новой даты
    rate, error = converter.get_rate("USD", "02.12.2024")
    
    assert rate == 96.0
    assert error is None
    mock_get_rate.assert_called_once_with("USD", "02.12.2024")


@patch('src.currate.currency_converter.get_currency_rate')
def test_convert_with_cache_disabled(mock_get_rate):
    """Тест convert с отключенным кэшем."""
    mock_get_rate.return_value = 95.5
    
    converter = CurrencyConverter(use_cache=False)
    result, rate, error = converter.convert(100.0, "USD", "01.12.2024")
    
    assert result == 9550.0
    assert rate == 95.5
    assert error is None
    mock_get_rate.assert_called_once_with("USD", "01.12.2024")


@patch('src.currate.currency_converter.get_currency_rate')
def test_convert_with_cache_enabled(mock_get_rate):
    """Тест convert с включенным кэшем."""
    mock_get_rate.return_value = 95.5
    
    converter = CurrencyConverter(use_cache=True)
    
    # Первый вызов
    result1, rate1, error1 = converter.convert(100.0, "USD", "01.12.2024")
    assert result1 == 9550.0
    assert rate1 == 95.5
    assert error1 is None
    
    # Второй вызов - должен использовать кэш
    mock_get_rate.reset_mock()
    result2, rate2, error2 = converter.convert(200.0, "USD", "01.12.2024")
    assert result2 == 19100.0
    assert rate2 == 95.5
    assert error2 is None
    # Кэш должен сработать
    assert mock_get_rate.call_count == 0




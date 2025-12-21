"""Тесты для валидации даты с пробелами."""

import pytest
from src.currate.currency_converter import CurrencyConverter


def test_validate_date_with_spaces():
    """Тест валидации даты с пробелами."""
    # Дата с пробелами должна быть валидной
    error = CurrencyConverter._validate_date(" 01.12.2024 ")
    assert error is None


def test_validate_date_without_spaces():
    """Тест валидации даты без пробелов."""
    error = CurrencyConverter._validate_date("01.12.2024")
    assert error is None


def test_convert_with_date_spaces():
    """Тест convert с датой, содержащей пробелы."""
    converter = CurrencyConverter(use_cache=False)
    
    # Мокаем get_currency_rate, чтобы не делать реальный запрос
    from unittest.mock import patch
    with patch('src.currate.currency_converter.get_currency_rate', return_value=95.5):
        result, rate, error = converter.convert(100.0, "USD", " 01.12.2024 ")
        
        assert error is None
        assert result is not None
        assert rate == 95.5


def test_get_rate_with_date_spaces():
    """Тест get_rate с датой, содержащей пробелы."""
    converter = CurrencyConverter(use_cache=False)
    
    from unittest.mock import patch
    with patch('src.currate.currency_converter.get_currency_rate', return_value=95.5):
        rate, error = converter.get_rate("USD", " 01.12.2024 ")
        
        assert error is None
        assert rate == 95.5


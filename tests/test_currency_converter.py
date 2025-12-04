"""Тесты для модуля конвертации валют."""

import pytest
from src.currate.currency_converter import CurrencyConverter


def test_validate_date_future():
    """Тест валидации даты в будущем."""
    error = CurrencyConverter._validate_date("31.12.2099")
    assert error == "Дата не может быть в будущем"


def test_validate_date_invalid_format():
    """Тест валидации неправильного формата даты."""
    error = CurrencyConverter._validate_date("2024-12-01")
    assert "Некорректный формат даты" in error


def test_validate_date_valid():
    """Тест валидации корректной даты."""
    error = CurrencyConverter._validate_date("01.12.2024")
    assert error is None


def test_format_result_usd():
    """Тест форматирования результата для USD."""
    converter = CurrencyConverter(use_cache=False)

    result = converter.format_result(100.0, 95.5, "USD")

    assert "9 550" in result  # 100 * 95.5 = 9550
    assert "$" in result
    assert "руб." in result


def test_format_result_eur():
    """Тест форматирования результата для EUR."""
    converter = CurrencyConverter(use_cache=False)

    result = converter.format_result(100.0, 105.0, "EUR")

    assert "10 500" in result  # 100 * 105 = 10500
    assert "€" in result
    assert "руб." in result


def test_unsupported_currency():
    """Тест неподдерживаемой валюты."""
    converter = CurrencyConverter(use_cache=False)

    result, error = converter.convert(100.0, "GBP", "01.12.2024")

    assert result is None
    assert "Неподдерживаемая валюта" in error


def test_negative_amount():
    """Тест отрицательной суммы."""
    converter = CurrencyConverter(use_cache=False)

    result, error = converter.convert(-100.0, "USD", "01.12.2024")

    assert result is None
    assert "положительным числом" in error


def test_zero_amount():
    """Тест нулевой суммы."""
    converter = CurrencyConverter(use_cache=False)

    result, error = converter.convert(0, "USD", "01.12.2024")

    assert result is None
    assert "положительным числом" in error

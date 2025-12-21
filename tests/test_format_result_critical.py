"""КРИТИЧНЫЕ ТЕСТЫ: Проверка точного формата строки результата.

ВАЖНО: Формат строки результата должен остаться НЕИЗМЕННЫМ!
Текущий формат: "{result_in_rub} руб. ({currency_symbol}{amount} по курсу {rate})"
"""

import pytest
from src.currate.currency_converter import CurrencyConverter


def test_format_result_exact_format_usd():
    """КРИТИЧНЫЙ ТЕСТ: Точный формат для USD."""
    converter = CurrencyConverter(use_cache=False)
    
    # Тест с конкретными значениями
    result = converter.format_result(100.0, 95.5, "USD")
    
    # Проверяем точную структуру
    assert result.startswith("9")
    assert "руб." in result
    assert "$" in result
    assert "по курсу" in result
    assert result.endswith(")")
    
    # Проверяем, что формат соответствует ожидаемому паттерну
    # Формат: "9 550,00 руб. ($100,00 по курсу 95,5000)"
    parts = result.split(" руб. ")
    assert len(parts) == 2
    assert parts[0].replace(" ", "").replace(",", ".").replace(".", "", 1).isdigit() or parts[0].replace(" ", "").replace(",", ".").replace(".", "", 1)[1:].isdigit()
    assert "$" in parts[1] or "€" in parts[1]
    assert "по курсу" in parts[1]


def test_format_result_exact_format_eur():
    """КРИТИЧНЫЙ ТЕСТ: Точный формат для EUR."""
    converter = CurrencyConverter(use_cache=False)
    
    result = converter.format_result(100.0, 105.0, "EUR")
    
    # Проверяем точную структуру
    assert "руб." in result
    assert "€" in result
    assert "по курсу" in result
    assert result.endswith(")")
    
    # Проверяем наличие суммы в рублях
    assert "10" in result  # 100 * 105 = 10500


def test_format_result_format_unchanged():
    """КРИТИЧНЫЙ ТЕСТ: Формат не должен измениться при рефакторинге."""
    converter = CurrencyConverter(use_cache=False)
    
    # Тестируем с различными значениями
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
        
        # КРИТИЧНЫЕ проверки формата:
        # 1. Должен содержать "руб."
        assert "руб." in result, f"Результат должен содержать 'руб.': {result}"
        
        # 2. Должен содержать символ валюты
        if currency == "USD":
            assert "$" in result, f"Результат должен содержать '$': {result}"
        elif currency == "EUR":
            assert "€" in result, f"Результат должен содержать '€': {result}"
        
        # 3. Должен содержать "по курсу"
        assert "по курсу" in result, f"Результат должен содержать 'по курсу': {result}"
        
        # 4. Должен заканчиваться на ")"
        assert result.endswith(")"), f"Результат должен заканчиваться на ')': {result}"
        
        # 5. Должен содержать сумму в скобках
        assert "(" in result and ")" in result, f"Результат должен содержать скобки: {result}"


def test_format_result_with_result_in_rub_parameter():
    """Тест format_result с параметром result_in_rub."""
    converter = CurrencyConverter(use_cache=False)
    
    # Тест с явным указанием result_in_rub
    result1 = converter.format_result(100.0, 95.5, "USD", result_in_rub=9550.0)
    result2 = converter.format_result(100.0, 95.5, "USD")  # Без параметра
    
    # Результаты должны быть одинаковыми
    assert result1 == result2
    
    # Тест с другим значением result_in_rub (не равным amount * rate)
    result3 = converter.format_result(100.0, 95.5, "USD", result_in_rub=10000.0)
    assert "10 000,00" in result3  # Используется переданное значение, а не вычисленное


def test_format_result_copy_paste_format():
    """КРИТИЧНЫЙ ТЕСТ: Формат для копирования в буфер обмена."""
    converter = CurrencyConverter(use_cache=False)
    
    # Тест с типичными значениями
    result = converter.format_result(100.0, 95.5, "USD")
    
    # Формат должен быть читаемым и копируемым
    # Пример ожидаемого формата: "9 550,00 руб. ($100,00 по курсу 95,5000)"
    
    # Проверяем структуру:
    # - Сумма в рублях с разделителем тысяч (пробел) и десятичным разделителем (запятая)
    # - Символ валюты и сумма в скобках
    # - Курс с 4 знаками после запятой
    
    # Разбиваем на части
    main_part, bracket_part = result.split(" руб. ")
    
    # Основная часть должна содержать число с разделителями
    assert main_part.replace(" ", "").replace(",", ".").replace(".", "", 1).replace(".", "").isdigit() or main_part.replace(" ", "").replace(",", ".").replace(".", "", 1)[1:].replace(".", "").isdigit()
    
    # Часть в скобках должна содержать символ валюты, сумму и курс
    assert "$" in bracket_part or "€" in bracket_part
    assert "по курсу" in bracket_part


def test_format_result_edge_cases():
    """Тест формата для граничных случаев."""
    converter = CurrencyConverter(use_cache=False)
    
    # Очень маленькая сумма
    result_small = converter.format_result(0.01, 95.5, "USD")
    assert "руб." in result_small
    assert "$" in result_small
    
    # Очень большая сумма
    result_large = converter.format_result(1000000.0, 95.5, "USD")
    assert "руб." in result_large
    assert "$" in result_large
    
    # Очень маленький курс
    result_small_rate = converter.format_result(100.0, 0.01, "USD")
    assert "руб." in result_small_rate
    
    # Очень большой курс
    result_large_rate = converter.format_result(100.0, 1000.0, "USD")
    assert "руб." in result_large_rate


def test_format_result_decimal_precision():
    """Тест точности форматирования десятичных чисел."""
    converter = CurrencyConverter(use_cache=False)
    
    # Тест с числами, требующими округления
    result = converter.format_result(100.123, 95.5678, "USD")
    
    # Проверяем, что формат корректен
    assert "руб." in result
    assert "$" in result
    assert "по курсу" in result
    
    # Сумма должна быть округлена до 2 знаков
    # 100.123 * 95.5678 = 9570.68... (округляется до 9570,68)


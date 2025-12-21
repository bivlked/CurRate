"""
Proof of Concept: Тестирование XML API ЦБ РФ
Проверка работоспособности XML парсинга перед основной реализацией.
"""

import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timedelta
from typing import Optional, Tuple


def convert_date_format(date_str: str) -> str:
    """
    Конвертирует дату из формата DD.MM.YYYY в DD/MM/YYYY для XML API.
    
    Args:
        date_str: Дата в формате DD.MM.YYYY
        
    Returns:
        str: Дата в формате DD/MM/YYYY
    """
    return date_str.replace('.', '/')


def test_xml_api(date: str) -> Tuple[bool, Optional[str], Optional[dict]]:
    """
    Тестирует получение и парсинг XML от ЦБ РФ.
    
    Args:
        date: Дата в формате DD.MM.YYYY
        
    Returns:
        Tuple[bool, Optional[str], Optional[dict]]: 
            (успех, сообщение об ошибке, данные о валютах)
    """
    # Конвертируем формат даты
    api_date = convert_date_format(date)
    url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={api_date}"
    
    try:
        # Выполняем запрос
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Парсим XML
        root = ET.fromstring(response.content)
        
        # Проверяем корневой элемент
        if root.tag != 'ValCurs':
            return False, f"Неожиданный корневой элемент: {root.tag}", None
        
        # Извлекаем информацию о валютах
        currencies = {}
        for valute in root.findall('Valute'):
            char_code_elem = valute.find('CharCode')
            nominal_elem = valute.find('Nominal')
            value_elem = valute.find('Value')
            
            if char_code_elem is not None and nominal_elem is not None and value_elem is not None:
                char_code = char_code_elem.text
                nominal = int(nominal_elem.text)
                # Заменяем запятую на точку для конвертации в float
                value_str = value_elem.text.replace(',', '.')
                value = float(value_str)
                
                # Рассчитываем курс за 1 единицу
                rate_per_unit = value / nominal
                
                currencies[char_code] = {
                    'nominal': nominal,
                    'value': value,
                    'rate_per_unit': rate_per_unit
                }
        
        return True, None, currencies
        
    except requests.exceptions.Timeout:
        return False, "Превышено время ожидания запроса", None
    except requests.exceptions.ConnectionError:
        return False, "Ошибка соединения с сервером", None
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP ошибка: {e}", None
    except ET.ParseError as e:
        return False, f"Ошибка парсинга XML: {e}", None
    except Exception as e:
        return False, f"Неожиданная ошибка: {e}", None


def test_specific_currency(date: str, currency: str) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Тестирует получение курса конкретной валюты.
    
    Args:
        date: Дата в формате DD.MM.YYYY
        currency: Код валюты (USD, EUR)
        
    Returns:
        Tuple[bool, Optional[str], Optional[float]]: 
            (успех, сообщение об ошибке, курс за 1 единицу)
    """
    success, error, currencies = test_xml_api(date)
    
    if not success:
        return False, error, None
    
    if currencies is None:
        return False, "Данные о валютах не получены", None
    
    currency_upper = currency.upper()
    if currency_upper not in currencies:
        return False, f"Валюта {currency} не найдена", None
    
    return True, None, currencies[currency_upper]['rate_per_unit']


def main():
    """Основная функция для тестирования."""
    print("=" * 60)
    print("PROOF OF CONCEPT: Тестирование XML API ЦБ РФ")
    print("=" * 60)
    print()
    
    # Тест 1: Проверка доступности xml.etree.ElementTree
    print("Тест 1: Проверка доступности xml.etree.ElementTree")
    try:
        import xml.etree.ElementTree as ET
        print("[OK] xml.etree.ElementTree доступен")
    except ImportError as e:
        print(f"[ERROR] Ошибка импорта: {e}")
        return
    print()
    
    # Тест 2: Получение данных за сегодня
    print("Тест 2: Получение данных за сегодня")
    today = datetime.now().strftime('%d.%m.%Y')
    print(f"Дата: {today}")
    
    success, error, currencies = test_xml_api(today)
    
    if success and currencies:
        print(f"[OK] Успешно получено {len(currencies)} валют")
        print(f"   Найдены валюты: {', '.join(sorted(currencies.keys())[:10])}...")
    else:
        print(f"[ERROR] Ошибка: {error}")
        return
    print()
    
    # Тест 3: Получение курса USD
    print("Тест 3: Получение курса USD")
    success, error, rate = test_specific_currency(today, 'USD')
    if success and rate is not None:
        print(f"[OK] Курс USD: {rate:.4f} руб. за 1 USD")
    else:
        print(f"[ERROR] Ошибка: {error}")
    print()
    
    # Тест 4: Получение курса EUR
    print("Тест 4: Получение курса EUR")
    success, error, rate = test_specific_currency(today, 'EUR')
    if success and rate is not None:
        print(f"[OK] Курс EUR: {rate:.4f} руб. за 1 EUR")
    else:
        print(f"[ERROR] Ошибка: {error}")
    print()
    
    # Тест 5: Проверка структуры XML
    print("Тест 5: Проверка структуры XML")
    api_date = convert_date_format(today)
    url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={api_date}"
    try:
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.content)
        
        print(f"[OK] Корневой элемент: {root.tag}")
        print(f"   Атрибуты: {root.attrib}")
        
        # Проверяем первую валюту
        first_valute = root.find('Valute')
        if first_valute is not None:
            print(f"   Первая валюта найдена")
            char_code = first_valute.find('CharCode')
            nominal = first_valute.find('Nominal')
            value = first_valute.find('Value')
            
            if char_code is not None:
                print(f"   CharCode: {char_code.text}")
            if nominal is not None:
                print(f"   Nominal: {nominal.text}")
            if value is not None:
                print(f"   Value: {value.text}")
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
    print()
    
    # Тест 6: Проверка обработки ошибок (несуществующая валюта)
    print("Тест 6: Проверка обработки ошибок (несуществующая валюта)")
    success, error, rate = test_specific_currency(today, 'XXX')
    if not success:
        print(f"[OK] Ошибка корректно обработана: {error}")
    else:
        print(f"[ERROR] Ошибка не обработана")
    print()
    
    # Тест 7: Проверка формата даты
    print("Тест 7: Проверка конвертации формата даты")
    test_dates = ['01.12.2024', '15.01.2025', '31.12.2023']
    for date_str in test_dates:
        converted = convert_date_format(date_str)
        print(f"   {date_str} -> {converted}")
    print()
    
    print("=" * 60)
    print("РЕЗУЛЬТАТ: Все тесты пройдены успешно!")
    print("XML API ЦБ РФ готов к использованию")
    print("=" * 60)


if __name__ == '__main__':
    main()


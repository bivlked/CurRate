"""Тесты для модуля кэширования."""

import pytest
from src.currate.cache import CurrencyCache


def test_cache_set_and_get():
    """Тест сохранения и получения значения из кэша."""
    cache = CurrencyCache(max_size=10, ttl_hours=24)

    cache.set("USD", "01.12.2024", 95.5)
    rate = cache.get("USD", "01.12.2024")

    assert rate == 95.5


def test_cache_miss():
    """Тест отсутствующего значения в кэше."""
    cache = CurrencyCache(max_size=10, ttl_hours=24)

    rate = cache.get("EUR", "01.12.2024")

    assert rate is None


def test_cache_size():
    """Тест подсчета размера кэша."""
    cache = CurrencyCache(max_size=10, ttl_hours=24)

    cache.set("USD", "01.12.2024", 95.5)
    cache.set("EUR", "01.12.2024", 105.0)

    assert cache.size() == 2


def test_cache_clear():
    """Тест очистки кэша."""
    cache = CurrencyCache(max_size=10, ttl_hours=24)

    cache.set("USD", "01.12.2024", 95.5)
    cache.set("EUR", "01.12.2024", 105.0)
    cache.clear()

    assert cache.size() == 0
    assert cache.get("USD", "01.12.2024") is None


def test_cache_eviction():
    """Тест вытеснения старых записей при переполнении."""
    cache = CurrencyCache(max_size=4, ttl_hours=24)

    # Заполняем кэш полностью
    cache.set("USD", "01.12.2024", 95.0)
    cache.set("EUR", "01.12.2024", 105.0)
    cache.set("USD", "02.12.2024", 96.0)
    cache.set("EUR", "02.12.2024", 106.0)

    assert cache.size() == 4

    # Добавляем еще одну запись - должно сработать вытеснение
    cache.set("USD", "03.12.2024", 97.0)

    # Размер кэша должен остаться 4 (одна запись вытеснена)
    assert cache.size() == 4
    # Проверяем, что самая старая запись вытеснена
    assert cache.get("USD", "01.12.2024") is None  # Первая запись должна быть вытеснена
    assert cache.get("USD", "03.12.2024") == 97.0  # Новая запись должна быть в кэше


def test_get_cache_returns_global_instance():
    """Тест, что get_cache() возвращает глобальный экземпляр кэша."""
    from src.currate.cache import get_cache
    
    cache1 = get_cache()
    cache2 = get_cache()
    
    # Должен быть один и тот же экземпляр
    assert cache1 is cache2
    
    # Изменения в одном должны отражаться в другом
    cache1.set("USD", "01.12.2024", 95.5)
    assert cache2.get("USD", "01.12.2024") == 95.5

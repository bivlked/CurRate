"""Тесты для граничных случаев кэша."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from src.currate.cache import CurrencyCache


def test_cache_cleanup_expired_with_no_expired():
    """Тест cleanup_expired когда нет устаревших записей."""
    cache = CurrencyCache(max_size=10, ttl_hours=24)
    
    cache.set("USD", "01.12.2024", 95.5)
    cache.set("EUR", "01.12.2024", 105.0)
    
    removed_count = cache.cleanup_expired()
    
    assert removed_count == 0
    assert cache.size() == 2


def test_cache_cleanup_expired_with_all_expired():
    """Тест cleanup_expired когда все записи устарели."""
    cache = CurrencyCache(max_size=10, ttl_hours=1)
    
    cache.set("USD", "01.12.2024", 95.5)
    cache.set("EUR", "01.12.2024", 105.0)
    
    # Симулируем истечение TTL
    with patch('src.currate.cache.datetime') as mock_datetime:
        future_time = datetime.now() + timedelta(hours=2)
        mock_datetime.now.return_value = future_time
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw) if args or kw else future_time
        
        removed_count = cache.cleanup_expired()
        
        assert removed_count == 2
        assert cache.size() == 0


def test_cache_set_cleanup_on_overflow():
    """Тест, что _cleanup_expired_unlocked вызывается при переполнении."""
    cache = CurrencyCache(max_size=3, ttl_hours=24)
    
    # Заполняем кэш до переполнения
    cache.set("USD", "01.12.2024", 95.0)
    cache.set("EUR", "01.12.2024", 105.0)
    cache.set("USD", "02.12.2024", 96.0)
    
    # При добавлении следующей записи должен вызваться _cleanup_expired_unlocked
    # (даже если нет устаревших записей)
    with patch.object(cache, '_cleanup_expired_unlocked', return_value=0) as mock_cleanup:
        cache.set("EUR", "02.12.2024", 106.0)
        # _cleanup_expired_unlocked должен быть вызван при переполнении
        mock_cleanup.assert_called_once()


def test_cache_get_with_expired_entry():
    """Тест get с устаревшей записью."""
    cache = CurrencyCache(max_size=10, ttl_hours=1)
    
    cache.set("USD", "01.12.2024", 95.5)
    
    # Симулируем истечение TTL
    with patch('src.currate.cache.datetime') as mock_datetime:
        future_time = datetime.now() + timedelta(hours=2)
        mock_datetime.now.return_value = future_time
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw) if args or kw else future_time
        
        rate = cache.get("USD", "01.12.2024")
        
        assert rate is None
        assert cache.size() == 0  # Устаревшая запись удалена


def test_cache_lru_behavior_on_get():
    """Тест LRU поведения при get (запись перемещается в конец)."""
    cache = CurrencyCache(max_size=3, ttl_hours=24)
    
    # Заполняем кэш
    cache.set("USD", "01.12.2024", 95.0)
    cache.set("EUR", "01.12.2024", 105.0)
    cache.set("USD", "02.12.2024", 96.0)
    
    # Получаем первую запись (она должна переместиться в конец)
    rate = cache.get("USD", "01.12.2024")
    assert rate == 95.0
    
    # Добавляем новую запись - должна быть вытеснена вторая (EUR, 01.12.2024)
    # так как USD, 01.12.2024 теперь в конце (недавно использована)
    cache.set("EUR", "02.12.2024", 106.0)
    
    # Проверяем, что USD, 01.12.2024 всё ещё в кэше (была перемещена в конец)
    assert cache.get("USD", "01.12.2024") == 95.0
    # EUR, 01.12.2024 должна быть вытеснена
    assert cache.get("EUR", "01.12.2024") is None


def test_cache_set_update_existing():
    """Тест обновления существующей записи через set."""
    cache = CurrencyCache(max_size=10, ttl_hours=24)
    
    cache.set("USD", "01.12.2024", 95.5)
    assert cache.get("USD", "01.12.2024") == 95.5
    assert cache.size() == 1
    
    # Обновляем значение
    cache.set("USD", "01.12.2024", 96.0)
    
    assert cache.get("USD", "01.12.2024") == 96.0
    assert cache.size() == 1  # Размер не должен увеличиться


def test_cache_clear_empty():
    """Тест очистки пустого кэша."""
    cache = CurrencyCache(max_size=10, ttl_hours=24)
    
    cache.clear()
    
    assert cache.size() == 0


def test_cache_size_empty():
    """Тест размера пустого кэша."""
    cache = CurrencyCache(max_size=10, ttl_hours=24)
    
    assert cache.size() == 0


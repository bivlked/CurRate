"""Тесты для потокобезопасности кэша."""

import pytest
import threading
import time
from src.currate.cache import CurrencyCache


def test_cache_thread_safety_concurrent_get_set():
    """Тест потокобезопасности при одновременных get и set."""
    cache = CurrencyCache(max_size=100, ttl_hours=24)
    results = []
    errors = []

    def worker(currency: str, date: str, rate: float, operation: str):
        """Рабочая функция для потока."""
        try:
            if operation == "set":
                cache.set(currency, date, rate)
            elif operation == "get":
                result = cache.get(currency, date)
                results.append(result)
        except Exception as e:
            errors.append(e)

    # Создаём несколько потоков для записи
    threads = []
    for i in range(10):
        t = threading.Thread(
            target=worker,
            args=(f"USD", f"0{i+1}.12.2024", 95.5 + i, "set")
        )
        threads.append(t)

    # Создаём несколько потоков для чтения
    for i in range(10):
        t = threading.Thread(
            target=worker,
            args=(f"USD", f"0{i+1}.12.2024", 0, "get")
        )
        threads.append(t)

    # Запускаем все потоки
    for t in threads:
        t.start()

    # Ждём завершения всех потоков
    for t in threads:
        t.join()

    # Проверяем, что не было ошибок
    assert len(errors) == 0, f"Обнаружены ошибки в потоках: {errors}"

    # Проверяем, что кэш в корректном состоянии
    assert cache.size() == 10


def test_cache_thread_safety_concurrent_cleanup():
    """Тест потокобезопасности при одновременной очистке."""
    cache = CurrencyCache(max_size=100, ttl_hours=24)
    
    # Заполняем кэш
    for i in range(20):
        cache.set(f"USD", f"{i:02d}.12.2024", 95.5 + i)

    errors = []

    def cleanup_worker():
        """Рабочая функция для очистки."""
        try:
            cache.cleanup_expired()
        except Exception as e:
            errors.append(e)

    # Создаём несколько потоков для очистки
    threads = []
    for _ in range(5):
        t = threading.Thread(target=cleanup_worker)
        threads.append(t)

    # Запускаем все потоки
    for t in threads:
        t.start()

    # Ждём завершения
    for t in threads:
        t.join()

    # Проверяем, что не было ошибок
    assert len(errors) == 0, f"Обнаружены ошибки при очистке: {errors}"


def test_cache_thread_safety_size():
    """Тест потокобезопасности метода size()."""
    cache = CurrencyCache(max_size=100, ttl_hours=24)
    sizes = []

    def size_worker():
        """Рабочая функция для получения размера."""
        try:
            size = cache.size()
            sizes.append(size)
        except Exception as e:
            sizes.append(-1)

    # Заполняем кэш
    for i in range(10):
        cache.set(f"USD", f"{i:02d}.12.2024", 95.5 + i)

    # Создаём несколько потоков для получения размера
    threads = []
    for _ in range(20):
        t = threading.Thread(target=size_worker)
        threads.append(t)

    # Запускаем все потоки
    for t in threads:
        t.start()

    # Ждём завершения
    for t in threads:
        t.join()

    # Все размеры должны быть одинаковыми (10)
    assert all(s == 10 for s in sizes), f"Размеры не совпадают: {sizes}"


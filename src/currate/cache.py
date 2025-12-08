"""
Модуль кэширования курсов валют.

Обеспечивает кэширование загруженных курсов валют для уменьшения
количества запросов к сайту ЦБ РФ.
"""

from typing import Optional, Tuple
from collections import OrderedDict
from datetime import datetime, timedelta


class CurrencyCache:
    """
    Кэш для хранения курсов валют.

    Хранит курсы валют в памяти с учетом даты и валюты.
    Кэш автоматически очищается при достижении лимита записей.
    """

    def __init__(self, max_size: int = 100, ttl_hours: int = 24):
        """
        Инициализирует кэш.

        Args:
            max_size: Максимальное количество записей в кэше (по умолчанию 100).
            ttl_hours: Время жизни записи в часах (по умолчанию 24).
        """
        self._cache: OrderedDict[Tuple[str, str], Tuple[float, datetime]] = OrderedDict()
        self._max_size = max_size
        self._ttl = timedelta(hours=ttl_hours)

    def get(self, currency: str, date: str) -> Optional[float]:
        """
        Получает курс валюты из кэша.

        Использует LRU (Least Recently Used) стратегию:
        при доступе запись перемещается в конец (самая недавно использованная).

        Args:
            currency: Код валюты (USD, EUR).
            date: Дата в формате DD.MM.YYYY.

        Returns:
            float: Курс валюты или None, если запись не найдена или устарела.
        """
        key = (currency, date)

        if key not in self._cache:
            return None

        # Извлекаем запись (удаляем из текущей позиции)
        rate, cached_at = self._cache.pop(key)

        # Проверяем, не устарела ли запись (ленивая проверка TTL)
        if datetime.now() - cached_at > self._ttl:
            return None

        # Перемещаем в конец (самая недавно использованная)
        self._cache[key] = (rate, cached_at)
        return rate

    def set(self, currency: str, date: str, rate: float) -> None:
        """
        Сохраняет курс валюты в кэш.

        Использует LRU (Least Recently Used) стратегию:
        при переполнении удаляется самая старая запись (первая в OrderedDict).

        Args:
            currency: Код валюты (USD, EUR).
            date: Дата в формате DD.MM.YYYY.
            rate: Курс валюты.
        """
        key = (currency, date)

        # Если ключ уже есть - обновляем и перемещаем в конец
        if key in self._cache:
            self._cache.pop(key)
        elif len(self._cache) >= self._max_size:
            # При переполнении сначала очищаем устаревшие записи (ленивая очистка)
            # Это оптимизирует производительность: очистка только при необходимости
            self.cleanup_expired()
            # Если после очистки все еще переполнен, удаляем самый старый элемент
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)

        # Добавляем в конец (самая недавно использованная)
        self._cache[key] = (rate, datetime.now())

    def clear(self) -> None:
        """Очищает весь кэш."""
        self._cache.clear()

    def size(self) -> int:
        """
        Возвращает текущий размер кэша.

        Returns:
            int: Количество записей в кэше.
        """
        return len(self._cache)

    def cleanup_expired(self) -> int:
        """
        Удаляет устаревшие записи из кэша.

        Returns:
            int: Количество удаленных записей.
        """
        expired_keys = []
        now = datetime.now()

        for key, (_, cached_at) in self._cache.items():
            if now - cached_at > self._ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)


# Глобальный экземпляр кэша
_global_cache = CurrencyCache()


def get_cache() -> CurrencyCache:
    """
    Возвращает глобальный экземпляр кэша.

    Returns:
        CurrencyCache: Глобальный кэш валют.
    """
    return _global_cache

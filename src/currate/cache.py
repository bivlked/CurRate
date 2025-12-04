"""
Модуль кэширования курсов валют.

Обеспечивает кэширование загруженных курсов валют для уменьшения
количества запросов к сайту ЦБ РФ.
"""

from typing import Dict, Optional, Tuple
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
        self._cache: Dict[Tuple[str, str], Tuple[float, datetime]] = {}
        self._max_size = max_size
        self._ttl = timedelta(hours=ttl_hours)

    def get(self, currency: str, date: str) -> Optional[float]:
        """
        Получает курс валюты из кэша.

        Args:
            currency: Код валюты (USD, EUR).
            date: Дата в формате DD.MM.YYYY.

        Returns:
            float: Курс валюты или None, если запись не найдена или устарела.
        """
        key = (currency, date)

        if key not in self._cache:
            return None

        rate, cached_at = self._cache[key]

        # Проверяем, не устарела ли запись
        if datetime.now() - cached_at > self._ttl:
            del self._cache[key]
            return None

        return rate

    def set(self, currency: str, date: str, rate: float) -> None:
        """
        Сохраняет курс валюты в кэш.

        Args:
            currency: Код валюты (USD, EUR).
            date: Дата в формате DD.MM.YYYY.
            rate: Курс валюты.
        """
        # Если кэш переполнен, удаляем самые старые записи
        if len(self._cache) >= self._max_size:
            self._evict_oldest()

        key = (currency, date)
        self._cache[key] = (rate, datetime.now())

    def clear(self) -> None:
        """Очищает весь кэш."""
        self._cache.clear()

    def _evict_oldest(self) -> None:
        """Удаляет 25% самых старых записей из кэша."""
        if not self._cache:
            return

        # Сортируем по времени добавления
        sorted_items = sorted(self._cache.items(), key=lambda x: x[1][1])

        # Удаляем 25% самых старых
        items_to_remove = max(1, len(sorted_items) // 4)
        for i in range(items_to_remove):
            key = sorted_items[i][0]
            del self._cache[key]

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

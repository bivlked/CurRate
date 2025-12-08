"""
Утилиты для окружения тестов.

Главная задача файла — не дать pytest упасть, если pytest-cov не установлен,
но в pytest.ini присутствуют покрывающие опции (--cov и др.). Мы регистрируем
заглушки, чтобы тесты могли запускаться «из коробки», даже без дополнений.
"""

import importlib.util
import warnings


def _cov_plugin_available() -> bool:
    """Есть ли установленный pytest-cov (независимо от автозагрузки)."""
    return importlib.util.find_spec("pytest_cov") is not None


def pytest_addoption(parser) -> None:
    """
    Регистрирует заглушки для опций покрытия, если pytest-cov недоступен.

    Это позволяет запускать тесты даже в окружениях без dev-зависимостей.
    """
    if _cov_plugin_available():
        return

    cov_group = parser.getgroup(
        "cov",
        "coverage reporting (no-op без pytest-cov)"
    )
    cov_group.addoption("--cov", action="append", default=[])
    cov_group.addoption("--cov-report", action="append", default=[])
    cov_group.addoption("--cov-fail-under", action="store", type=float, default=None)


def pytest_configure(config) -> None:
    """Выводим предупреждение, если pytest-cov не найден."""
    if config.pluginmanager.hasplugin("cov") or _cov_plugin_available():
        return
    warnings.warn(
        "pytest-cov не установлен: опции покрытия из pytest.ini будут пропущены",
        RuntimeWarning,
    )

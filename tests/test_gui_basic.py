"""Базовые тесты для GUI модуля (без полного запуска Tkinter)."""

import pytest


def test_gui_import():
    """Тест импорта GUI модуля."""
    from src.currate import gui
    assert hasattr(gui, 'CurrencyConverterApp')


def test_gui_class_exists():
    """Тест существования класса CurrencyConverterApp."""
    from src.currate.gui import CurrencyConverterApp
    assert CurrencyConverterApp is not None


def test_gui_class_has_methods():
    """Тест наличия основных методов в классе GUI."""
    from src.currate.gui import CurrencyConverterApp
    # Проверяем, что класс имеет необходимые методы
    assert hasattr(CurrencyConverterApp, '__init__')
    assert hasattr(CurrencyConverterApp, 'run')


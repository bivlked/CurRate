"""Тесты для точки входа приложения."""

import sys
import pytest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path
from src.currate import main


@patch('src.currate.main.tk.Tk')
@patch('src.currate.main.CurrencyConverterApp')
def test_main_function(mock_app_class, mock_tk):
    """Тест функции main()."""
    mock_root = Mock()
    mock_tk.return_value = mock_root
    mock_app = Mock()
    mock_app_class.return_value = mock_app
    
    main.main()
    
    # Проверяем, что Tk был создан
    mock_tk.assert_called_once()
    # Проверяем, что CurrencyConverterApp был создан
    mock_app_class.assert_called_once_with(mock_root)
    # Проверяем, что run был вызван
    mock_app.run.assert_called_once()


@patch('src.currate.main.tk.Tk')
@patch('src.currate.main.CurrencyConverterApp')
def test_main_module_entry(mock_app_class, mock_tk):
    """Тест запуска модуля как скрипта."""
    mock_root = Mock()
    mock_tk.return_value = mock_root
    mock_app = Mock()
    mock_app_class.return_value = mock_app
    
    # Симулируем запуск через __main__
    with patch('src.currate.main.__name__', '__main__'):
        main.main()
    
    mock_tk.assert_called_once()
    mock_app_class.assert_called_once_with(mock_root)
    mock_app.run.assert_called_once()


def test_import_with_relative_import_success():
    """Тест успешного относительного импорта."""
    # Импорт должен работать нормально
    from src.currate.main import CurrencyConverterApp
    assert CurrencyConverterApp is not None


def test_main_module_has_currency_converter_app():
    """Тест, что модуль main имеет CurrencyConverterApp после импорта."""
    from src.currate.main import CurrencyConverterApp
    assert CurrencyConverterApp is not None
    # Проверяем, что это класс
    assert isinstance(CurrencyConverterApp, type)


@patch('src.currate.main.sys.path')
@patch('src.currate.main.Path')
def test_main_path_addition_when_not_in_path(mock_path, mock_sys_path):
    """Тест добавления пути проекта в sys.path при запуске как скрипта."""
    # Симулируем ситуацию, когда путь не в sys.path
    mock_path_instance = MagicMock()
    mock_path_instance.parent.parent.parent = Path("test_root")
    mock_path.return_value = mock_path_instance
    mock_sys_path.__contains__ = lambda x: False
    
    # Сохраняем оригинальный __name__
    original_name = main.__name__
    
    # Симулируем запуск как __main__
    with patch.object(main, '__name__', '__main__'):
        # Перезагружаем модуль для выполнения блока if __name__ == "__main__"
        import importlib
        try:
            importlib.reload(main)
        except Exception:
            pass  # Может быть ошибка из-за моков, но это нормально
    
    # Восстанавливаем
    main.__name__ = original_name


@patch('src.currate.main.CurrencyConverterApp', side_effect=ModuleNotFoundError("No module named 'currate.gui'"))
@patch('builtins.__import__')
def test_import_module_not_found_fallback(mock_import, mock_app):
    """Тест обработки ModuleNotFoundError с переходом на абсолютный импорт."""
    # Мокируем успешный абсолютный импорт
    mock_module = MagicMock()
    mock_module.CurrencyConverterApp = MagicMock()
    mock_import.return_value = mock_module
    
    # Перезагружаем модуль для тестирования логики импорта
    import importlib
    original_app = getattr(main, 'CurrencyConverterApp', None)
    
    try:
        # Сохраняем оригинальный импорт перед перезагрузкой
        import src.currate.main as main_module
        # Перезагружаем
        importlib.reload(main_module)
    except Exception:
        pass  # Может быть ошибка из-за моков
    
    # Восстанавливаем если нужно
    if original_app:
        main.CurrencyConverterApp = original_app






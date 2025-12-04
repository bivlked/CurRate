"""Тесты для точки входа приложения."""

import pytest
from unittest.mock import patch, Mock
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


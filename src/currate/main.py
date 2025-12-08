"""
CurRate - Конвертер валют с курсами ЦБ РФ.

Главный модуль приложения - точка входа.
"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь для поддержки прямого запуска
if __name__ == "__main__":
    # Получаем путь к корневой директории проекта
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import tkinter as tk

# Используем абсолютный импорт для поддержки прямого запуска
try:
    from .gui import CurrencyConverterApp
except ImportError:
    # Если относительный импорт не работает, используем абсолютный
    from src.currate.gui import CurrencyConverterApp


def main() -> None:
    """
    Главная функция запуска приложения.

    Создает корневое окно Tkinter и запускает приложение.
    """
    root = tk.Tk()
    app = CurrencyConverterApp(root)
    app.run()


if __name__ == "__main__":
    main()

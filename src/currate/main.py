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
except ModuleNotFoundError:
    # ModuleNotFoundError возникает при отсутствии модуля (относительный импорт не работает)
    # Пытаемся использовать абсолютный импорт
    try:
        from src.currate.gui import CurrencyConverterApp
    except ImportError as abs_e:
        # Если и абсолютный импорт не работает, это может быть ошибка зависимостей
        # Пробрасываем её дальше с понятным сообщением
        raise ImportError(
            f"Не удалось импортировать CurrencyConverterApp. "
            f"Проверьте установку зависимостей (pyperclip, tkcalendar): {abs_e}"
        ) from abs_e
except ImportError as e:
    # ImportError (не ModuleNotFoundError) возникает при ошибках внутри модуля
    # (например, отсутствие pyperclip, tkcalendar внутри gui.py)
    # Пробрасываем её дальше без маскировки, чтобы пользователь видел реальную причину
    raise


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

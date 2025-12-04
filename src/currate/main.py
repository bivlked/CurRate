"""
CurRate - Конвертер валют с курсами ЦБ РФ.

Главный модуль приложения - точка входа.
"""

import tkinter as tk
from .gui import CurrencyConverterApp


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

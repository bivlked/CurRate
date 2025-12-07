#!/usr/bin/env python
"""
Простой скрипт для запуска приложения CurRate.

Использование:
    poetry run python run.py
    или
    python run.py
"""

if __name__ == "__main__":
    from src.currate.main import main
    main()

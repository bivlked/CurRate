# CurRate

Currency rates project

## Описание

Проект для работы с курсами валют.

## Установка

```bash
# Клонировать репозиторий
git clone <url>
cd CurRate

# Установить зависимости через Poetry
poetry install

# Активировать виртуальное окружение
poetry shell
```

## Использование

```bash
# Запуск основного скрипта
poetry run python src/currate/main.py

# Или в активированном окружении
python src/currate/main.py
```

## Разработка

```bash
# Добавить зависимость
poetry add <package>

# Добавить dev зависимость
poetry add --group dev <package>

# Запустить тесты
poetry run pytest

# Форматирование кода
poetry run black src tests
```

## Структура проекта

```
CurRate/
├── src/
│   └── currate/        # Основной код проекта
│       ├── __init__.py
│       └── main.py
├── tests/              # Тесты
│   └── __init__.py
├── pyproject.toml      # Конфигурация Poetry и зависимости
├── poetry.lock         # Блокировка версий зависимостей (auto)
├── README.md           # Этот файл
├── .gitignore          # Игнорируемые файлы для git
└── .env.example        # Шаблон переменных окружения
```

## Лицензия

MIT

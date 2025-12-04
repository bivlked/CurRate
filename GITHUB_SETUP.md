# Инструкция по созданию публичного репозитория на GitHub

## Шаги для создания репозитория

### 1. Создание репозитория на GitHub

1. Перейдите на https://github.com/new
2. Заполните форму:
   - **Repository name**: `CurRate` (или другое имя по вашему выбору)
   - **Description**: `Конвертер валют с курсами ЦБ РФ - GUI приложение на Python`
   - **Visibility**: ✅ **Public** (публичный)
   - **НЕ добавляйте** README, .gitignore или лицензию (они уже есть в проекте)
3. Нажмите "Create repository"

### 2. Подключение локального репозитория к GitHub

После создания репозитория GitHub покажет инструкции. Выполните следующие команды:

```powershell
# Добавить remote репозиторий (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/CurRate.git

# Переименовать ветку в main (если нужно)
git branch -M main

# Отправить код на GitHub
git push -u origin main
```

### 3. Проверка безопасности перед первым коммитом

**ВАЖНО**: Перед коммитом убедитесь, что нет секретов:

```powershell
# Проверить на наличие потенциальных секретов
git diff --cached

# Проверить все файлы на секреты
git grep -i "password\|secret\|api_key\|token\|credential" -- :/
```

### 4. Первый коммит

```powershell
# Добавить все файлы (кроме игнорируемых)
git add .

# Проверить, что будет закоммичено
git status

# Создать коммит
git commit -m "feat: initial project setup

- Add currency converter GUI application
- Add CBR parser with retry logic
- Add caching system for exchange rates
- Add unit tests for core components
- Configure Poetry for dependency management"

# Отправить на GitHub
git push -u origin main
```

## Рекомендации по ведению репозитория

### Формат коммитов (Conventional Commits)

Используйте следующий формат:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Типы коммитов:**
- `feat`: новая функциональность
- `fix`: исправление бага
- `docs`: изменения в документации
- `style`: форматирование кода
- `refactor`: рефакторинг
- `test`: добавление/изменение тестов
- `chore`: обновление зависимостей, конфигурации

**Примеры:**
```bash
git commit -m "feat(converter): add EUR currency support"
git commit -m "fix(parser): handle network timeout errors"
git commit -m "test(cache): add TTL expiration tests"
git commit -m "refactor(gui): improve error handling"
```

### Регулярность коммитов

- Коммитьте изменения регулярно (после каждого логического шага)
- Не накапливайте большие изменения в одном коммите
- Каждый коммит должен быть работоспособным

### Проверка перед коммитом

```powershell
# Запустить тесты
poetry run pytest

# Проверить форматирование
poetry run black --check src tests

# Проверить линтер
poetry run pylint src/currate

# Проверить статус
git status

# Проверить изменения
git diff
```

## Защита от утечки секретов

### Что НЕ должно попадать в репозиторий:

- API ключи
- Пароли
- Токены доступа
- Приватные ключи
- Данные пользователей
- Конфигурационные файлы с секретами

### Проверка перед каждым коммитом:

```powershell
# Проверить изменения на секреты
git diff --cached | Select-String -Pattern "password|secret|api_key|token|credential" -CaseSensitive:$false

# Если что-то найдено - НЕ коммитить!
```

### Если секрет уже попал в репозиторий:

1. Немедленно изменить секрет
2. Удалить из истории Git (git filter-branch или BFG Repo-Cleaner)
3. Обновить .gitignore
4. Уведомить всех, кто мог видеть секрет

## Настройка GitHub

### Рекомендуемые настройки:

1. **Branches**: Защитить ветку `main` (Settings → Branches)
2. **Actions**: Включить GitHub Actions для CI/CD
3. **Issues**: Включить Issues для отслеживания задач
4. **Releases**: Настроить автоматические релизы

### Добавить badges в README:

После создания репозитория можно добавить badges:
- Build status
- Test coverage
- License
- Python version

## Следующие шаги

1. Создать репозиторий на GitHub
2. Подключить remote
3. Сделать первый коммит
4. Настроить защиту веток
5. Настроить CI/CD (опционально)


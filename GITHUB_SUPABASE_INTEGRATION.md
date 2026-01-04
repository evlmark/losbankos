# 🔗 Интеграция GitHub и Supabase для автоматических миграций

## Что это дает?

- ✅ Автоматическое применение SQL миграций при коммите в GitHub
- ✅ Версионирование схемы БД в Git
- ✅ Не нужно вручную выполнять SQL в Supabase Dashboard
- ✅ История всех изменений схемы БД
- ✅ Легко откатить изменения

---

## 📋 Вариант 1: Supabase CLI + GitHub Actions (Рекомендуется)

### Шаг 1: Установка Supabase CLI локально

**На macOS:**
```bash
brew install supabase/tap/supabase
```

**На Linux:**
```bash
# Скачайте бинарник с https://github.com/supabase/cli/releases
# Или через npm:
npm install -g supabase
```

**На Windows:**
```bash
# Через Scoop:
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase

# Или через npm:
npm install -g supabase
```

**Проверка установки:**
```bash
supabase --version
```

### Шаг 2: Логин в Supabase через CLI

1. Откройте терминал
2. Выполните:
   ```bash
   supabase login
   ```
3. Откроется браузер для авторизации
4. Войдите в свой аккаунт Supabase
5. После успешного входа CLI сохранит токен

### Шаг 3: Связывание проекта с Supabase

1. Перейдите в папку проекта:
   ```bash
   cd "/Users/markevlampiev/Downloads/Cursor Files/Competitors/reviews_analyzer"
   ```

2. Инициализируйте Supabase в проекте:
   ```bash
   supabase init
   ```
   Это создаст папку `supabase/` с конфигурацией

3. Свяжите проект с вашим Supabase проектом:
   ```bash
   supabase link --project-ref vqqdmdffssmobsofbnqf
   ```
   Где `vqqdmdffssmobsofbnqf` - это часть из вашего URL (https://vqqdmdffssmobsofbnqf.supabase.co)

4. Введите ваш database password (который вы создали при создании проекта)

### Шаг 4: Создание первой миграции

1. Создайте миграцию из существующего SQL файла:
   ```bash
   supabase migration new initial_setup
   ```
   Это создаст файл в `supabase/migrations/` с timestamp

2. Скопируйте содержимое `supabase_setup.sql` в созданный файл миграции

3. Или создайте миграцию вручную:
   ```bash
   # Откройте созданный файл миграции
   # Вставьте SQL из supabase_setup.sql
   ```

### Шаг 5: Применение миграции локально (тест)

```bash
supabase db push
```

Это применит миграции к вашему Supabase проекту.

### Шаг 6: Получение Supabase Access Token для GitHub Actions

1. Перейдите: https://supabase.com/dashboard/account/tokens
2. Нажмите **"Generate new token"**
3. Дайте имя токену (например, "GitHub Actions")
4. Скопируйте токен (он показывается только один раз!)

### Шаг 7: Добавление токена в GitHub Secrets

1. Перейдите: https://github.com/evlmark/losbankos/settings/secrets/actions
2. Нажмите **"New repository secret"**
3. Добавьте:
   - **Name:** `SUPABASE_ACCESS_TOKEN`
   - **Value:** токен из шага 6
4. Нажмите **"Add secret"**

### Шаг 8: Создание GitHub Actions Workflow

Создайте файл `.github/workflows/supabase_migrations.yml`:

```yaml
name: Supabase Migrations

on:
  push:
    branches:
      - main
    paths:
      - 'supabase/migrations/**'
  workflow_dispatch:  # Позволяет запускать вручную

jobs:
  migrate:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Setup Supabase CLI
      uses: supabase/setup-cli@v1
      with:
        version: latest
    
    - name: Run migrations
      env:
        SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
        SUPABASE_DB_PASSWORD: ${{ secrets.SUPABASE_DB_PASSWORD }}
      run: |
        supabase link --project-ref vqqdmdffssmobsofbnqf
        supabase db push
```

### Шаг 9: Добавление пароля БД в GitHub Secrets

1. Перейдите: https://github.com/evlmark/losbankos/settings/secrets/actions
2. Добавьте:
   - **Name:** `SUPABASE_DB_PASSWORD`
   - **Value:** ваш database password (`xafsur-3voqvi-mokgIw`)

### Шаг 10: Коммит и тест

1. Закоммитьте изменения:
   ```bash
   git add supabase/ .github/workflows/supabase_migrations.yml
   git commit -m "Add Supabase migrations and GitHub Actions integration"
   git push origin main
   ```

2. Проверьте GitHub Actions:
   - Перейдите: https://github.com/evlmark/losbankos/actions
   - Должен запуститься workflow "Supabase Migrations"
   - Проверьте, что он выполнился успешно

---

## 📋 Вариант 2: GitHub Actions + Supabase REST API (Проще, но менее гибко)

### Шаг 1: Получение Supabase Access Token

1. Перейдите: https://supabase.com/dashboard/account/tokens
2. Создайте новый токен
3. Сохраните его

### Шаг 2: Добавление в GitHub Secrets

1. Добавьте `SUPABASE_ACCESS_TOKEN` в GitHub Secrets
2. Добавьте `SUPABASE_URL` (если еще нет)
3. Добавьте `SUPABASE_DB_PASSWORD`

### Шаг 3: Создание Workflow

Создайте `.github/workflows/supabase_migrations.yml`:

```yaml
name: Supabase Migrations

on:
  push:
    paths:
      - 'supabase/migrations/**'
  workflow_dispatch:

jobs:
  migrate:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Install Supabase CLI
      run: |
        npm install -g supabase
    
    - name: Run migrations
      env:
        SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
        SUPABASE_DB_PASSWORD: ${{ secrets.SUPABASE_DB_PASSWORD }}
      run: |
        supabase login --token $SUPABASE_ACCESS_TOKEN
        supabase link --project-ref vqqdmdffssmobsofbnqf
        supabase db push
```

---

## 📋 Вариант 3: Ручное выполнение SQL (Самый простой, но не автоматический)

Если автоматизация кажется сложной, можно просто:

1. Хранить SQL миграции в папке `supabase/migrations/`
2. При изменении схемы:
   - Создать новый файл миграции
   - Закоммитить в Git
   - Вручную скопировать SQL в Supabase SQL Editor
   - Выполнить

Это не автоматически, но проще в настройке.

---

## ⚙️ Что нужно настроить

### Обязательно:
- ✅ Supabase CLI установлен локально
- ✅ Логин через `supabase login`
- ✅ Связывание проекта через `supabase link`
- ✅ Supabase Access Token в GitHub Secrets
- ✅ Database Password в GitHub Secrets
- ✅ GitHub Actions workflow файл

### Опционально:
- 📁 Папка `supabase/migrations/` для хранения миграций
- 📝 Файл `supabase/config.toml` для конфигурации

---

## 🔍 Проверка работы

### После настройки:

1. **Создайте тестовую миграцию:**
   ```bash
   supabase migration new test_migration
   ```

2. **Добавьте простой SQL:**
   ```sql
   -- Тестовая миграция
   SELECT 1;
   ```

3. **Закоммитьте и запушьте:**
   ```bash
   git add supabase/migrations/
   git commit -m "Test migration"
   git push
   ```

4. **Проверьте GitHub Actions:**
   - Должен запуститься workflow
   - Должен выполниться успешно

---

## ⚠️ Важные замечания

### Безопасность:
- **Никогда не коммитьте** `SUPABASE_ACCESS_TOKEN` или пароли в код
- Храните их только в GitHub Secrets
- Используйте разные токены для разных окружений (dev/prod)

### Ограничения:
- Миграции применяются только при изменении файлов в `supabase/migrations/`
- Данные (подписчики, отчеты) не синхронизируются автоматически
- Это только для схемы БД (таблицы, индексы, политики)

### Откат изменений:
- Можно создать миграцию для отката
- Или использовать `supabase db reset` (осторожно - удалит все данные!)

---

## 🆘 Если что-то не работает

### Проблема: CLI не устанавливается
**Решение:** Используйте npm версию или скачайте бинарник с GitHub

### Проблема: Не могу залогиниться
**Решение:** Проверьте, что используете правильный аккаунт Supabase

### Проблема: Ошибка при `supabase link`
**Решение:** 
- Проверьте project-ref (часть из URL)
- Проверьте пароль БД
- Убедитесь, что проект активен

### Проблема: Workflow не запускается
**Решение:**
- Проверьте, что файлы в `supabase/migrations/` изменены
- Проверьте путь в `paths:` в workflow
- Проверьте, что workflow файл в правильной папке

### Проблема: Ошибка в workflow
**Решение:**
- Проверьте логи в GitHub Actions
- Убедитесь, что все секреты добавлены
- Проверьте, что токены не истекли

---

## 📊 Сравнение вариантов

| Вариант | Сложность настройки | Автоматизация | Гибкость |
|---------|---------------------|---------------|----------|
| **Вариант 1 (CLI + Actions)** | Средняя | ✅ Полная | ✅ Высокая |
| **Вариант 2 (REST API)** | Низкая | ✅ Полная | ⚠️ Средняя |
| **Вариант 3 (Ручной)** | Очень низкая | ❌ Нет | ⚠️ Низкая |

---

## ✅ Рекомендация

**Для начала:** Используйте Вариант 3 (ручное выполнение)
- Проще всего
- Не требует настройки
- Можно перейти на автоматизацию позже

**Для продакшена:** Используйте Вариант 1 (CLI + Actions)
- Полная автоматизация
- Версионирование миграций
- История изменений

---

## 📚 Полезные ссылки

- **Supabase CLI Docs:** https://supabase.com/docs/reference/cli
- **GitHub Actions:** https://docs.github.com/en/actions
- **Supabase Migrations:** https://supabase.com/docs/guides/cli/local-development#database-migrations

---

## 🎯 Итог

**Сложность:** Средняя (2-3 часа на настройку первый раз)

**Плюсы:**
- Автоматизация миграций
- Версионирование схемы
- Не нужно вручную выполнять SQL

**Минусы:**
- Требует настройки
- Нужно установить CLI
- Нужны токены и пароли

**Стоит ли делать?**
- Если планируете часто менять схему БД - **ДА**
- Если схема стабильная - можно обойтись ручным выполнением SQL


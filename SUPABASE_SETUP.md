# 🗄️ Настройка Supabase для хранения подписчиков и отчетов

## Зачем нужен Supabase?

Supabase упрощает работу с данными:
- ✅ Нет проблем с синхронизацией через git
- ✅ Подписчики и отчеты в одном месте
- ✅ Доступ из бота на Render и из GitHub Actions
- ✅ Бесплатный tier (500MB базы данных)
- ✅ Простой веб-интерфейс для управления данными

---

## 📋 Шаг 1: Создание проекта Supabase

### 1.1 Регистрация

1. Перейдите: https://supabase.com
2. Нажмите **"Start your project"** или **"Sign up"**
3. Войдите через GitHub (рекомендуется) или создайте аккаунт

### 1.2 Создание проекта

1. Нажмите **"New Project"**
2. Заполните форму:
   - **Name:** `reviews-analyzer` (или любое другое имя)
   - **Database Password:** придумайте надежный пароль (сохраните его!)
   - **Region:** выберите ближайший (например, `West US` или `Europe West`)
   - **Pricing Plan:** выберите **Free** (достаточно для начала)
3. Нажмите **"Create new project"**
4. Подождите 1-2 минуты, пока проект создается

---

## 📋 Шаг 2: Получение credentials

### 2.1 Project Settings

1. В левом меню нажмите **⚙️ Settings** (шестеренка)
2. Выберите **API** в подменю

### 2.2 Сохраните следующие данные:

**Project URL:**
- Находится в разделе **Project URL**
- Пример: `https://xxxxx.supabase.co`
- Скопируйте и сохраните

**anon/public key:**
- Находится в разделе **Project API keys**
- Скопируйте **anon public** ключ (это ваш `SUPABASE_KEY`)
- Пример: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

**service_role key (опционально, для админских операций):**
- Тот же раздел
- Скопируйте **service_role** ключ (НЕ публикуйте его!)
- Используйте только для серверных операций

### 2.3 Database Connection String

1. В Settings выберите **Database**
2. Найдите раздел **Connection string**
3. Выберите **URI** вкладку
4. Скопируйте строку подключения
5. Замените `[YOUR-PASSWORD]` на пароль, который вы создали при создании проекта
6. Пример: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres`

---

## 📋 Шаг 3: Создание таблиц в базе данных

### Вариант A: Автоматическая настройка (Рекомендуется)

1. **Установите зависимости:**
   ```bash
   pip install supabase psycopg2-binary
   ```

2. **Настройте переменные окружения:**
   
   Создайте файл `.env` в корне проекта (или добавьте в существующий):
   ```bash
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=ваш_anon_public_key
   SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
   
   **Важно:** Замените `[YOUR-PASSWORD]` на пароль, который вы создали при создании проекта.

3. **Запустите скрипт настройки:**
   ```bash
   python setup_supabase.py
   ```
   
   Скрипт автоматически создаст все таблицы, индексы и политики безопасности.

### Вариант B: Ручная настройка через SQL Editor

Если автоматическая настройка не работает, используйте ручной метод:

#### 3.1 Откройте SQL Editor

1. В левом меню нажмите **SQL Editor**
2. Нажмите **"New query"**

#### 3.2 Выполните SQL скрипт

Откройте файл `supabase_setup.sql` в проекте, скопируйте весь его содержимое и вставьте в SQL Editor, затем нажмите **"Run"**.

Или выполните SQL по частям:

#### 3.3 Создайте таблицу подписчиков

Вставьте и выполните следующий SQL:

```sql
-- Таблица подписчиков Telegram бота
CREATE TABLE IF NOT EXISTS subscribers (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,
    subscribed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    last_report_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индекс для быстрого поиска по chat_id
CREATE INDEX IF NOT EXISTS idx_subscribers_chat_id ON subscribers(chat_id);

-- Индекс для активных подписчиков
CREATE INDEX IF NOT EXISTS idx_subscribers_active ON subscribers(is_active) WHERE is_active = TRUE;
```

### 3.3 Создайте таблицу отчетов

Вставьте и выполните следующий SQL:

```sql
-- Таблица отчетов
CREATE TABLE IF NOT EXISTS reports (
    id BIGSERIAL PRIMARY KEY,
    app_name TEXT NOT NULL,
    report_content TEXT NOT NULL,
    report_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_reviews INTEGER,
    positive_count INTEGER,
    neutral_count INTEGER,
    negative_count INTEGER,
    is_latest BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индекс для поиска последнего отчета
CREATE INDEX IF NOT EXISTS idx_reports_latest ON reports(is_latest) WHERE is_latest = TRUE;

-- Индекс для поиска по дате
CREATE INDEX IF NOT EXISTS idx_reports_date ON reports(report_date DESC);

-- Индекс для поиска по приложению
CREATE INDEX IF NOT EXISTS idx_reports_app_name ON reports(app_name);
```

### 3.4 Создайте таблицу для комбинированных отчетов

Вставьте и выполните следующий SQL:

```sql
-- Таблица для комбинированных отчетов (все компании вместе)
CREATE TABLE IF NOT EXISTS combined_reports (
    id BIGSERIAL PRIMARY KEY,
    report_content TEXT NOT NULL,
    report_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_apps INTEGER,
    total_reviews INTEGER,
    is_latest BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индекс для последнего комбинированного отчета
CREATE INDEX IF NOT EXISTS idx_combined_reports_latest ON combined_reports(is_latest) WHERE is_latest = TRUE;

-- Индекс для поиска по дате
CREATE INDEX IF NOT EXISTS idx_combined_reports_date ON combined_reports(report_date DESC);
```

### 3.4 Настройте Row Level Security (RLS)

Для безопасности настройте RLS (опционально, но рекомендуется):

```sql
-- Включить RLS для таблиц
ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE combined_reports ENABLE ROW LEVEL SECURITY;

-- Политики для subscribers (разрешить все операции через API)
CREATE POLICY "Allow all operations on subscribers" ON subscribers
    FOR ALL USING (true) WITH CHECK (true);

-- Политики для reports (разрешить чтение всем, запись через API)
CREATE POLICY "Allow read on reports" ON reports
    FOR SELECT USING (true);
CREATE POLICY "Allow insert on reports" ON reports
    FOR INSERT WITH CHECK (true);

-- Политики для combined_reports
CREATE POLICY "Allow read on combined_reports" ON combined_reports
    FOR SELECT USING (true);
CREATE POLICY "Allow insert on combined_reports" ON combined_reports
    FOR INSERT WITH CHECK (true);
```

**Важно:** Если RLS вызывает проблемы, можно временно отключить:
```sql
ALTER TABLE subscribers DISABLE ROW LEVEL SECURITY;
ALTER TABLE reports DISABLE ROW LEVEL SECURITY;
ALTER TABLE combined_reports DISABLE ROW LEVEL SECURITY;
```

---

## 📋 Шаг 4: Установка переменных окружения

### 4.1 Для GitHub Actions (GitHub Secrets)

1. Перейдите: https://github.com/evlmark/losbankos/settings/secrets/actions
2. Добавьте следующие секреты:

**SUPABASE_URL:**
- **Name:** `SUPABASE_URL`
- **Value:** ваш Project URL (например, `https://xxxxx.supabase.co`)

**SUPABASE_KEY:**
- **Name:** `SUPABASE_KEY`
- **Value:** ваш anon public key

**SUPABASE_DB_URL (опционально, для прямого подключения к PostgreSQL):**
- **Name:** `SUPABASE_DB_URL`
- **Value:** connection string из шага 2.3

### 4.2 Для Render (Environment Variables)

1. Откройте Render Dashboard → ваш Web Service
2. Перейдите в раздел **Environment**
3. Добавьте переменные:

**SUPABASE_URL:**
- **Key:** `SUPABASE_URL`
- **Value:** ваш Project URL

**SUPABASE_KEY:**
- **Key:** `SUPABASE_KEY`
- **Value:** ваш anon public key

**SUPABASE_DB_URL (опционально):**
- **Key:** `SUPABASE_DB_URL`
- **Value:** connection string

4. Нажмите **"Save Changes"**
5. Render автоматически перезапустит сервис

---

## 📋 Шаг 5: Установка библиотеки для работы с Supabase

### 5.1 Добавьте в requirements.txt

Добавьте следующую строку в `requirements.txt`:

```
supabase==2.3.4
psycopg2-binary==2.9.9
```

Или если используете только REST API (без прямого подключения к PostgreSQL):

```
supabase==2.3.4
```

### 5.2 Установите зависимости

```bash
pip install -r requirements.txt
```

---

## 📋 Шаг 6: Миграция существующих данных (опционально)

### 6.1 Миграция подписчиков

Если у вас уже есть подписчики в `telegram_subscribers.json`:

1. Откройте файл `telegram_subscribers.json`
2. Скопируйте список chat_id
3. В Supabase SQL Editor выполните:

```sql
-- Вставьте подписчиков (замените chat_id на ваши)
INSERT INTO subscribers (chat_id, subscribed_at)
VALUES 
    (123456789, NOW()),
    (987654321, NOW())
ON CONFLICT (chat_id) DO NOTHING;
```

### 6.2 Миграция отчетов

Если у вас уже есть отчеты в папке `reports/`:

1. Откройте файл `reports/latest_report.md`
2. Скопируйте содержимое
3. В Supabase SQL Editor выполните:

```sql
-- Вставьте отчет (замените содержимое на ваше)
INSERT INTO combined_reports (report_content, report_date, is_latest)
VALUES 
    ('содержимое вашего отчета', NOW(), TRUE)
ON CONFLICT DO NOTHING;

-- Сделайте все остальные отчеты не последними
UPDATE combined_reports SET is_latest = FALSE WHERE id != (SELECT id FROM combined_reports ORDER BY report_date DESC LIMIT 1);
```

---

## 📋 Шаг 7: Проверка подключения

### 7.1 Проверка через Supabase Dashboard

1. Откройте Supabase Dashboard
2. Перейдите в **Table Editor**
3. Вы должны увидеть созданные таблицы:
   - `subscribers`
   - `reports`
   - `combined_reports`

### 7.2 Тестовая вставка данных

В SQL Editor выполните:

```sql
-- Тестовая вставка подписчика
INSERT INTO subscribers (chat_id) VALUES (999999999) ON CONFLICT DO NOTHING;

-- Проверка
SELECT * FROM subscribers WHERE chat_id = 999999999;

-- Удаление тестового подписчика
DELETE FROM subscribers WHERE chat_id = 999999999;
```

---

## 📋 Шаг 8: Обновление кода

После настройки Supabase нужно обновить код:

1. **telegram_bot.py** - использовать Supabase вместо файлов для:
   - Загрузки/сохранения подписчиков
   - Чтения последнего отчета

2. **main.py** - использовать Supabase для:
   - Сохранения отчетов в БД
   - Отправки отчетов подписчикам из БД

3. **config.py** - добавить конфигурацию Supabase

---

## 🔍 Проверка работы

### После обновления кода:

1. **Проверьте бота:**
   - Отправьте `/start` в Telegram
   - Бот должен добавить вас в подписчики в Supabase

2. **Проверьте Supabase:**
   - Откройте Table Editor → `subscribers`
   - Должен появиться ваш chat_id

3. **Проверьте отчеты:**
   - Запустите workflow в GitHub Actions
   - Отчет должен сохраниться в `combined_reports`
   - Бот должен прочитать его из БД

---

## ⚠️ Важные замечания

### Безопасность:

1. **Никогда не коммитьте** `SUPABASE_KEY` или `SUPABASE_DB_URL` в код
2. Используйте только **anon public key** в клиентском коде
3. **service_role key** используйте только на сервере (GitHub Actions, Render)
4. Настройте RLS политики для защиты данных

### Лимиты бесплатного плана:

- **500MB** базы данных
- **2GB** bandwidth в месяц
- **50,000** запросов в месяц
- **500MB** файлового хранилища

Для вашего проекта этого должно быть достаточно.

### Резервное копирование:

Supabase автоматически делает бэкапы, но можно настроить дополнительные:
- Settings → Database → Backups

---

## 📚 Полезные ссылки

- **Supabase Dashboard:** https://supabase.com/dashboard
- **Документация:** https://supabase.com/docs
- **SQL Editor:** https://supabase.com/dashboard/project/_/sql
- **Table Editor:** https://supabase.com/dashboard/project/_/editor

---

## 🆘 Если что-то не работает

### Проблема: Не могу подключиться к Supabase

**Решение:**
1. Проверьте, что `SUPABASE_URL` правильный (без слеша в конце)
2. Проверьте, что `SUPABASE_KEY` правильный (anon public key)
3. Проверьте, что проект не приостановлен (Free tier может приостанавливаться)

### Проблема: Ошибка при вставке данных

**Решение:**
1. Проверьте RLS политики (может быть нужно отключить)
2. Проверьте, что таблицы созданы правильно
3. Проверьте логи в Supabase Dashboard → Logs

### Проблема: Бот не видит данные

**Решение:**
1. Проверьте, что переменные окружения установлены в Render
2. Проверьте, что код использует правильные переменные
3. Проверьте логи бота на Render

---

## ✅ Следующие шаги

После настройки Supabase:

1. ✅ Обновите код для работы с БД (см. следующие инструкции)
2. ✅ Протестируйте работу бота
3. ✅ Запустите workflow и проверьте сохранение отчетов
4. ✅ Удалите старые файлы (`telegram_subscribers.json`, папка `reports/`)

Готово! 🎉


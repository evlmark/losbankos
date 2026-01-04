# 🌐 Настройка бота на Render Web Services

## Шаги настройки

### 1. Создайте Web Service в Render

1. Нажмите **"New Web Service"** в Render
2. Подключите GitHub репозиторий: `evlmark/losbankos`
3. Настройте следующие параметры:

### 2. Настройки сервиса

**Name:** `losbankos-bot` (или любое другое имя)

**Environment:** `Python 3`

**Python Version:** `3.11` (важно! Python 3.13 несовместим с pandas)

**Region:** Выберите ближайший (например, Frankfurt)

**Branch:** `main`

**Root Directory:** (оставьте пустым)

**Build Command:**
```
pip install --upgrade pip && pip install -r requirements.txt
```

**Start Command:**
```
python run_bot.py
```

**⚠️ ВАЖНО:** 
- НЕ используйте `bash python run_bot.py` - это вызовет ошибку
- Используйте просто `python run_bot.py`
- Или полный путь: `/opt/render/project/src/.venv/bin/python run_bot.py`

### 3. Переменные окружения

В разделе **Environment Variables** добавьте:

- **Key:** `TELEGRAM_BOT_TOKEN`
  **Value:** `ваш_telegram_bot_token` (из .env файла)

- **Key:** `OPENAI_API_KEY`
  **Value:** `ваш_openai_api_key` (из .env файла)

- **Key:** `LLM_PROVIDER`
  **Value:** `openai`

- **Key:** `LLM_MODEL`
  **Value:** `gpt-4o-mini`

- **Key:** `SUPABASE_URL` (ОБЯЗАТЕЛЬНО для работы с базой данных)
  **Value:** `https://vqqdmdffssmobsofbnqf.supabase.co`
  **Описание:** URL вашего Supabase проекта

- **Key:** `SUPABASE_KEY` (ОБЯЗАТЕЛЬНО для работы с базой данных)
  **Value:** `ваш_anon_public_key`
  **Описание:** Anon public key для доступа к Supabase API
  **Где найти:** Supabase Dashboard → Settings → API → Project API keys → anon public

- **Key:** `GIT_TOKEN` (ОПЦИОНАЛЬНО, только если не используете Supabase)
  **Value:** `ваш_github_personal_access_token`
  **Описание:** GitHub Personal Access Token (только для fallback на файловое хранилище)
  **Примечание:** Если используете Supabase, этот токен не нужен

### 4. План

Выберите **Free** план (если доступен)

### 5. Деплой

Нажмите **"Create Web Service"**

Render начнет деплой. Это займет несколько минут.

---

## Как перезапустить деплой

### Вариант 1: Через Manual Deploy (Рекомендуется)

1. В Render Dashboard найдите кнопку **"Manual Deploy"** (справа вверху)
2. Нажмите на нее
3. Выберите **"Deploy latest commit"**
4. Render начнет новый деплой с последними изменениями

### Вариант 2: Автоматически

- Render автоматически перезапускает деплой при изменении кода в GitHub
- Если вы только что отправили изменения, подождите 1-2 минуты

### Вариант 3: Очистить кэш и перезапустить

Если деплой все еще не работает:
1. Manual Deploy → **"Clear build cache & deploy"**
2. Это удалит старый кэш и начнет чистый деплой

---

## После деплоя

1. **Проверьте логи:**
   - В Render Dashboard откройте ваш сервис
   - Перейдите в раздел "Logs"
   - Должно быть: "Starting Telegram bot..." и "Starting Telegram bot polling..."

2. **Проверьте работу бота:**
   - Откройте бота @losbankosbot в Telegram
   - Отправьте `/start`
   - Бот должен ответить

3. **Проверьте подписчиков:**
   - Отправьте `/subscribers`
   - Должен показать ваш chat_id

---

## ⚠️ Важно: Ограничение бесплатного плана

**"Your free instance will spin down with inactivity"**

Это означает:
- Если бот не получает запросы **15 минут**, он "засыпает"
- При новом запросе бот просыпается, но это занимает **~50 секунд**
- Пользователь получит ответ с задержкой 50+ секунд

**Как это влияет:**
- ✅ Бот будет работать, но с задержкой при первом запросе после простоя
- ❌ Не идеально для постоянной работы, но для тестирования подойдет
- ✅ GitHub Actions все равно сможет отправлять отчеты (он "разбудит" бота)

**Решения:**
1. Принять задержку (для начала подойдет)
2. Использовать Background Workers (если есть бесплатный план)
3. Перейти на платный план Render ($7/месяц)
4. Использовать другой сервис (Oracle Cloud Free Tier, Fly.io)

---

## Если возникнут проблемы

1. Проверьте логи в Render Dashboard
2. Убедитесь, что все переменные окружения установлены
3. Проверьте, что Start Command правильный: `python run_bot.py`


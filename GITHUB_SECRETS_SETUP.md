# 🔐 Настройка GitHub Secrets

## Инструкция по добавлению секретов

1. Перейдите в ваш репозиторий: https://github.com/evlmark/losbankos
2. Нажмите **Settings** (в верхнем меню)
3. В левом меню выберите **Secrets and variables** → **Actions**
4. Нажмите **New repository secret** для каждого секрета ниже

---

## 📋 Список секретов для добавления

### 1. Telegram Bot Token (ОБЯЗАТЕЛЬНО)

- **Name:** `TELEGRAM_BOT_TOKEN`
- **Value:** `ваш_telegram_bot_token` (получите у @BotFather в Telegram)
- **Описание:** Токен Telegram бота для отправки отчетов

---

### 2. OpenAI API Key (ОБЯЗАТЕЛЬНО для AI-суммаризации)

- **Name:** `OPENAI_API_KEY`
- **Value:** `ваш_openai_api_key` (получите на https://platform.openai.com/api-keys)
- **Описание:** Токен OpenAI для генерации AI-суммари отзывов

---

### 3. LLM Provider (ОПЦИОНАЛЬНО, но рекомендуется)

- **Name:** `LLM_PROVIDER`
- **Value:** `openai`
- **Описание:** Провайдер LLM (openai или anthropic)
- **По умолчанию:** `openai` (если не указано)

---

### 4. LLM Model (ОПЦИОНАЛЬНО, но рекомендуется)

- **Name:** `LLM_MODEL`
- **Value:** `gpt-4o-mini`
- **Описание:** Модель LLM для использования
- **По умолчанию:** `gpt-4o-mini` (если не указано)

---

### 5. Notification Method (ОПЦИОНАЛЬНО)

- **Name:** `NOTIFICATION_METHOD`
- **Value:** `telegram`
- **Описание:** Метод уведомлений (telegram или slack)
- **По умолчанию:** `telegram` (если не указано)

---

### 6. Reviews Per App (ОПЦИОНАЛЬНО)

- **Name:** `REVIEWS_PER_APP`
- **Value:** `100`
- **Описание:** Количество отзывов для сбора с каждого приложения
- **По умолчанию:** `100` (если не указано)

---

### 7. Git Token (ОБЯЗАТЕЛЬНО для автоматического коммита отчетов)

- **Name:** `GIT_TOKEN`
- **Value:** `ваш_github_personal_access_token`
- **Описание:** GitHub Personal Access Token для автоматического коммита отчетов в репозиторий из GitHub Actions
- **Как создать:**
  1. Перейдите: https://github.com/settings/tokens
  2. Нажмите "Generate new token (classic)"
  3. Выберите права: `repo` (полный доступ к репозиториям)
  4. Скопируйте токен
- **Где использовать:** 
  - **В GitHub Secrets** (для автоматического коммита отчетов из workflow)
  - **В Render Environment Variables** (для синхронизации подписчиков из бота)
- **Важно:** Без этого токена отчеты не будут автоматически коммититься в репозиторий, и бот не сможет их прочитать

**Альтернатива (если не хотите создавать PAT):**
Настройте права для `GITHUB_TOKEN` в репозитории:
1. Settings → Actions → General
2. Scroll down to "Workflow permissions"
3. Выберите "Read and write permissions"
4. Нажмите "Save"

---

## 📝 Опциональные секреты (если нужны)

### Anthropic API Key (если используете Anthropic вместо OpenAI)

- **Name:** `ANTHROPIC_API_KEY`
- **Value:** `ваш_токен_anthropic`
- **Описание:** Токен Anthropic для альтернативного LLM провайдера

### Slack Configuration (если используете Slack вместо Telegram)

- **Name:** `SLACK_BOT_TOKEN`
- **Value:** `ваш_slack_bot_token`
- **Описание:** Токен Slack бота

- **Name:** `SLACK_CHANNEL_ID`
- **Value:** `ваш_slack_channel_id`
- **Описание:** ID Slack канала

### Telegram Chat ID (если используете старый способ уведомлений)

- **Name:** `TELEGRAM_CHAT_ID`
- **Value:** `ваш_chat_id`
- **Описание:** ID Telegram чата/канала (не нужно для нового бота с /start)

---

## ✅ Минимальный набор секретов (для работы)

Для базовой работы достаточно добавить:

1. ✅ `TELEGRAM_BOT_TOKEN` - для отправки отчетов
2. ✅ `OPENAI_API_KEY` - для AI-суммаризации отзывов
3. ✅ `SUPABASE_URL` - URL вашего Supabase проекта
4. ✅ `SUPABASE_KEY` - anon public key для Supabase

Остальные настройки будут использованы по умолчанию.

---

## 🎯 Рекомендуемый набор секретов

Для полной функциональности добавьте:

1. ✅ `TELEGRAM_BOT_TOKEN`
2. ✅ `OPENAI_API_KEY`
3. ✅ `SUPABASE_URL`
4. ✅ `SUPABASE_KEY`
5. ✅ `LLM_PROVIDER` = `openai`
6. ✅ `LLM_MODEL` = `gpt-4o-mini`
7. ✅ `NOTIFICATION_METHOD` = `telegram`
8. ✅ `REVIEWS_PER_APP` = `100`

---

## 📸 Как добавить секрет

1. Нажмите **New repository secret**
2. В поле **Name** введите название секрета (например, `TELEGRAM_BOT_TOKEN`)
3. В поле **Secret** вставьте значение (например, токен)
4. Нажмите **Add secret**
5. Повторите для всех секретов

---

## 🔍 Проверка секретов

После добавления всех секретов:

1. Перейдите в **Actions** → **Weekly Reviews Analysis**
2. Нажмите **Run workflow** (для тестового запуска)
3. Проверьте логи выполнения
4. Если все настроено правильно, отчет будет отправлен в Telegram

---

## ⚠️ Важно

- **Никогда не коммитьте секреты в код!** Они должны быть только в GitHub Secrets
- Файл `.env` уже в `.gitignore` и не будет закоммичен
- Секреты доступны только в GitHub Actions, не в коде репозитория

---

## 📚 Ссылки

- Репозиторий: https://github.com/evlmark/losbankos
- Настройка секретов: https://github.com/evlmark/losbankos/settings/secrets/actions
- GitHub Actions: https://github.com/evlmark/losbankos/actions


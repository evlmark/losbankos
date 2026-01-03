# 🚀 Быстрый старт: Деплой на GitHub Actions

## Шаг 1: Создание Telegram бота (5 минут)

1. Откройте Telegram → найдите [@BotFather](https://t.me/botfather)
2. Отправьте `/newbot` и следуйте инструкциям
3. **Скопируйте токен** (например: `123456789:ABCdef...`)
4. Получите Chat ID:
   - Для личного чата: напишите боту, затем откройте:
     ```
     https://api.telegram.org/botВАШ_ТОКЕН/getUpdates
     ```
   - Найдите `"chat":{"id":123456789}` - это ваш Chat ID

Подробнее: см. `setup_telegram_bot.md`

## Шаг 2: Создание GitHub репозитория

```bash
# В папке проекта
git init
git add .
git commit -m "Initial commit: Reviews Analyzer"

# Создайте репозиторий на GitHub, затем:
git remote add origin https://github.com/ВАШ_USERNAME/reviews-analyzer.git
git branch -M main
git push -u origin main
```

## Шаг 3: Настройка Secrets в GitHub

1. Перейдите в ваш репозиторий на GitHub
2. Settings → Secrets and variables → Actions
3. Нажмите "New repository secret" и добавьте:

   **Обязательные:**
   - `TELEGRAM_BOT_TOKEN` = ваш токен бота
   - `TELEGRAM_CHAT_ID` = ваш Chat ID
   - `NOTIFICATION_METHOD` = `telegram`

   **Опциональные (для LLM саммари):**
   - `OPENAI_API_KEY` = ваш OpenAI ключ
   - `LLM_PROVIDER` = `openai`
   - `LLM_MODEL` = `gpt-4o-mini`

   **Опциональные (настройки):**
   - `REVIEWS_PER_APP` = `100` (количество отзывов)

## Шаг 4: Настройка расписания (опционально)

Файл `.github/workflows/weekly_reviews.yml` уже создан и настроен на:
- Запуск каждый понедельник в 09:00 UTC
- Возможность ручного запуска

Чтобы изменить расписание, отредактируйте строку:
```yaml
- cron: '0 9 * * 1'  # Понедельник, 09:00 UTC
```

Примеры:
- `'0 9 * * 1'` - каждый понедельник в 09:00
- `'0 9 * * 0'` - каждое воскресенье в 09:00
- `'0 */6 * * *'` - каждые 6 часов

## Шаг 5: Первый запуск

1. Перейдите в Actions → Weekly Reviews Analysis
2. Нажмите "Run workflow" → "Run workflow"
3. Дождитесь завершения (обычно 2-5 минут)
4. Проверьте Telegram - должен прийти отчет!

## ✅ Готово!

Теперь скрипт будет автоматически запускаться по расписанию и отправлять отчеты в Telegram.

### Полезные команды:

- **Просмотр логов:** Actions → выберите workflow → выберите run
- **Скачать отчеты:** Actions → выберите run → Artifacts
- **Изменить расписание:** отредактируйте `.github/workflows/weekly_reviews.yml`

### Важно:

- ✅ Код можно писать локально и пушить в GitHub - все будет работать
- ✅ GitHub Actions запускается автоматически по расписанию
- ✅ Отчеты сохраняются как Artifacts на 30 дней
- ✅ Все секреты хранятся безопасно в GitHub Secrets

### Устранение неполадок:

**Бот не отправляет сообщения:**
- Проверьте токен и Chat ID в Secrets
- Убедитесь, что бот добавлен в канал/чат

**Workflow не запускается:**
- Проверьте, что файл `.github/workflows/weekly_reviews.yml` в репозитории
- Проверьте синтаксис cron выражения

**Ошибки при парсинге:**
- Проверьте `competitors.json` - правильные ли App ID


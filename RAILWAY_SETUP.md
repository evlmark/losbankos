# 🚂 Настройка бота на Railway

## Проблема: "Error loading ASGI app"

Railway пытается запустить бот как веб-приложение, но бот - это long-running процесс с polling.

## Решение

### Вариант 1: Настройка через Railway Dashboard (Рекомендуется)

1. **Откройте ваш сервис на Railway**
2. **Settings → Deploy**
3. **Root Directory:** (оставьте пустым, репозиторий уже в правильной папке)
4. **Start Command:** `python run_bot.py`
5. **Build Command:** `pip install --upgrade pip && pip install -r requirements.txt`

### Вариант 2: Использовать Procfile (автоматически)

Railway автоматически использует `Procfile` из корня репозитория:
- `Procfile` уже создан: `worker: python run_bot.py`

### Вариант 3: Использовать railway.json (автоматически)

Файл `railway.json` в корне репозитория уже настроен с правильным `startCommand`: `python run_bot.py`

## Переменные окружения

В Railway Dashboard → Variables добавьте:

- `TELEGRAM_BOT_TOKEN`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `OPENAI_API_KEY`
- `LLM_PROVIDER` = `openai`
- `LLM_MODEL` = `gpt-4o-mini`

## Важно

1. **Root Directory:** Если код в подпапке, укажите `Competitors/reviews_analyzer`
2. **Start Command:** Должен быть `python run_bot.py` (не `python main.py`!)
3. **Service Type:** Railway должен определить это как "Worker" или "Service", не как "Web Service"

## Проверка

1. **Логи:** Должно быть `🚀 Starting Telegram bot polling...`
2. **Health endpoint:** `https://your-service.up.railway.app/health` должен вернуть `Bot is running`
3. **Telegram:** Отправьте `/ping` - должен ответить

## Если всё ещё не работает

1. Проверьте логи на Railway - там будет точная ошибка
2. Убедитесь, что `Root Directory` правильный
3. Убедитесь, что `Start Command` правильный: `python run_bot.py`
4. Попробуйте полный путь: `cd Competitors/reviews_analyzer && python run_bot.py`


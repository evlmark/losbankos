# 🔄 Keep-Alive Setup для Render Free Tier

## Проблема

На бесплатном тарифе Render Web Service засыпает после **15 минут** бездействия. Когда бот засыпает:
- Команды в Telegram не обрабатываются сразу
- Первый запрос после простоя занимает ~50 секунд (пока бот просыпается)
- Пользователи видят задержку в ответах

## Решение

GitHub Actions автоматически "будит" бота каждые **10 минут**, отправляя HTTP запрос к health endpoint.

## Настройка

### Шаг 1: Найдите URL вашего бота на Render

1. Откройте [Render Dashboard](https://dashboard.render.com)
2. Найдите ваш Web Service (например, `losbankos-bot`)
3. Скопируйте URL из раздела **"Service Details"**
   - Формат: `https://your-service-name.onrender.com`
   - Пример: `https://losbankos-bot.onrender.com`

### Шаг 2: Обновите URL в keep-alive workflow

**Вариант 1: Прямое редактирование (проще)**

1. Откройте файл `.github/workflows/keep_alive.yml`
2. Найдите строку:
   ```yaml
   RENDER_URL="${RENDER_SERVICE_URL:-https://losbankos-bot.onrender.com}"
   ```
3. Замените `losbankos-bot.onrender.com` на ваш реальный URL
4. Сохраните и закоммитьте изменения

**Вариант 2: Через GitHub Secrets (рекомендуется)**

1. Откройте GitHub репозиторий
2. Перейдите в **Settings → Secrets and variables → Actions**
3. Нажмите **"New repository secret"**
4. **Name:** `RENDER_SERVICE_URL`
5. **Value:** `https://your-service-name.onrender.com` (ваш реальный URL)
6. Сохраните

Workflow автоматически использует этот секрет, если он установлен.

### Шаг 3: Проверьте работу

1. Подождите 10-15 минут после настройки
2. Откройте **Actions** в GitHub репозитории
3. Найдите workflow **"Keep Bot Alive"**
4. Проверьте, что он запускается каждые 10 минут
5. В логах должно быть: `✅ Bot is alive! (HTTP 200)`

## Как это работает

```
GitHub Actions (каждые 10 минут)
    ↓
HTTP GET запрос к https://your-bot.onrender.com/health
    ↓
Render Web Service получает запрос
    ↓
Бот остается "живым" и не засыпает
    ↓
Telegram команды обрабатываются мгновенно
```

## Проверка health endpoint вручную

Вы можете проверить health endpoint вручную:

```bash
curl https://your-service-name.onrender.com/health
```

Должен вернуться: `Bot is running`

## Логи

В логах Render вы увидите:
```
🏥 Health check request from <IP>
```

Это означает, что keep-alive запросы доходят до бота.

## Troubleshooting

### Бот все еще засыпает

1. **Проверьте URL:** Убедитесь, что URL в workflow правильный
2. **Проверьте Actions:** Откройте GitHub Actions и убедитесь, что workflow запускается
3. **Проверьте логи:** В Render логах должны быть записи `🏥 Health check request`
4. **Проверьте интервал:** GitHub Actions может иметь задержку, но обычно запускается в течение 10-15 минут

### Workflow не запускается

1. Убедитесь, что файл `.github/workflows/keep_alive.yml` существует
2. Проверьте синтаксис YAML (должен быть валидным)
3. Убедитесь, что workflow включен в настройках репозитория

### Health endpoint не отвечает

1. Проверьте, что бот запущен на Render
2. Проверьте логи Render - должны быть записи о запуске health server
3. Убедитесь, что порт настроен правильно (Render автоматически устанавливает переменную `PORT`)

## Альтернативы

Если keep-alive через GitHub Actions не работает:

1. **Платный план Render** ($7/месяц) - бот не засыпает
2. **Background Worker** (если доступен бесплатный план)
3. **Внешний сервис keep-alive:**
   - [cron-job.org](https://cron-job.org) - бесплатный cron сервис
   - [UptimeRobot](https://uptimerobot.com) - мониторинг с keep-alive
   - [Pingdom](https://www.pingdom.com) - мониторинг с ping


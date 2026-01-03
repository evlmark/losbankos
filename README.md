# Reviews Analyzer Service

Сервис для автоматического сбора, анализа и публикации отзывов конкурентов из App Store и Google Play.

## Возможности

- 📱 Сбор отзывов из App Store и Google Play
- 🤖 Анализ отзывов с помощью LLM (OpenAI или Anthropic)
- 📊 Создание структурированных отчетов
- 📢 Автоматическая публикация в Telegram или Slack
- ⏰ Планировщик для еженедельного запуска

## Установка

1. Клонируйте репозиторий или скопируйте файлы

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл и добавьте ваши API ключи
```

4. Создайте файл конфигурации конкурентов:
```bash
cp competitors.json.example competitors.json
# Отредактируйте competitors.json и добавьте информацию о конкурентах
```

## Конфигурация

### Переменные окружения (.env)

- `LLM_PROVIDER` - провайдер LLM: `openai` или `anthropic`
- `LLM_MODEL` - модель для использования (например, `gpt-4o-mini` или `claude-3-haiku-20240307`)
- `OPENAI_API_KEY` - API ключ OpenAI (если используете OpenAI)
- `ANTHROPIC_API_KEY` - API ключ Anthropic (если используете Anthropic)
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота
- `TELEGRAM_CHAT_ID` - ID чата/канала в Telegram
- `SLACK_BOT_TOKEN` - токен Slack бота
- `SLACK_CHANNEL_ID` - ID канала в Slack
- `NOTIFICATION_METHOD` - метод уведомлений: `telegram` или `slack`
- `SCHEDULE_DAY_OF_WEEK` - день недели для запуска (например, `monday`)
- `SCHEDULE_TIME` - время запуска (например, `09:00`)

### Конфигурация конкурентов (competitors.json)

```json
{
  "competitors": [
    {
      "name": "Название приложения",
      "store_type": "appstore",
      "app_id": "1234567890",
      "country": "us"
    },
    {
      "name": "Другое приложение",
      "store_type": "googleplay",
      "app_id": "com.example.app",
      "country": "us",
      "lang": "en"
    }
  ]
}
```

**Параметры:**
- `name` - название приложения (для отображения в отчетах)
- `store_type` - тип стора: `appstore` или `googleplay`
- `app_id` - ID приложения в сторе
  - Для App Store: числовой ID (можно найти в URL приложения)
  - Для Google Play: package name (например, `com.example.app`)
- `country` - код страны (опционально, по умолчанию `us`, игнорируется если `all_countries: true`)
- `lang` - язык для Google Play (опционально, по умолчанию `en`)
- `all_countries` - если `true`, собирает отзывы из всех стран (опционально, по умолчанию `false`)

**Пример для глобальных отзывов:**
```json
{
  "name": "Global App",
  "store_type": "googleplay",
  "app_id": "com.example.global",
  "all_countries": true,
  "lang": "en"
}
```

## Использование

### Разовый запуск

```bash
python main.py
```

### Запуск планировщика

Для автоматического еженедельного запуска:

```bash
python scheduler.py
```

Планировщик будет работать в фоновом режиме и запускать анализ согласно настройкам в `.env`.

### Альтернатива: Cron (Linux/Mac)

Вы также можете использовать системный cron:

```bash
# Редактируйте crontab
crontab -e

# Добавьте строку для запуска каждый понедельник в 9:00
0 9 * * 1 cd /path/to/reviews_analyzer && python main.py
```

## Структура проекта

```
reviews_analyzer/
├── main.py                 # Главный скрипт
├── scheduler.py            # Планировщик задач
├── config.py              # Конфигурация
├── store_scrapers.py      # Модуль для сбора отзывов
├── review_analyzer.py     # Модуль для анализа отзывов
├── notifiers.py           # Модуль для отправки уведомлений
├── competitors.json       # Конфигурация конкурентов
├── .env                   # Переменные окружения
├── requirements.txt       # Зависимости
├── data/
│   ├── reviews/          # Сохраненные отзывы
│   └── outputs/          # Сгенерированные отчеты
└── logs/                 # Логи
```

## Как найти App ID

### App Store
1. Откройте приложение в App Store
2. URL будет выглядеть как: `https://apps.apple.com/app/id1234567890`
3. Число после `/id` - это App ID

### Google Play
1. Откройте приложение в Google Play
2. URL будет выглядеть как: `https://play.google.com/store/apps/details?id=com.example.app`
3. Значение параметра `id` - это package name

## Примеры использования

### Добавление нового конкурента

Отредактируйте `competitors.json` и добавьте новую запись:

```json
{
  "name": "Новый конкурент",
  "store_type": "appstore",
  "app_id": "9876543210",
  "country": "ru"
}
```

### Изменение метода уведомлений

В файле `.env` измените:
```
NOTIFICATION_METHOD=slack
```

И добавьте соответствующие токены для Slack.

## Логирование

Логи сохраняются в папке `logs/` с ротацией каждую неделю и хранением в течение 4 недель.

## Устранение неполадок

### Ошибка импорта библиотек
Убедитесь, что все зависимости установлены:
```bash
pip install -r requirements.txt
```

### Ошибка API ключей
Проверьте, что все необходимые API ключи указаны в `.env` файле.

### Ошибка при отправке в Telegram
- Убедитесь, что бот добавлен в канал/чат
- Проверьте правильность `TELEGRAM_CHAT_ID` (может быть числовым ID или username с @)

### Ошибка при отправке в Slack
- Убедитесь, что бот добавлен в канал
- Проверьте правильность `SLACK_CHANNEL_ID` (может быть ID канала или его имя)

## 🤖 Telegram бот

Бот работает в двух режимах:

1. **Интерактивный режим** - обрабатывает команды `/start` и `/help`
   - Запуск: `python run_bot.py`
   - Должен работать постоянно (на облачном сервисе)

2. **Автоматическая отправка** - отправляет новые отчеты подписчикам
   - Работает автоматически при запуске `main.py`

**Как это работает:**
- Пользователь нажимает `/start` → получает последний отчет и подписывается
- При создании нового отчета → автоматически отправляется всем подписчикам

Подробная инструкция: см. `BOT_SETUP.md`

## 🚀 Автоматический запуск и деплой

### GitHub Actions (Рекомендуется - бесплатно)

Сервис можно настроить для автоматического запуска через GitHub Actions без необходимости в собственном сервере.

#### Быстрая настройка:

1. **Создайте репозиторий на GitHub и загрузите код:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/reviews-analyzer.git
   git push -u origin main
   ```

2. **Настройте Secrets в GitHub:**
   - Перейдите: Settings → Secrets and variables → Actions
   - Добавьте необходимые secrets (см. `DEPLOYMENT.md`)

3. **Настройте Telegram бота:**
   - См. подробную инструкцию в `setup_telegram_bot.md`

4. **Проверьте расписание:**
   - Файл `.github/workflows/weekly_reviews.yml` уже настроен
   - По умолчанию: каждый понедельник в 09:00 UTC
   - Можно запустить вручную: Actions → Weekly Reviews Analysis → Run workflow

#### Подробная инструкция:
См. файл `DEPLOYMENT.md` для детальной информации о всех вариантах деплоя.

## Лицензия

MIT


# Инструкция по деплою и настройке автоматического запуска

## 🚀 Варианты деплоя

### Вариант 1: GitHub Actions (Рекомендуется - бесплатно)

GitHub Actions позволяет запускать скрипт автоматически по расписанию без необходимости в собственном сервере.

#### Шаги настройки:

1. **Создайте репозиторий на GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/reviews-analyzer.git
   git push -u origin main
   ```

2. **Настройте Secrets в GitHub**
   - Перейдите в Settings → Secrets and variables → Actions
   - Добавьте следующие secrets:
     - `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота
     - `TELEGRAM_CHAT_ID` - ID чата/канала
     - `OPENAI_API_KEY` (опционально) - для LLM саммари
     - `ANTHROPIC_API_KEY` (опционально) - альтернатива OpenAI
     - `LLM_PROVIDER` (опционально) - "openai" или "anthropic"
     - `LLM_MODEL` (опционально) - модель для использования
     - `NOTIFICATION_METHOD` - "telegram" или "slack"
     - `REVIEWS_PER_APP` (опционально) - количество отзывов (по умолчанию 100)

3. **Настройте расписание**
   - Файл `.github/workflows/weekly_reviews.yml` уже создан
   - По умолчанию запуск каждый понедельник в 09:00 UTC
   - Можно изменить в файле (формат cron)

4. **Проверьте работу**
   - Перейдите в Actions → Weekly Reviews Analysis
   - Можно запустить вручную через "Run workflow"

---

### Вариант 2: Облачные сервисы (Heroku, Railway, Render)

#### Heroku (платный после бесплатного периода)

1. Создайте `Procfile`:
   ```
   worker: python scheduler.py
   ```

2. Установите Heroku CLI и задеплойте:
   ```bash
   heroku create your-app-name
   heroku config:set TELEGRAM_BOT_TOKEN=your_token
   heroku config:set TELEGRAM_CHAT_ID=your_chat_id
   git push heroku main
   ```

#### Railway (бесплатный tier доступен)

1. Подключите GitHub репозиторий
2. Настройте переменные окружения
3. Railway автоматически определит Python проект

#### Render (бесплатный tier доступен)

1. Создайте новый Web Service
2. Подключите GitHub репозиторий
3. Настройте переменные окружения
4. Используйте команду: `python scheduler.py`

---

## 📱 Настройка Telegram бота

### Шаг 1: Создание бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/botfather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям и получите токен бота
4. Сохраните токен (например: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Шаг 2: Получение Chat ID

#### Для личного чата:
1. Напишите боту любое сообщение
2. Откройте в браузере: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Найдите `"chat":{"id":123456789}` - это ваш Chat ID

#### Для канала:
1. Добавьте бота в канал как администратора
2. Отправьте сообщение в канал
3. Откройте: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Найдите Chat ID канала (обычно отрицательное число, например `-1001234567890`)

### Шаг 3: Настройка в проекте

Для локального запуска добавьте в `.env`:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
NOTIFICATION_METHOD=telegram
```

Для GitHub Actions добавьте в Secrets (см. выше).

---

## ⚙️ Настройка расписания

### GitHub Actions (cron формат)

В файле `.github/workflows/weekly_reviews.yml`:
```yaml
schedule:
  - cron: '0 9 * * 1'  # Понедельник, 09:00 UTC
```

Формат cron: `минута час день месяц день_недели`

Примеры:
- `'0 9 * * 1'` - каждый понедельник в 09:00
- `'0 9 * * 0'` - каждое воскресенье в 09:00
- `'0 9 1 * *'` - 1-го числа каждого месяца в 09:00
- `'0 */6 * * *'` - каждые 6 часов

### Локальный планировщик (scheduler.py)

Если запускаете на своем сервере:
```bash
python scheduler.py
```

Настройте в `.env`:
```bash
SCHEDULE_DAY_OF_WEEK=monday
SCHEDULE_TIME=09:00
```

---

## 📝 Структура проекта для GitHub

Убедитесь, что в репозитории есть:
```
reviews_analyzer/
├── .github/
│   └── workflows/
│       └── weekly_reviews.yml  ← GitHub Actions workflow
├── main.py
├── scheduler.py
├── config.py
├── store_scrapers.py
├── review_analyzer.py
├── report_generator.py
├── notifiers.py
├── competitors.json
├── requirements.txt
├── README.md
└── .gitignore
```

**Важно:** Не коммитьте `.env` файл! Он уже в `.gitignore`.

---

## 🔐 Безопасность

1. **Никогда не коммитьте:**
   - `.env` файл
   - API ключи в коде
   - `competitors.json` с чувствительными данными (если есть)

2. **Используйте GitHub Secrets** для всех токенов и ключей

3. **Проверьте `.gitignore`** перед коммитом:
   ```bash
   git status
   ```

---

## ✅ Проверка работы

1. **Локально:**
   ```bash
   python main.py
   ```

2. **GitHub Actions:**
   - Перейдите в Actions
   - Запустите workflow вручную
   - Проверьте логи выполнения

3. **Telegram:**
   - После успешного выполнения должен прийти отчет в Telegram

---

## 🐛 Устранение неполадок

### Бот не отправляет сообщения
- Проверьте, что бот добавлен в канал/чат
- Проверьте правильность Chat ID
- Убедитесь, что бот имеет права на отправку сообщений

### GitHub Actions не запускается
- Проверьте синтаксис cron в workflow файле
- Убедитесь, что все secrets настроены
- Проверьте логи в Actions

### Ошибки при парсинге
- Проверьте правильность App ID в `competitors.json`
- Убедитесь, что приложения доступны в указанных странах

---

## 📚 Полезные ссылки

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Cron Expression Generator](https://crontab.guru/)


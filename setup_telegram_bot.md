# 📱 Быстрая настройка Telegram бота

## Шаг 1: Создание бота

1. Откройте Telegram
2. Найдите [@BotFather](https://t.me/botfather)
3. Отправьте команду: `/newbot`
4. Следуйте инструкциям:
   - Введите имя бота (например: "Reviews Analyzer Bot")
   - Введите username бота (должен заканчиваться на `bot`, например: `reviews_analyzer_bot`)
5. **Скопируйте токен** который даст BotFather (выглядит как: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Шаг 2: Получение Chat ID

### Вариант A: Для личного чата

1. Напишите вашему боту любое сообщение (например: "Hello")
2. Откройте в браузере (замените `YOUR_BOT_TOKEN` на ваш токен):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
3. Найдите в ответе `"chat":{"id":123456789}` - это ваш Chat ID

### Вариант B: Для канала/группы

1. Создайте канал или группу
2. Добавьте бота в канал как администратора
3. Отправьте любое сообщение в канал
4. Откройте в браузере:
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
5. Найдите Chat ID канала (обычно отрицательное число, например: `-1001234567890`)

### Вариант C: Использование специального бота

1. Найдите [@userinfobot](https://t.me/userinfobot) в Telegram
2. Напишите ему - он покажет ваш Chat ID
3. Для канала: добавьте бота в канал и отправьте сообщение, затем проверьте через getUpdates

## Шаг 3: Настройка в проекте

### Для локального запуска:

Создайте файл `.env`:
```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
NOTIFICATION_METHOD=telegram
```

### Для GitHub Actions:

1. Перейдите в ваш репозиторий на GitHub
2. Settings → Secrets and variables → Actions
3. Нажмите "New repository secret"
4. Добавьте:
   - Name: `TELEGRAM_BOT_TOKEN`, Value: ваш токен
   - Name: `TELEGRAM_CHAT_ID`, Value: ваш Chat ID
   - Name: `NOTIFICATION_METHOD`, Value: `telegram`

## Шаг 4: Тестирование

Запустите скрипт:
```bash
python main.py
```

Если все настроено правильно, отчет должен прийти в Telegram!

## 🔍 Проверка токена и Chat ID

Если что-то не работает, проверьте:

1. **Токен правильный?**
   ```bash
   curl https://api.telegram.org/botYOUR_BOT_TOKEN/getMe
   ```
   Должен вернуть информацию о боте

2. **Chat ID правильный?**
   ```bash
   curl https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
   Покажет последние сообщения и Chat ID

## ⚠️ Важные замечания

- **Никогда не публикуйте токен бота!** Он должен быть только в Secrets или .env
- Chat ID для канала обычно отрицательный
- Бот должен быть добавлен в канал/группу как администратор (для каналов)
- Для личных чатов бот должен быть запущен (написать ему сообщение)


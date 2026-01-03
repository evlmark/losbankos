# 🚀 Настройка GitHub репозитория

## Шаг 1: Создайте репозиторий на GitHub

1. Перейдите на https://github.com/new
2. Название репозитория: `reviews-analyzer` (или любое другое)
3. Описание: `Weekly competitor reviews analysis service with Telegram bot`
4. Выберите **Private** или **Public**
5. **НЕ** добавляйте README, .gitignore или лицензию (они уже есть)
6. Нажмите **Create repository**

## Шаг 2: Подключите локальный репозиторий

После создания репозитория GitHub покажет инструкции. Используйте команды ниже:

```bash
cd "/Users/markevlampiev/Downloads/Cursor Files/Competitors/reviews_analyzer"

# Добавить все файлы
git add .

# Создать первый коммит
git commit -m "Initial commit: Reviews analyzer with Telegram bot"

# Подключить к GitHub (замените YOUR_USERNAME на evlmark)
git remote add origin https://github.com/evlmark/reviews-analyzer.git

# Отправить код на GitHub
git branch -M main
git push -u origin main
```

## Шаг 3: Настройте GitHub Secrets для автоматизации

После создания репозитория:

1. Перейдите в **Settings** → **Secrets and variables** → **Actions**
2. Добавьте следующие секреты:
   - `TELEGRAM_BOT_TOKEN` = `8109257733:AAETqbBqvf5AfE3pl8SqjSAa7NkEvv2ifKs`
   - `OPENAI_API_KEY` (опционально, если используете LLM)
   - `ANTHROPIC_API_KEY` (опционально, если используете Anthropic)

## Готово! 

После этого:
- ✅ Код будет на GitHub
- ✅ GitHub Actions будет автоматически запускаться каждую неделю
- ✅ Отчеты будут отправляться в Telegram бот


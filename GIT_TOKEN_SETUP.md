# 🔑 Настройка GIT_TOKEN для автоматической синхронизации подписчиков

## Зачем нужен GIT_TOKEN?

Когда пользователь подписывается на бота через `/start`, его chat_id сохраняется в файл `telegram_subscribers.json`. Чтобы этот файл автоматически синхронизировался с GitHub репозиторием, бот должен иметь возможность делать `git push`.

**GIT_TOKEN** - это GitHub Personal Access Token, который дает боту права на запись в репозиторий.

---

## 📝 Как создать GIT_TOKEN

### Шаг 1: Создайте токен на GitHub

1. Перейдите: https://github.com/settings/tokens
2. Нажмите **"Generate new token (classic)"**
3. Заполните форму:
   - **Note:** `Render Bot Sync` (или любое другое описание)
   - **Expiration:** Выберите срок действия (рекомендуется: 90 days или No expiration)
   - **Select scopes:** Выберите `repo` (полный доступ к репозиториям)
4. Нажмите **"Generate token"**
5. **⚠️ ВАЖНО:** Скопируйте токен сразу! Он больше не будет показан.

### Шаг 2: Добавьте токен в Render

1. Откройте Render Dashboard
2. Найдите ваш Web Service (бот)
3. Перейдите в раздел **Environment**
4. Нажмите **"Add Environment Variable"**
5. Добавьте:
   - **Key:** `GIT_TOKEN`
   - **Value:** вставьте скопированный токен
6. Нажмите **"Save Changes"**
7. Render автоматически перезапустит сервис

---

## ✅ Проверка работы

После добавления GIT_TOKEN:

1. **Откройте бота в Telegram**
2. **Отправьте `/start`** (если еще не подписаны)
3. **Отправьте `/subscribers`**
4. **Проверьте статус:**
   - Должно быть: `✅ GIT_TOKEN настроен - автоматическая синхронизация включена`
   - Если видите: `⚠️ GIT_TOKEN не настроен` - проверьте, что токен добавлен в Render

5. **Проверьте GitHub:**
   - Перейдите в репозиторий: https://github.com/evlmark/losbankos
   - Откройте файл `telegram_subscribers.json`
   - Там должен быть ваш chat_id

---

## 🔍 Логи в Render

После подписки через `/start`, проверьте логи в Render:

**Успешная синхронизация:**
```
✅ Subscriber file committed to git successfully
Pushing to GitHub using GIT_TOKEN...
✅ Subscriber file pushed to GitHub successfully
```

**Если GIT_TOKEN не настроен:**
```
⚠️  Git push failed (GIT_TOKEN not set): ...
⚠️  Set GIT_TOKEN in Render Environment Variables to enable auto-sync
```

---

## ⚠️ Важно

- **GIT_TOKEN должен иметь права `repo`** - это дает полный доступ к репозиториям
- **Не коммитьте токен в код!** Он должен быть только в Render Environment Variables
- **Токен можно отозвать** в любой момент: https://github.com/settings/tokens
- **Если токен истек** - создайте новый и обновите в Render

---

## 🆘 Если синхронизация не работает

1. **Проверьте токен:**
   - Убедитесь, что токен имеет права `repo`
   - Проверьте, что токен не истек

2. **Проверьте Render:**
   - Убедитесь, что `GIT_TOKEN` добавлен в Environment Variables
   - Проверьте, что сервис перезапустился после добавления

3. **Проверьте логи:**
   - В Render Dashboard → Logs
   - Найдите сообщения о git push
   - Если есть ошибки - скопируйте их

4. **Проверьте репозиторий:**
   - Убедитесь, что remote URL правильный (HTTPS)
   - Проверьте, что branch называется `main` (не `master`)

---

## 📚 Связанные документы

- [RENDER_WEBSERVICE_SETUP.md](RENDER_WEBSERVICE_SETUP.md) - полная инструкция по настройке бота на Render
- [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md) - настройка секретов для GitHub Actions


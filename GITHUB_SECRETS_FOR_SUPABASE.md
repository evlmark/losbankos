# 🔐 GitHub Secrets для Supabase интеграции

## Секреты, которые нужно добавить

Перейдите: https://github.com/evlmark/losbankos/settings/secrets/actions

### 1. SUPABASE_ACCESS_TOKEN (ОБЯЗАТЕЛЬНО)

**Как получить:**
1. Откройте: https://supabase.com/dashboard/account/tokens
2. Нажмите **"Generate new token"**
3. Дайте имя токену (например, "GitHub Actions Migrations")
4. Скопируйте токен (он показывается только один раз!)

**Добавить в GitHub:**
- **Name:** `SUPABASE_ACCESS_TOKEN`
- **Value:** ваш токен из Supabase
- **Описание:** Токен для доступа к Supabase API через CLI

---

### 2. SUPABASE_URL (если еще нет)

**Значение:**
```
https://vqqdmdffssmobsofbnqf.supabase.co
```

**Добавить в GitHub:**
- **Name:** `SUPABASE_URL`
- **Value:** `https://vqqdmdffssmobsofbnqf.supabase.co`
- **Описание:** URL вашего Supabase проекта

---

### 3. SUPABASE_DB_PASSWORD (ОБЯЗАТЕЛЬНО)

**Значение:**
```
xafsur-3voqvi-mokgIw
```

**Добавить в GitHub:**
- **Name:** `SUPABASE_DB_PASSWORD`
- **Value:** `xafsur-3voqvi-mokgIw`
- **Описание:** Пароль базы данных Supabase

---

## 📋 Быстрая инструкция

1. **Откройте:** https://github.com/evlmark/losbankos/settings/secrets/actions
2. **Для каждого секрета:**
   - Нажмите **"New repository secret"**
   - Введите Name и Value
   - Нажмите **"Add secret"**

3. **Проверьте, что добавлены:**
   - ✅ `SUPABASE_ACCESS_TOKEN`
   - ✅ `SUPABASE_URL`
   - ✅ `SUPABASE_DB_PASSWORD`

---

## ⚠️ Важно

- **Никогда не коммитьте** эти значения в код
- Храните их только в GitHub Secrets
- `SUPABASE_ACCESS_TOKEN` можно перегенерировать, если потеряли
- `SUPABASE_DB_PASSWORD` нельзя восстановить - сохраните его надежно

---

## ✅ После добавления секретов

1. Workflow автоматически запустится при изменении файлов в `supabase/migrations/`
2. Или запустите вручную: Actions → Supabase Migrations → Run workflow


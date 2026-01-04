# 🔍 Как найти SUPABASE_DB_URL (Connection String)

## Пошаговая инструкция

### Шаг 1: Откройте Settings

1. В левом меню Supabase Dashboard найдите иконку **⚙️ Settings** (шестеренка)
2. Она находится в самом низу левого меню
3. Нажмите на нее

### Шаг 2: Выберите Database

1. В открывшемся меню Settings выберите **Database**
2. Это второй пункт в списке (после API)

### Шаг 3: Найдите Connection string

1. Прокрутите страницу вниз
2. Найдите раздел **"Connection string"** или **"Connection pooling"**
3. Вы увидите несколько вкладок: **URI**, **JDBC**, **Golang**, и т.д.

### Шаг 4: Скопируйте URI

1. Нажмите на вкладку **URI**
2. Вы увидите строку вида:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
   или
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

### Шаг 5: Замените пароль

1. В строке найдите `[YOUR-PASSWORD]`
2. Замените его на пароль, который вы создали при создании проекта Supabase
3. **Важно:** Это тот пароль, который вы вводили при создании проекта (не API key!)

### Пример:

**До замены:**
```
postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijklmnop.supabase.co:5432/postgres
```

**После замены (если пароль `mypassword123`):**
```
postgresql://postgres:mypassword123@db.abcdefghijklmnop.supabase.co:5432/postgres
```

---

## Альтернативный способ (если не видите Connection string)

### Вариант 1: Connection info

1. В Settings → Database найдите раздел **"Connection info"** или **"Database settings"**
2. Там будут указаны:
   - **Host:** `db.xxxxx.supabase.co` (или похожее)
   - **Database name:** `postgres`
   - **Port:** `5432`
   - **User:** `postgres`
   - **Password:** ваш пароль (который вы создали при создании проекта)

3. Соберите строку вручную по формуле:
   ```
   postgresql://[USER]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]
   ```

**Пример:**
- Host: `db.abcdefghijklmnop.supabase.co`
- Port: `5432`
- User: `postgres`
- Password: `mypassword123`
- Database: `postgres`

**Результат:**
```
postgresql://postgres:mypassword123@db.abcdefghijklmnop.supabase.co:5432/postgres
```

### Вариант 2: Если забыли пароль

Если вы забыли пароль базы данных:

1. **Попробуйте найти его:**
   - Проверьте, сохранили ли вы его при создании проекта
   - Проверьте менеджер паролей (если использовали)

2. **Если не можете найти:**
   - К сожалению, пароль базы данных нельзя восстановить
   - Нужно будет создать новый проект или использовать только REST API (без прямого подключения к PostgreSQL)

3. **Для автоматического скрипта:**
   - Если у вас нет `SUPABASE_DB_URL`, скрипт `setup_supabase.py` создаст SQL файл
   - Вы сможете выполнить его вручную в SQL Editor

---

## Где использовать SUPABASE_DB_URL

### В `.env` файле:
```bash
SUPABASE_DB_URL=postgresql://postgres:mypassword123@db.abcdefghijklmnop.supabase.co:5432/postgres
```

### В GitHub Secrets:
- Name: `SUPABASE_DB_URL`
- Value: ваша connection string

### В Render Environment Variables:
- Key: `SUPABASE_DB_URL`
- Value: ваша connection string

---

## ⚠️ Важно о безопасности

1. **Никогда не коммитьте** `SUPABASE_DB_URL` в код
2. Храните его только в:
   - `.env` файле (который в `.gitignore`)
   - GitHub Secrets
   - Render Environment Variables
3. Если случайно закоммитили - немедленно смените пароль базы данных

---

## 🆘 Если все еще не можете найти

1. **Проверьте, что вы в правильном проекте:**
   - Вверху страницы должно быть название вашего проекта
   - Убедитесь, что это тот проект, который вы создали

2. **Попробуйте другой способ:**
   - Используйте только `SUPABASE_URL` и `SUPABASE_KEY`
   - Скрипт создаст SQL файл для ручного выполнения
   - Выполните `supabase_setup.sql` в SQL Editor

3. **Свяжитесь со мной:**
   - Пришлите скриншот страницы Settings → Database
   - Я помогу найти нужную информацию


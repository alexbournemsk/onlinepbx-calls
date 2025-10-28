# Настройка Supabase для OnlinePBX Calls

Это руководство поможет вам настроить приложение для использования Supabase PostgreSQL вместо локального SQLite.

## Преимущества Supabase

✅ **Данные не теряются при обновлении** - БД работает отдельно от контейнера  
✅ **Надежность** - автоматические бэкапы и высокая доступность  
✅ **Масштабируемость** - подходит для production  
✅ **Бесплатный план** - до 500 МБ базы данных  

## Шаг 1: Создание проекта в Supabase

1. Перейдите на https://supabase.com/
2. Зарегистрируйтесь или войдите в аккаунт
3. Нажмите **"New Project"**
4. Заполните данные проекта:
   - **Name**: `onlinepbx-calls` (или любое другое имя)
   - **Database Password**: придумайте надежный пароль и **сохраните его**
   - **Region**: выберите ближайший регион (например, Frankfurt для Европы)
5. Нажмите **"Create new project"**
6. Дождитесь создания проекта (1-2 минуты)

## Шаг 2: Получение строки подключения

1. В панели Supabase перейдите в **Settings** → **Database**
2. Найдите раздел **"Connection string"**
3. Выберите режим **"URI"**
4. Скопируйте строку подключения, она выглядит так:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
   ```
5. **Замените `[YOUR-PASSWORD]`** на пароль, который вы указали при создании проекта

**Пример строки подключения:**
```
postgresql://postgres:MySecurePassword123@db.abcdefghijklmnop.supabase.co:5432/postgres
```

## Шаг 3: Настройка приложения

### Вариант A: Docker Compose

1. Откройте файл `docker-compose.yml`
2. Найдите закомментированную строку с `DATABASE_URL`
3. Раскомментируйте и вставьте вашу строку подключения:

```yaml
environment:
  - FLASK_ENV=production
  - DOMAIN=guitardo.onpbx.ru
  - AUTH_KEY=qJqxwdH7ZccfzS1F3UoStTRJSZHvfWTR5Dt4kiv7Og
  
  # Supabase PostgreSQL
  - DATABASE_URL=postgresql://postgres:MySecurePassword123@db.abcdefghijklmnop.supabase.co:5432/postgres
```

4. Удалите или закомментируйте строку `DB_FILE` (она не нужна для PostgreSQL)

5. Пересоздайте контейнер:
```bash
docker-compose down
docker-compose up -d --build
```

### Вариант B: Переменные окружения на сервере

Если вы разворачиваете на Render, Heroku или другом PaaS:

1. Добавьте переменную окружения `DATABASE_URL` со строкой подключения к Supabase
2. Удалите переменную `DB_FILE` (если она есть)
3. Выполните деплой

**Для Render.com:**
- Dashboard → Service → Environment
- Add Environment Variable:
  - Key: `DATABASE_URL`
  - Value: `postgresql://postgres:MySecurePassword123@db.xxx.supabase.co:5432/postgres`

**Для Heroku:**
```bash
heroku config:set DATABASE_URL="postgresql://postgres:MySecurePassword123@db.xxx.supabase.co:5432/postgres"
```

## Шаг 4: Проверка работы

1. Перезапустите приложение
2. Откройте приложение в браузере
3. Проверьте логи:
   ```bash
   docker-compose logs -f pbx-app
   ```
   
   Вы должны увидеть:
   ```
   INFO:root:Using PostgreSQL (Supabase)
   INFO:root:PostgreSQL connection pool created successfully
   INFO:root:Database initialized successfully
   ```

4. Попробуйте получить статистику - данные должны сохраниться в Supabase

## Шаг 5: Миграция данных из SQLite (опционально)

Если у вас уже есть данные в локальной SQLite базе, вы можете их мигрировать:

### Экспорт из SQLite

```bash
# Подключитесь к контейнеру
docker exec -it onlinepbx_calls-pbx-app-1 bash

# Установите sqlite3 (если нет)
apt-get update && apt-get install -y sqlite3

# Экспортируйте данные
sqlite3 calls_history.db .dump > dump.sql
exit
```

### Импорт в Supabase

1. В панели Supabase перейдите в **SQL Editor**
2. Создайте новый запрос
3. Скопируйте содержимое `dump.sql` (только INSERT команды)
4. Адаптируйте SQL-синтаксис для PostgreSQL (если требуется)
5. Выполните запрос

**Примечание:** SQLite и PostgreSQL имеют небольшие различия в синтаксисе, возможно потребуется адаптация.

## Мониторинг и управление

### Просмотр данных в Supabase

1. Перейдите в **Table Editor** в панели Supabase
2. Выберите таблицу (`calls`, `daily_stats`, `trunks`, `cache_requests`)
3. Просматривайте и редактируйте данные

### Создание бэкапов

В настройках проекта Supabase:
- Перейдите в **Settings** → **Database**
- Настройте автоматические бэкапы
- На бесплатном плане: point-in-time recovery не доступен

### SQL Запросы

Используйте **SQL Editor** для выполнения произвольных SQL-запросов:

```sql
-- Проверка количества звонков
SELECT COUNT(*) FROM calls;

-- Статистика по дням
SELECT date, SUM(total_calls) as total 
FROM daily_stats 
GROUP BY date 
ORDER BY date DESC;

-- Очистка старых данных (старше 90 дней)
DELETE FROM calls 
WHERE start_stamp < EXTRACT(EPOCH FROM NOW() - INTERVAL '90 days');
```

## Возврат к SQLite (если нужно)

1. В `docker-compose.yml` закомментируйте `DATABASE_URL`
2. Раскомментируйте `DB_FILE=/app/data/calls_history.db`
3. Убедитесь, что volume `./data:/app/data` подключен
4. Пересоздайте контейнер:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## Устранение проблем

### Ошибка подключения

```
ERROR:root:Failed to create PostgreSQL connection pool
```

**Решение:**
- Проверьте правильность строки подключения
- Убедитесь, что пароль не содержит специальных символов (или они экранированы)
- Проверьте, что IP-адрес вашего сервера не заблокирован в Supabase

### Ошибка аутентификации

```
psycopg2.OperationalError: FATAL: password authentication failed
```

**Решение:**
- Проверьте пароль в строке подключения
- Убедитесь, что используете правильный пароль проекта

### Медленные запросы

**Решение:**
- Проверьте индексы в таблицах (они создаются автоматически при init_db)
- Рассмотрите обновление плана Supabase для лучшей производительности

## Безопасность

⚠️ **Важно:**

1. **Никогда не коммитьте** `docker-compose.yml` с реальной строкой подключения в публичный репозиторий
2. Используйте `.env` файл для хранения секретов:
   ```bash
   # .env
   DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
   ```
   
   И ссылайтесь на него в docker-compose.yml:
   ```yaml
   environment:
     - DATABASE_URL=${DATABASE_URL}
   ```

3. Добавьте `.env` в `.gitignore`
4. Регулярно меняйте пароль БД
5. Используйте Row Level Security (RLS) в Supabase для дополнительной защиты

## Полезные ссылки

- [Документация Supabase](https://supabase.com/docs)
- [PostgreSQL документация](https://www.postgresql.org/docs/)
- [psycopg2 документация](https://www.psycopg.org/docs/)

## Поддержка

Если у вас возникли проблемы:
1. Проверьте логи приложения
2. Проверьте логи Supabase в панели управления
3. Убедитесь, что все переменные окружения установлены правильно


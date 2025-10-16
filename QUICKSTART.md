# 🚀 Быстрый деплой в интернет за 5 минут

## Шаг 1: Подготовка кода

Ваш код готов! Файлы созданы:
- ✅ `Dockerfile` - для контейнеризации
- ✅ `docker-compose.yml` - для локального запуска
- ✅ `Procfile` - для Heroku/Railway
- ✅ `render.yaml` - для Render.com
- ✅ `.gitignore` - защита секретных данных
- ✅ `config.py` - поддержка переменных окружения

---

## Шаг 2: Загрузка на GitHub

### Если у вас УЖЕ есть Git репозиторий:
```powershell
cd C:\projects\onlinepbx_calls
git add .
git commit -m "Подготовка к деплою"
git push
```

### Если Git репозитория НЕТ:

**2.1. Инициализируйте Git:**
```powershell
cd C:\projects\onlinepbx_calls
git init
git add .
git commit -m "Первый коммит"
```

**2.2. Создайте репозиторий на GitHub:**
- Зайдите на https://github.com/
- Нажмите "New repository" (зеленая кнопка)
- Название: `onlinepbx-calls` (или любое другое)
- НЕ добавляйте README, .gitignore или лицензию
- Нажмите "Create repository"

**2.3. Загрузите код:**
```powershell
git remote add origin https://github.com/ваш-username/onlinepbx-calls.git
git branch -M main
git push -u origin main
```

---

## Шаг 3: Выберите платформу для деплоя

### 🌟 ВАРИАНТ A: Railway.app (РЕКОМЕНДУЮ!)

**Почему:** Проще всего, бесплатно, быстро

1. Зайдите на https://railway.app/
2. Нажмите "Login" → войдите через GitHub
3. Нажмите "New Project" → "Deploy from GitHub repo"
4. Выберите ваш репозиторий `onlinepbx-calls`
5. Railway автоматически определит Dockerfile и задеплоит!
6. Нажмите "Settings" → "Generate Domain" для получения публичного URL
7. **ГОТОВО!** Приложение доступно по адресу типа: `https://ваш-проект.up.railway.app`

**Важно:** Добавьте переменные окружения в Railway:
- Перейдите в "Variables"
- Добавьте:
  - `DOMAIN` = `guitardo.onpbx.ru`
  - `AUTH_KEY` = `qJqxwdH7ZccfzS1F3UoStTRJSZHvfWTR5Dt4kiv7Og`

---

### 🎨 ВАРИАНТ B: Render.com

**Почему:** Тоже просто, бесплатно, но засыпает после 15 мин

1. Зайдите на https://render.com/
2. Войдите через GitHub
3. Нажмите "New +" → "Web Service"
4. Подключите GitHub репозиторий `onlinepbx-calls`
5. Render автоматически определит Docker
6. В секции "Environment" добавьте переменные:
   - `DOMAIN` = `guitardo.onpbx.ru`
   - `AUTH_KEY` = `qJqxwdH7ZccfzS1F3UoStTRJSZHvfWTR5Dt4kiv7Og`
7. Нажмите "Create Web Service"
8. **ГОТОВО!** Приложение доступно: `https://ваш-проект.onrender.com`

**Минус:** Засыпает после 15 минут неактивности (первая загрузка ~30 сек)

---

### 🐍 ВАРИАНТ C: PythonAnywhere.com

**Почему:** Всегда активно, но настройка сложнее

1. Зайдите на https://www.pythonanywhere.com/
2. Создайте бесплатный аккаунт
3. Откройте Bash консоль
4. Выполните команды:

```bash
# Клонируем репозиторий
git clone https://github.com/ваш-username/onlinepbx-calls.git
cd onlinepbx-calls

# Создаем виртуальное окружение
mkvirtualenv --python=/usr/bin/python3.10 pbx-env
pip install -r requirements.txt
```

5. Перейдите во вкладку "Web" → "Add a new web app"
6. Выберите "Manual configuration" → Python 3.10
7. В разделе "Code":
   - Source code: `/home/ваш-username/onlinepbx-calls`
   - Working directory: `/home/ваш-username/onlinepbx-calls`
8. В разделе "Virtualenv":
   - Путь: `/home/ваш-username/.virtualenvs/pbx-env`
9. Нажмите на ссылку "WSGI configuration file" и замените содержимое:

```python
import sys
import os

path = '/home/ваш-username/onlinepbx-calls'
if path not in sys.path:
    sys.path.append(path)

# Устанавливаем переменные окружения
os.environ['DOMAIN'] = 'guitardo.onpbx.ru'
os.environ['AUTH_KEY'] = 'qJqxwdH7ZccfzS1F3UoStTRJSZHvfWTR5Dt4kiv7Og'

from wsgi import app as application
```

10. Нажмите "Reload" (зеленая кнопка)
11. **ГОТОВО!** Приложение: `https://ваш-username.pythonanywhere.com`

---

## Шаг 4: Проверка работы

1. Откройте URL вашего приложения в браузере
2. Должна открыться главная страница с таблицей звонков
3. Проверьте другие страницы: `/stats`, `/trunks`

---

## 🎯 Мой совет для новичка:

**Используйте Railway.app** - это самый простой вариант:
1. Загрузили код на GitHub
2. Подключили к Railway
3. Получили рабочий сайт

Всё! 5 минут и готово! 🎉

---

## ⚠️ Важные замечания:

1. **База данных будет пустой** - она создается заново при каждом деплое
2. **Файл pbx_api_key.json не загружается** - он в .gitignore для безопасности
3. **Логирование** - смотрите логи на платформе хостинга, не в файлах

---

## 🆘 Проблемы?

### "Git не установлен"
Скачайте: https://git-scm.com/download/win

### "GitHub не принимает пароль"
Используйте Personal Access Token:
- Зайдите на GitHub.com → Settings → Developer settings → Personal access tokens
- Generate new token → выберите "repo" → создайте токен
- Используйте токен вместо пароля

### "Приложение не запускается"
Проверьте логи на платформе:
- Railway: вкладка "Deployments" → "View Logs"
- Render: вкладка "Logs"
- PythonAnywhere: вкладка "Web" → "Log files"

---

## 📖 Полная документация

См. файл `DEPLOY_INTERNET.md` для подробностей.


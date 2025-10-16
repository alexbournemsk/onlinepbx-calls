# 🌍 Деплой приложения в интернет

## Варианты для новичков (от простого к сложному)

---

## ⭐ Вариант 1: Railway.app (САМЫЙ ПРОСТОЙ!)

**Бесплатно:** 500 часов работы в месяц  
**Время деплоя:** 5 минут  
**Сложность:** ⭐ (очень легко)

### Шаги:

1. **Создайте аккаунт:**
   - Зайдите на https://railway.app/
   - Нажмите "Start a New Project"
   - Войдите через GitHub

2. **Загрузите код на GitHub:**
   - Если у вас нет Git репозитория, создайте его:
   ```powershell
   cd C:\projects\onlinepbx_calls
   git init
   git add .
   git commit -m "Initial commit"
   ```
   - Создайте репозиторий на GitHub.com
   - Загрузите код:
   ```powershell
   git remote add origin https://github.com/ваш-username/ваш-репозиторий.git
   git push -u origin main
   ```

3. **Деплой на Railway:**
   - В Railway нажмите "Deploy from GitHub repo"
   - Выберите ваш репозиторий
   - Railway автоматически определит Dockerfile и задеплоит!
   - Получите публичный URL (например: https://ваше-приложение.up.railway.app)

4. **Готово!** Приложение работает в интернете 🎉

**Важно:** Файлы `calls_history.db` и `pbx_api_key.json` не будут загружены в Git (они в .gitignore). База данных будет создана заново при запуске.

---

## 🚀 Вариант 2: Render.com

**Бесплатно:** Да, но засыпает после 15 минут неактивности  
**Время деплоя:** 5 минут  
**Сложность:** ⭐ (очень легко)

### Шаги:

1. **Создайте аккаунт:**
   - Зайдите на https://render.com/
   - Войдите через GitHub

2. **Загрузите код на GitHub** (см. выше)

3. **Деплой:**
   - Нажмите "New +" → "Web Service"
   - Подключите ваш GitHub репозиторий
   - Render автоматически определит Docker
   - Нажмите "Create Web Service"
   - Получите URL: https://ваше-приложение.onrender.com

4. **Готово!** 🎉

**Минус:** Приложение "засыпает" после 15 минут без запросов. Первый запрос после сна загружается ~30 секунд.

---

## 🐍 Вариант 3: PythonAnywhere.com

**Бесплатно:** Да, всегда работает  
**Время деплоя:** 10 минут  
**Сложность:** ⭐⭐ (средне)

### Шаги:

1. **Создайте аккаунт:**
   - Зайдите на https://www.pythonanywhere.com/
   - Создайте бесплатный аккаунт

2. **Загрузите код:**
   - Откройте Bash консоль в PythonAnywhere
   - Клонируйте репозиторий:
   ```bash
   git clone https://github.com/ваш-username/ваш-репозиторий.git
   cd ваш-репозиторий
   ```

3. **Создайте виртуальное окружение:**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 pbx-env
   pip install -r requirements.txt
   ```

4. **Настройте Web App:**
   - Перейдите во вкладку "Web"
   - Нажмите "Add a new web app"
   - Выберите "Manual configuration" → Python 3.10
   - В разделе "Code" укажите:
     - Source code: `/home/ваш-username/ваш-репозиторий`
     - WSGI file: создайте файл со следующим содержимым:

   ```python
   import sys
   path = '/home/ваш-username/ваш-репозиторий'
   if path not in sys.path:
       sys.path.append(path)
   
   from wsgi import app as application
   ```

5. **Перезапустите Web App**
   - Нажмите зеленую кнопку "Reload"
   - Ваше приложение доступно: https://ваш-username.pythonanywhere.com

---

## 🖥️ Вариант 4: VPS (DigitalOcean, Timeweb, Selectel)

**Стоимость:** ~$5-10/месяц  
**Время деплоя:** 30 минут  
**Сложность:** ⭐⭐⭐⭐ (сложно)

### Это для опытных пользователей:

1. **Купите VPS:**
   - DigitalOcean: https://digitalocean.com (от $6/мес)
   - Timeweb: https://timeweb.cloud (от 150₽/мес)
   - Selectel: https://selectel.ru (от 150₽/мес)

2. **Подключитесь по SSH:**
   ```bash
   ssh root@ваш-ip-адрес
   ```

3. **Установите Docker:**
   ```bash
   curl -fsSL https://get.docker.com | sh
   apt install docker-compose -y
   ```

4. **Загрузите код:**
   ```bash
   git clone https://github.com/ваш-username/ваш-репозиторий.git
   cd ваш-репозиторий
   ```

5. **Запустите:**
   ```bash
   docker-compose up -d --build
   ```

6. **Настройте домен (опционально):**
   - Купите домен на reg.ru, nic.ru или другом регистраторе
   - Добавьте A-запись, указывающую на IP вашего VPS
   - Установите Nginx и настройте прокси на порт 8000

---

## 🎯 Какой вариант выбрать?

### Для новичка:
**✅ Railway.app** - самый простой, всё автоматически

### Для тестирования:
**✅ Render.com** - бесплатно, но засыпает

### Для постоянной работы (бесплатно):
**✅ PythonAnywhere** - всегда активно, но медленнее

### Для профессионального использования:
**✅ VPS** - полный контроль, но нужны навыки

---

## ⚠️ Важные замечания:

1. **База данных:** 
   - Текущая SQLite база (`calls_history.db`) не подходит для облачных платформ (она пересоздается при каждом деплое)
   - Для продакшена рекомендуется PostgreSQL или MySQL
   - Или используйте облачную SQLite (например, Turso)

2. **Файлы конфигурации:**
   - Не загружайте в Git файлы с ключами API
   - Используйте переменные окружения на платформе хостинга

3. **Логи:**
   - На облачных платформах логи нужно смотреть через их интерфейс
   - Не используйте файлы для логов

---

## 🔧 Переменные окружения

На платформах хостинга установите следующие переменные:

```
FLASK_ENV=production
DOMAIN=guitardo.onpbx.ru
AUTH_KEY=ваш-ключ-api
```

Измените `config.py` для чтения из переменных окружения:

```python
import os

DOMAIN = os.getenv('DOMAIN', 'guitardo.onpbx.ru')
AUTH_KEY = os.getenv('AUTH_KEY', 'qJqxwdH7ZccfzS1F3UoStTRJSZHvfWTR5Dt4kiv7Og')
API_URL = f'https://api2.onlinepbx.ru/{DOMAIN}/mongo_history/search.json'
AUTH_URL = f'https://api2.onlinepbx.ru/{DOMAIN}/auth.json'
```

---

## 📞 Нужна помощь?

Если что-то не получается:
1. Проверьте логи на платформе хостинга
2. Убедитесь, что все зависимости установлены
3. Проверьте переменные окружения


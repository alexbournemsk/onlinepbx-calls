# 🚀 Деплой на Timeweb Cloud - Пошаговая инструкция

## Шаг 1: Создание сервера

1. **Войдите в панель Timeweb:** https://timeweb.cloud/my/
2. **Перейдите:** "Облачные серверы" → "Создать сервер"
3. **Выберите конфигурацию:**
   - **Операционная система:** Ubuntu 22.04 LTS
   - **Тариф:** Самый дешевый (S1 - 1 CPU, 1 GB RAM) - достаточно для вашего приложения
   - **Регион:** Москва (или любой в РФ)
   - **SSH-ключ:** пока пропустите (будете использовать пароль)
4. **Нажмите:** "Заказать" или "Создать"
5. **Дождитесь создания сервера** (~2-3 минуты)
6. **Сохраните данные:**
   - IP-адрес сервера (например: 123.45.67.89)
   - Пароль root (придет на email или в панели)

---

## Шаг 2: Подключение к серверу

### Вариант А: Через веб-консоль Timeweb (проще для новичков)
1. В панели Timeweb найдите ваш сервер
2. Нажмите кнопку "Консоль" или "VNC"
3. Войдите:
   - login: `root`
   - password: (пароль из панели)

### Вариант Б: Через SSH с вашего компьютера
```powershell
ssh root@ВАШ-IP-АДРЕС
# Введите пароль
```

---

## Шаг 3: Установка Docker на сервере

После подключения выполните команды по порядку:

```bash
# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Устанавливаем Docker Compose
apt install docker-compose -y

# Проверяем установку
docker --version
docker-compose --version
```

---

## Шаг 4: Загрузка вашего приложения

```bash
# Устанавливаем Git
apt install git -y

# Клонируем ваш репозиторий
cd /opt
git clone https://github.com/alexbournemsk/onlinepbx-calls.git
cd onlinepbx-calls

# Проверяем файлы
ls -la
```

---

## Шаг 5: Создание необходимых файлов

### 5.1. Создаем директорию для логов
```bash
mkdir -p logs
```

### 5.2. Создаем файл с ключами API
```bash
nano pbx_api_key.json
```

Вставьте (если у вас есть ключ API, иначе оставьте пустым):
```json
{}
```

Сохраните: `Ctrl+X`, затем `Y`, затем `Enter`

---

## Шаг 6: Запуск приложения

```bash
# Собираем и запускаем Docker контейнер
docker-compose up -d --build

# Проверяем статус
docker-compose ps

# Смотрим логи
docker-compose logs -f
```

Если всё хорошо, вы увидите, что контейнер запущен!

---

## Шаг 7: Настройка файрвола

Откройте порт 8000 для доступа из интернета:

```bash
# Установка UFW (если не установлен)
apt install ufw -y

# Разрешаем SSH (важно, чтобы не потерять доступ!)
ufw allow 22/tcp

# Разрешаем порт приложения
ufw allow 8000/tcp

# Включаем файрвол
ufw --force enable

# Проверяем статус
ufw status
```

**⚠️ ВАЖНО в Timeweb:**
Также нужно открыть порт в панели Timeweb:
1. Перейдите в настройки вашего сервера
2. Найдите раздел "Файрвол" или "Firewall"
3. Добавьте правило: TCP порт 8000 → разрешить
4. Сохраните

---

## Шаг 8: Проверка работы

Откройте в браузере:
```
http://ВАШ-IP-АДРЕС:8000
```

Например: `http://123.45.67.89:8000`

**Должна открыться ваша страница с таблицей звонков!** 🎉

---

## Шаг 9 (Опционально): Подключение домена

Если у вас есть домен (например, `myapp.ru`):

### 9.1. Настройка DNS
В вашем регистраторе доменов (например, reg.ru) добавьте A-запись:
```
A    @    ВАШ-IP-АДРЕС
```

### 9.2. Установка Nginx
```bash
apt install nginx -y

# Создаем конфигурацию
nano /etc/nginx/sites-available/pbx
```

Вставьте:
```nginx
server {
    listen 80;
    server_name ваш-домен.ru;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Сохраните и активируйте:
```bash
ln -s /etc/nginx/sites-available/pbx /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Открываем порт 80
ufw allow 80/tcp
```

Теперь приложение доступно по адресу: `http://ваш-домен.ru`

### 9.3. SSL сертификат (HTTPS)
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d ваш-домен.ru
```

Теперь: `https://ваш-домен.ru` 🔒

---

## 📋 Полезные команды

```bash
# Просмотр логов
docker-compose logs -f

# Перезапуск приложения
docker-compose restart

# Остановка
docker-compose down

# Обновление кода
cd /opt/onlinepbx-calls
git pull
docker-compose down
docker-compose up -d --build

# Проверка использования ресурсов
docker stats

# Проверка портов
netstat -tlnp | grep 8000
```

---

## 🆘 Проблемы?

### Приложение не запускается
```bash
# Смотрим логи
docker-compose logs

# Проверяем контейнер
docker ps -a
```

### Не открывается в браузере
1. Проверьте, что контейнер запущен: `docker-compose ps`
2. Проверьте файрвол сервера: `ufw status`
3. Проверьте файрвол в панели Timeweb
4. Проверьте порт: `netstat -tlnp | grep 8000`

### Нет доступа к серверу
1. Проверьте IP-адрес в панели Timeweb
2. Убедитесь, что сервер запущен
3. Попробуйте через веб-консоль Timeweb

---

## 💰 Стоимость

- Timeweb S1 (1 CPU, 1 GB RAM): ~150-200₽/месяц
- Достаточно для вашего приложения
- Серверы в РФ → API работает! ✅


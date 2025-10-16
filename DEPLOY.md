# 🚀 Инструкции по деплою PBX приложения

## Варианты деплоя

### 1. 🐳 Docker (Рекомендуется)

#### Быстрый старт:
```bash
# Клонируем проект
git clone <your-repo>
cd onlinepbx_calls

# Запускаем деплой
chmod +x deploy.sh
./deploy.sh
```

#### Ручной запуск:
```bash
# Создаем директории
mkdir -p logs

# Собираем и запускаем
docker-compose up -d --build

# Проверяем статус
docker-compose ps
docker-compose logs -f
```

#### Остановка:
```bash
docker-compose down
```

### 2. 🐧 Linux сервер (systemd)

#### Установка:
```bash
# Копируем проект
sudo cp -r /path/to/onlinepbx_calls /opt/pbx-calls
cd /opt/pbx-calls

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Создаем пользователя
sudo useradd -r -s /bin/false www-data

# Копируем systemd сервис
sudo cp systemd.service /etc/systemd/system/pbx-calls.service
sudo systemctl daemon-reload

# Запускаем сервис
sudo systemctl enable pbx-calls
sudo systemctl start pbx-calls

# Проверяем статус
sudo systemctl status pbx-calls
```

#### Управление:
```bash
# Перезапуск
sudo systemctl restart pbx-calls

# Остановка
sudo systemctl stop pbx-calls

# Логи
sudo journalctl -u pbx-calls -f
```

### 3. ☁️ Облачные платформы

#### Heroku:
```bash
# Устанавливаем Heroku CLI
# Создаем Procfile
echo "web: gunicorn --bind 0.0.0.0:$PORT wsgi:app" > Procfile

# Деплой
heroku create your-app-name
git push heroku main
```

#### Railway:
```bash
# Подключаем GitHub репозиторий
# Railway автоматически определит Dockerfile
# Настраиваем переменные окружения
```

#### DigitalOcean App Platform:
```bash
# Создаем app.yaml
# Подключаем GitHub репозиторий
# Настраиваем переменные окружения
```

## 🔧 Настройка

### Переменные окружения:
```bash
# Для продакшена
export FLASK_ENV=production
export FLASK_DEBUG=False
```

### Nginx (опционально):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Мониторинг

### Логи:
```bash
# Docker
docker-compose logs -f

# Systemd
sudo journalctl -u pbx-calls -f

# Файлы логов
tail -f logs/access.log
tail -f logs/error.log
```

### Проверка здоровья:
```bash
# Проверка доступности
curl http://localhost:8000/

# Проверка статистики
curl http://localhost:8000/stats
```

## 🔒 Безопасность

### Firewall (Ubuntu/Debian):
```bash
# Разрешаем только нужные порты
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### SSL сертификат (Let's Encrypt):
```bash
# Устанавливаем certbot
sudo apt install certbot python3-certbot-nginx

# Получаем сертификат
sudo certbot --nginx -d your-domain.com
```

## 📈 Масштабирование

### Горизонтальное масштабирование:
```yaml
# docker-compose.yml
services:
  pbx-app:
    # ... конфигурация
    deploy:
      replicas: 3
```

### Load Balancer (Nginx):
```nginx
upstream pbx_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}
```

## 🛠️ Обслуживание

### Обновление:
```bash
# Docker
git pull
docker-compose down
docker-compose up -d --build

# Systemd
git pull
sudo systemctl restart pbx-calls
```

### Резервное копирование:
```bash
# База данных
cp calls_history.db backup/calls_history_$(date +%Y%m%d).db

# Логи
tar -czf logs_$(date +%Y%m%d).tar.gz logs/
```

## 🆘 Устранение неполадок

### Частые проблемы:

1. **Порт занят:**
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

2. **Права доступа:**
```bash
sudo chown -R www-data:www-data /opt/pbx-calls
```

3. **Недостаточно памяти:**
```bash
# Увеличиваем swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 📞 Поддержка

При возникновении проблем проверьте:
- Логи приложения
- Статус сервисов
- Доступность портов
- Права доступа к файлам

# Конфигурация Gunicorn для продакшена

# Количество воркеров (обычно 2 * CPU cores + 1)
workers = 3

# Биндинг (порт и хост)
bind = "0.0.0.0:8000"

# Таймауты
timeout = 120
keepalive = 2

# Логирование (выводим в консоль, а не в файлы)
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Перезапуск при изменении файлов (только для разработки)
reload = False

# Максимальное количество запросов на воркера перед перезапуском
max_requests = 1000
max_requests_jitter = 50

# Предзагрузка приложения
preload_app = True

# Пользователь и группа (для Linux)
# user = "www-data"
# group = "www-data"

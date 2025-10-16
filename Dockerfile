# Dockerfile для контейнеризации приложения
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Gunicorn для продакшена
RUN pip install gunicorn

# Копируем код приложения
COPY . .

# Создаем директории и файлы
RUN mkdir -p logs && \
    echo '{}' > pbx_api_key.json && \
    rm -rf calls_history.db && \
    touch calls_history.db

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

# Открываем порт
EXPOSE 8000

# Команда запуска через Gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]

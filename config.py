import os

# Читаем из переменных окружения или используем значения по умолчанию
DOMAIN = os.getenv('DOMAIN', 'guitardo.onpbx.ru')
AUTH_KEY = os.getenv('AUTH_KEY', 'qJqxwdH7ZccfzS1F3UoStTRJSZHvfWTR5Dt4kiv7Og')
API_URL = f'https://api2.onlinepbx.ru/{DOMAIN}/mongo_history/search.json'
AUTH_URL = f'https://api2.onlinepbx.ru/{DOMAIN}/auth.json' 
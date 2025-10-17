from flask import Flask, render_template, jsonify
import requests
import time
import os
import json
from datetime import datetime
from config import API_URL, AUTH_KEY, AUTH_URL, DOMAIN
import logging
import sqlite3
import hashlib

KEY_FILE = 'pbx_api_key.json'
DB_FILE = 'calls_history.db'

def format_timestamp(timestamp):
    """Преобразует Unix timestamp в формат ЧЧ:ММ:СС ДД.ММ.ГГ"""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%H:%M:%S %d.%m.%y')
    except (ValueError, TypeError, OSError):
        return str(timestamp)

def format_period_label(start_timestamp, end_timestamp):
    """Форматирует метку периода для статистики"""
    try:
        start_dt = datetime.fromtimestamp(start_timestamp)
        end_dt = datetime.fromtimestamp(end_timestamp)
        
        # Если это один день
        if start_dt.date() == end_dt.date():
            return f"за {start_dt.strftime('%d.%m.%Y')} {start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"
        else:
            # Если период охватывает несколько дней
            return f"за {start_dt.strftime('%d.%m.%Y %H:%M')}-{end_dt.strftime('%d.%m.%Y %H:%M')}"
    except (ValueError, TypeError, OSError):
        return ""

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('pbx_app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def load_api_key():
    try:
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'r') as f:
                data = json.load(f)
                logging.info('API key loaded from file.')
                return data.get('api_key')
        logging.info('API key file not found.')
    except Exception as e:
        logging.error(f'Error loading API key from file: {e}')
    return None

def save_api_key(key_id, key):
    api_key = f"{key_id}:{key}"
    try:
        with open(KEY_FILE, 'w') as f:
            json.dump({'api_key': api_key}, f)
        logging.info('API key saved to file.')
    except Exception as e:
        logging.error(f'Error saving API key to file: {e}')
    return api_key

def get_new_api_key():
    payload = {'auth_key': AUTH_KEY, 'new': 'true'}
    try:
        resp = requests.post(AUTH_URL, data=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') == '1':
            key_id = data['data']['key_id']
            key = data['data']['key']
            logging.info('New API key obtained successfully.')
            return save_api_key(key_id, key)
        else:
            logging.error(f"Auth error: {data}")
            raise Exception(f"Auth error: {data}")
    except Exception as e:
        logging.error(f"Error getting new API key: {e}")
        return None

def get_valid_api_key():
    api_key = load_api_key()
    if not api_key:
        logging.info('No valid API key found, requesting new one.')
        api_key = get_new_api_key()
    return api_key

def init_db():
    """Инициализация базы данных SQLite"""
    import os
    logging.info(f"=== DATABASE INITIALIZATION DEBUG ===")
    logging.info(f"DB_FILE path: {DB_FILE}")
    logging.info(f"Current working directory: {os.getcwd()}")
    logging.info(f"DB file exists: {os.path.exists(DB_FILE)}")
    logging.info(f"Current user: {os.getuid() if hasattr(os, 'getuid') else 'Windows'}")
    
    # ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ФАЙЛЕ БД
    if os.path.exists(DB_FILE):
        import stat
        file_stat = os.stat(DB_FILE)
        logging.info(f"=== FILE DETAILS ===")
        logging.info(f"File size: {file_stat.st_size} bytes")
        logging.info(f"File mode (octal): {oct(file_stat.st_mode)}")
        logging.info(f"File permissions: {stat.filemode(file_stat.st_mode)}")
        logging.info(f"File owner UID: {file_stat.st_uid}")
        logging.info(f"File group GID: {file_stat.st_gid}")
        logging.info(f"Is regular file: {stat.S_ISREG(file_stat.st_mode)}")
        logging.info(f"Is directory: {stat.S_ISDIR(file_stat.st_mode)}")
        logging.info(f"Is link: {stat.S_ISLNK(file_stat.st_mode)}")
        
        # Проверяем, можем ли читать/писать
        logging.info(f"Can read: {os.access(DB_FILE, os.R_OK)}")
        logging.info(f"Can write: {os.access(DB_FILE, os.W_OK)}")
        logging.info(f"Can execute: {os.access(DB_FILE, os.X_OK)}")
        
        # Пробуем открыть файл для чтения
        try:
            with open(DB_FILE, 'rb') as f:
                content = f.read(16)
                logging.info(f"File content (first 16 bytes): {content}")
        except Exception as e:
            logging.error(f"Cannot read file: {e}")
    
    # Список всех файлов в текущей директории
    logging.info(f"=== FILES IN CURRENT DIRECTORY ===")
    try:
        files = os.listdir('.')
        for f in files:
            fstat = os.stat(f)
            logging.info(f"  {f}: size={fstat.st_size}, mode={oct(fstat.st_mode)}")
    except Exception as e:
        logging.error(f"Cannot list directory: {e}")
    
    # Проверяем права доступа к текущей директории
    try:
        test_file = 'test_write_permissions.tmp'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logging.info(f"Write permissions in current dir: OK")
    except Exception as e:
        logging.error(f"Write permissions in current dir: FAILED - {e}")
    
    # Пытаемся создать директорию, если нужно
    db_dir = os.path.dirname(DB_FILE)
    if db_dir and not os.path.exists(db_dir):
        logging.info(f"Creating directory: {db_dir}")
        os.makedirs(db_dir, exist_ok=True)
    
    logging.info(f"Attempting to connect to database...")
    try:
        conn = sqlite3.connect(DB_FILE)
        logging.info(f"Database connection: SUCCESS")
    except Exception as e:
        logging.error(f"Database connection: FAILED - {e}")
        logging.error(f"Exception type: {type(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        
        # Пробуем удалить файл/директорию и создать заново
        logging.info(f"=== ATTEMPTING TO RECREATE DATABASE FILE ===")
        try:
            if os.path.exists(DB_FILE):
                logging.info(f"Removing existing file/directory...")
                if os.path.isdir(DB_FILE):
                    logging.info(f"Removing directory: {DB_FILE}")
                    import shutil
                    shutil.rmtree(DB_FILE)
                else:
                    logging.info(f"Removing file: {DB_FILE}")
                    os.remove(DB_FILE)
                logging.info(f"File/directory removed successfully")
            
            logging.info(f"Creating new database file...")
            conn = sqlite3.connect(DB_FILE)
            logging.info(f"Database connection after recreation: SUCCESS")
        except Exception as e2:
            logging.error(f"Recreation also failed: {e2}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise
    cursor = conn.cursor()
    
    # Проверяем, существует ли таблица calls со старой структурой
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calls'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # Проверяем наличие колонки end_stamp
        cursor.execute("PRAGMA table_info(calls)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'end_stamp' not in columns or 'call_data' not in columns:
            logging.info('Old table structure detected, recreating calls table...')
            cursor.execute('DROP TABLE IF EXISTS calls')
            table_exists = False
    
    # Таблица для хранения звонков
    if not table_exists:
        cursor.execute('''
            CREATE TABLE calls (
                id TEXT PRIMARY KEY,
                start_stamp INTEGER NOT NULL,
                end_stamp INTEGER NOT NULL,
                caller_id_number TEXT,
                destination_number TEXT,
                billsec INTEGER,
                duration INTEGER,
                accountcode TEXT,
                gateway TEXT,
                caller_id_name TEXT,
                description TEXT,
                call_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logging.info('Created calls table with new structure')
    
    # Индексы для быстрого поиска по временным интервалам
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_start_stamp ON calls(start_stamp)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_end_stamp ON calls(end_stamp)
    ''')
    
    # Таблица для хранения trunk'ов (номеров)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trunks (
            number TEXT PRIMARY KEY,
            description TEXT,
            trunk_data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица для кеша запросов (для отслеживания запрошенных периодов)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_hash TEXT UNIQUE,
            start_stamp INTEGER,
            end_stamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица для статистики по дням
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            start_stamp INTEGER NOT NULL,
            end_stamp INTEGER NOT NULL,
            caller_number TEXT NOT NULL,
            description TEXT,
            total_calls INTEGER NOT NULL,
            calls_over_45s INTEGER NOT NULL,
            percentage_over_45s REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, caller_number)
        )
    ''')
    
    # Индекс для быстрого поиска по дате
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_date ON daily_stats(date)
    ''')
    
    conn.commit()
    conn.close()
    logging.info('Database initialized successfully')

def get_request_hash(start_stamp, end_stamp):
    """Создает хеш для идентификации уникального запроса"""
    return hashlib.md5(f"{start_stamp}_{end_stamp}".encode()).hexdigest()

def is_period_cached(start_stamp, end_stamp):
    """Проверяет, есть ли данные за указанный период в кеше"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Проверяем, есть ли запись о таком запросе
    request_hash = get_request_hash(start_stamp, end_stamp)
    cursor.execute('''
        SELECT COUNT(*) FROM cache_requests 
        WHERE request_hash = ?
    ''', (request_hash,))
    
    cached = cursor.fetchone()[0] > 0
    conn.close()
    
    return cached

def save_calls_to_cache(calls, start_stamp, end_stamp):
    """Сохраняет звонки в кеш"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Сохраняем каждый звонок
        for call in calls:
            # Используем уникальный идентификатор звонка (если есть) или создаем свой
            call_id = call.get('id') or call.get('uuid') or hashlib.md5(
                f"{call.get('start_stamp')}_{call.get('caller_id_number')}_{call.get('destination_number')}".encode()
            ).hexdigest()
            
            cursor.execute('''
                INSERT OR REPLACE INTO calls 
                (id, start_stamp, end_stamp, caller_id_number, destination_number, 
                 billsec, duration, accountcode, gateway, caller_id_name, description, call_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                call_id,
                call.get('start_stamp', 0),
                call.get('end_stamp', 0),
                call.get('caller_id_number', ''),
                call.get('destination_number', ''),
                call.get('billsec', 0),
                call.get('duration', 0),
                call.get('accountcode', ''),
                call.get('gateway', ''),
                call.get('caller_id_name', ''),
                call.get('description', ''),
                json.dumps(call)
            ))
        
        # Сохраняем информацию о запросе
        request_hash = get_request_hash(start_stamp, end_stamp)
        cursor.execute('''
            INSERT OR REPLACE INTO cache_requests 
            (request_hash, start_stamp, end_stamp)
            VALUES (?, ?, ?)
        ''', (request_hash, start_stamp, end_stamp))
        
        conn.commit()
        logging.info(f'Saved {len(calls)} calls to cache for period {start_stamp}-{end_stamp}')
    except Exception as e:
        logging.error(f'Error saving calls to cache: {e}')
        conn.rollback()
    finally:
        conn.close()

def get_calls_from_cache(start_stamp, end_stamp):
    """Получает звонки из кеша за указанный период"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT call_data FROM calls 
        WHERE start_stamp >= ? AND start_stamp <= ?
        AND accountcode = 'outbound'
        ORDER BY start_stamp DESC
    ''', (start_stamp, end_stamp))
    
    rows = cursor.fetchall()
    conn.close()
    
    calls = [json.loads(row[0]) for row in rows]
    logging.info(f'Retrieved {len(calls)} calls from cache for period {start_stamp}-{end_stamp}')
    return calls

def save_trunks_to_cache(trunks_data):
    """Сохраняет данные о trunk'ах в кеш"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        for trunk in trunks_data:
            number = trunk.get('number', '')
            description = trunk.get('description', '')
            
            if number:
                cursor.execute('''
                    INSERT OR REPLACE INTO trunks 
                    (number, description, trunk_data, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (number, description, json.dumps(trunk)))
        
        conn.commit()
        logging.info(f'Saved {len(trunks_data)} trunks to cache')
    except Exception as e:
        logging.error(f'Error saving trunks to cache: {e}')
        conn.rollback()
    finally:
        conn.close()

def get_trunks_from_cache(max_age_seconds=3600):
    """Получает trunk'и из кеша, если они не старше указанного времени"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Проверяем, есть ли актуальные данные (не старше max_age_seconds)
    cursor.execute('''
        SELECT trunk_data FROM trunks 
        WHERE datetime(updated_at) > datetime('now', '-' || ? || ' seconds')
    ''', (max_age_seconds,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        trunks = [json.loads(row[0]) for row in rows]
        logging.info(f'Retrieved {len(trunks)} trunks from cache')
        return trunks
    else:
        logging.info('No fresh trunks data in cache')
        return None

def save_daily_stats(caller_stats, start_stamp, end_stamp, date_str):
    """Сохраняет статистику по номерам за определенный день"""
    if not caller_stats:
        return
    
    # Определяем, является ли этот день сегодняшним
    from datetime import datetime
    today_str = datetime.now().strftime('%Y-%m-%d')
    is_today = (date_str == today_str)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        for stat in caller_stats:
            caller_number = stat.get('caller_number', '')
            if not caller_number:
                continue
            
            # Проверяем, есть ли уже запись для этого дня и номера
            cursor.execute('''
                SELECT id FROM daily_stats 
                WHERE date = ? AND caller_number = ?
            ''', (date_str, caller_number))
            
            existing = cursor.fetchone()
            
            if existing and not is_today:
                # Для прошлых дней не обновляем данные
                continue
            
            if existing:
                # Обновляем существующую запись (только для сегодняшнего дня)
                cursor.execute('''
                    UPDATE daily_stats 
                    SET total_calls = ?,
                        calls_over_45s = ?,
                        percentage_over_45s = ?,
                        description = ?,
                        start_stamp = ?,
                        end_stamp = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE date = ? AND caller_number = ?
                ''', (
                    stat.get('total_calls', 0),
                    stat.get('calls_over_45s', 0),
                    stat.get('percentage_over_45s', 0.0),
                    stat.get('description', ''),
                    start_stamp,
                    end_stamp,
                    date_str,
                    caller_number
                ))
            else:
                # Создаем новую запись
                cursor.execute('''
                    INSERT INTO daily_stats 
                    (date, start_stamp, end_stamp, caller_number, description, 
                     total_calls, calls_over_45s, percentage_over_45s)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_str,
                    start_stamp,
                    end_stamp,
                    caller_number,
                    stat.get('description', ''),
                    stat.get('total_calls', 0),
                    stat.get('calls_over_45s', 0),
                    stat.get('percentage_over_45s', 0.0)
                ))
        
        conn.commit()
        logging.info(f'Saved {len(caller_stats)} stats records for date {date_str}')
    except Exception as e:
        logging.error(f'Error saving daily stats: {e}')
        conn.rollback()
    finally:
        conn.close()

def get_daily_stats_by_date(date_str):
    """Получает статистику за определенный день"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT caller_number, description, total_calls, calls_over_45s, percentage_over_45s
        FROM daily_stats 
        WHERE date = ?
        ORDER BY total_calls DESC
    ''', (date_str,))
    
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            'caller_number': row[0],
            'description': row[1],
            'total_calls': row[2],
            'calls_over_45s': row[3],
            'percentage_over_45s': row[4]
        })
    
    return result

def get_all_stats_dates():
    """Получает список всех дат, для которых есть статистика"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT date, start_stamp, end_stamp, 
               SUM(total_calls) as total_calls_count
        FROM daily_stats 
        GROUP BY date
        ORDER BY date DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            'date': row[0],
            'start_stamp': row[1],
            'end_stamp': row[2],
            'total_calls': row[3]
        })
    
    return result

def get_comprehensive_stats():
    """Получает сводную статистику всех номеров по всем дням"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Получаем все уникальные номера
    cursor.execute('''
        SELECT DISTINCT caller_number, description
        FROM daily_stats 
        ORDER BY caller_number
    ''')
    
    numbers = cursor.fetchall()
    
    # Получаем все даты
    cursor.execute('''
        SELECT DISTINCT date 
        FROM daily_stats 
        ORDER BY date DESC
    ''')
    
    dates = [row[0] for row in cursor.fetchall()]
    
    # Получаем все данные статистики
    cursor.execute('''
        SELECT date, caller_number, description, total_calls, calls_over_45s, percentage_over_45s
        FROM daily_stats 
        ORDER BY date DESC, caller_number
    ''')
    
    stats_data = cursor.fetchall()
    conn.close()
    
    # Создаем словарь для быстрого поиска
    stats_dict = {}
    for row in stats_data:
        date, caller_number, description, total_calls, calls_over_45s, percentage_over_45s = row
        key = (date, caller_number)
        stats_dict[key] = {
            'total_calls': total_calls,
            'calls_over_45s': calls_over_45s,
            'percentage_over_45s': percentage_over_45s
        }
    
    # Формируем результат
    result = []
    for caller_number, description in numbers:
        number_stats = {
            'caller_number': caller_number,
            'description': description or '',
            'dates': {}
        }
        
        for date in dates:
            key = (date, caller_number)
            if key in stats_dict:
                number_stats['dates'][date] = stats_dict[key]
            else:
                number_stats['dates'][date] = None
        
        result.append(number_stats)
    
    # Сортируем по количеству звонков за вчерашний день (вторая дата в списке, так как даты отсортированы по убыванию)
    if len(dates) >= 2:
        yesterday_date = dates[1]  # Вторая дата в списке (вчерашний день)
        result.sort(key=lambda x: x['dates'].get(yesterday_date, {}).get('total_calls', 0) if x['dates'].get(yesterday_date) else 0, reverse=True)
    elif len(dates) >= 1:
        # Если есть только одна дата, сортируем по ней
        today_date = dates[0]
        result.sort(key=lambda x: x['dates'].get(today_date, {}).get('total_calls', 0) if x['dates'].get(today_date) else 0, reverse=True)
    
    return result, dates

def calculate_caller_stats(calls):
    """Вычисляет статистику по уникальным номерам звонящих"""
    stats = {}
    
    for call in calls:
        caller_number = call.get('caller_id_number', '')
        duration = call.get('billsec', 0)
        
        # Пропускаем трехзначные номера (и короче)
        if caller_number and len(caller_number) > 3:
            if caller_number not in stats:
                stats[caller_number] = {
                    'total_calls': 0,
                    'calls_over_45s': 0,
                    'description': call.get('description', '')
                }
            
            stats[caller_number]['total_calls'] += 1
            if duration > 45:
                stats[caller_number]['calls_over_45s'] += 1
    
    # Преобразуем в список и вычисляем проценты
    result = []
    for caller_number, data in stats.items():
        total_calls = data['total_calls']
        calls_over_45s = data['calls_over_45s']
        percentage = (calls_over_45s / total_calls * 100) if total_calls > 0 else 0
        
        result.append({
            'caller_number': caller_number,
            'description': data['description'],
            'total_calls': total_calls,
            'calls_over_45s': calls_over_45s,
            'percentage_over_45s': round(percentage, 1)
        })
    
    # Сортируем по количеству звонков (по убыванию)
    result.sort(key=lambda x: x['total_calls'], reverse=True)
    return result

def get_trunks_data():
    """Получает данные о trunk'ах (номерах) из API или кеша"""
    # Сначала пытаемся получить из кеша (актуальность 1 час)
    cached_trunks = get_trunks_from_cache(max_age_seconds=3600)
    
    if cached_trunks:
        logging.info('Using trunks data from cache')
        # Создаем словарь для быстрого поиска описания по номеру
        trunks_dict = {}
        for trunk in cached_trunks:
            number = trunk.get('number', '')
            description = trunk.get('description', '')
            if number:
                trunks_dict[number] = description
        return trunks_dict
    
    # Если нет в кеше, запрашиваем из API
    logging.info('Fetching trunks data from API')
    api_key = get_valid_api_key()
    if not api_key:
        return {}
    
    headers = {
        'x-pbx-authentication': api_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # URL для получения статуса номеров
    trunks_url = f'https://api2.onlinepbx.ru/{DOMAIN}/trunks/get.json'
    
    try:
        response = requests.post(trunks_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('isNotAuth'):
            logging.warning('API key expired for trunks, requesting new key...')
            get_new_api_key()
            return {}
        
        if data.get('status') == '1':
            trunks_data = data.get('data', [])
            
            # Сохраняем в кеш
            save_trunks_to_cache(trunks_data)
            
            # Создаем словарь для быстрого поиска описания по номеру
            trunks_dict = {}
            for trunk in trunks_data:
                number = trunk.get('number', '')
                description = trunk.get('description', '')
                if number:
                    trunks_dict[number] = description
            return trunks_dict
        else:
            logging.error(f"Trunks API error: {data}")
            return {}
            
    except Exception as e:
        logging.error(f"Error getting trunks data: {e}")
        return {}

app = Flask(__name__)

# Инициализируем базу данных при старте приложения
init_db()

def get_calls_data(interval_seconds, title):
    """Общая функция для получения данных о звонках за указанный интервал"""
    logging.info(f'Entering get_calls_data function for {title}')
    now = int(time.time())
    start_time = now - interval_seconds
    payload = {
        'start_stamp_from': start_time,
        'start_stamp_to': now
    }
    calls = []
    error = None
    period_label = format_period_label(start_time, now)
    
    # Получаем данные о trunk'ах для описаний номеров
    trunks_dict = get_trunks_data()
    
    # Проверяем, есть ли данные в кеше
    if is_period_cached(start_time, now):
        logging.info(f'Using cached data for period {start_time}-{now}')
        calls = get_calls_from_cache(start_time, now)
        
        # Добавляем форматированные поля и описания
        for call in calls:
            call['formatted_start_stamp'] = format_timestamp(call.get('start_stamp', 0))
            caller_number = call.get('caller_id_number', '')
            call['description'] = trunks_dict.get(caller_number, '')
        
        # Вычисляем статистику по номерам звонящих
        caller_stats = calculate_caller_stats(calls)
        return calls, caller_stats, error, period_label
    
    # Если нет в кеше, запрашиваем из API
    logging.info(f'Fetching data from API for period {start_time}-{now}')
    for attempt in range(2):  # максимум 2 попытки: с текущим ключом и с новым
        api_key = get_valid_api_key()
        if not api_key:
            error = 'Не удалось получить API-ключ для авторизации.'
            logging.error(error)
            break
        headers = {
            'x-pbx-authentication': api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = requests.post(API_URL, data=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logging.info(f"API Response Status Code: {response.status_code}")
            logging.info(f"API Response Body: {response.text}")
            data = response.json()
            logging.info(f"Parsed JSON data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            if data.get('isNotAuth'):
                logging.warning('API key expired or invalid, requesting new key...')
                get_new_api_key()
                continue  # повторить запрос с новым ключом
            all_calls = data.get('data', [])
            # Фильтруем только исходящие звонки (accountcode = 'outbound')
            calls = [call for call in all_calls if call.get('accountcode') == 'outbound']
            # Сортируем звонки от новых к старым (по убыванию start_stamp)
            calls.sort(key=lambda call: call.get('start_stamp', 0), reverse=True)
            for call in calls:
                call['caller_id_number'] = call.get('gateway') or call.get('caller_id_number') or call.get('caller_id_name')
                call['billsec'] = call.get('billsec', call.get('duration', 0))
                call['formatted_start_stamp'] = format_timestamp(call.get('start_stamp', 0))
                # Добавляем описание номера из данных о trunk'ах
                caller_number = call['caller_id_number']
                call['description'] = trunks_dict.get(caller_number, '')
            
            # Сохраняем полученные данные в кеш
            save_calls_to_cache(calls, start_time, now)
            
            # Вычисляем статистику по номерам звонящих
            caller_stats = calculate_caller_stats(calls)
            break  # успешный запрос, выходим из цикла
        except requests.exceptions.Timeout:
            error = 'Превышено время ожидания ответа от API.'
            logging.error(error)
            break
        except requests.exceptions.RequestException as e:
            if '403' in str(e):
                logging.warning('API key expired (403 Forbidden), requesting new key...')
                get_new_api_key()
                continue  # повторить запрос с новым ключом
            error = f'Ошибка запроса к API: {e}'
            logging.error(error)
            break
        except Exception as e:
            error = f'Непредвиденная ошибка: {e}'
            logging.error(error)
            break
    # Инициализируем статистику если не была вычислена
    if 'caller_stats' not in locals():
        caller_stats = []
    
    return calls, caller_stats, error, period_label

@app.route('/')
def index():
    """Главная страница - звонки за последние 10 минут"""
    calls, caller_stats, error, period_label = get_calls_data(600, "10 минут")
    return render_template('index.html', calls=calls, caller_stats=caller_stats, error=error, title="Звонки за последние 10 минут", period_label=period_label)

@app.route('/1h')
def calls_1h():
    """Звонки за последний час"""
    calls, caller_stats, error, period_label = get_calls_data(3600, "1 час")
    return render_template('index.html', calls=calls, caller_stats=caller_stats, error=error, title="Звонки за последний час", period_label=period_label)

@app.route('/4h')
def calls_4h():
    """Звонки за последние 4 часа"""
    calls, caller_stats, error, period_label = get_calls_data(14400, "4 часа")
    return render_template('index.html', calls=calls, caller_stats=caller_stats, error=error, title="Звонки за последние 4 часа", period_label=period_label)

@app.route('/8h')
def calls_8h():
    """Звонки за последние 8 часов"""
    calls, caller_stats, error, period_label = get_calls_data(28800, "8 часов")
    return render_template('index.html', calls=calls, caller_stats=caller_stats, error=error, title="Звонки за последние 8 часов", period_label=period_label)

@app.route('/today')
def calls_today():
    """Звонки за сегодня"""
    from datetime import datetime, time
    now = datetime.now()
    start_of_day = datetime.combine(now.date(), time.min)
    start_time = int(start_of_day.timestamp())
    end_time = int(now.timestamp())
    date_str_display = now.strftime('%d.%m.%Y')
    date_str_db = now.strftime('%Y-%m-%d')
    
    # Используем функцию с фиксированными временными метками для сохранения статистики
    calls, caller_stats, error, period_label = get_calls_data_for_period(start_time, end_time, f"сегодня ({date_str_display})", date_str_db)
    return render_template('index.html', calls=calls, caller_stats=caller_stats, error=error, title=f"Звонки за сегодня ({date_str_display})", period_label=period_label)

def get_calls_data_for_period(start_time, end_time, title, date_str=None):
    """Общая функция для получения данных о звонках за указанный период с фиксированными временными метками"""
    logging.info(f'Entering get_calls_data_for_period function for {title}')
    
    # Определяем дату для сохранения статистики
    if not date_str:
        date_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
    
    payload = {
        'start_stamp_from': start_time,
        'start_stamp_to': end_time
    }
    calls = []
    error = None
    period_label = format_period_label(start_time, end_time)
    
    # Получаем данные о trunk'ах для описаний номеров
    trunks_dict = get_trunks_data()
    
    # Проверяем, есть ли данные в кеше
    if is_period_cached(start_time, end_time):
        logging.info(f'Using cached data for period {start_time}-{end_time}')
        calls = get_calls_from_cache(start_time, end_time)
        
        # Добавляем форматированные поля и описания
        for call in calls:
            call['formatted_start_stamp'] = format_timestamp(call.get('start_stamp', 0))
            caller_number = call.get('caller_id_number', '')
            call['description'] = trunks_dict.get(caller_number, '')
        
        # Вычисляем статистику по номерам звонящих
        caller_stats = calculate_caller_stats(calls)
        
        # Сохраняем статистику в БД (если её ещё нет)
        save_daily_stats(caller_stats, start_time, end_time, date_str)
        
        return calls, caller_stats, error, period_label
    
    # Если нет в кеше, запрашиваем из API
    logging.info(f'Fetching data from API for period {start_time}-{end_time}')
    for attempt in range(2):  # максимум 2 попытки: с текущим ключом и с новым
        api_key = get_valid_api_key()
        if not api_key:
            error = 'Не удалось получить API-ключ для авторизации.'
            logging.error(error)
            break
        headers = {
            'x-pbx-authentication': api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = requests.post(API_URL, data=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logging.info(f"API Response Status Code: {response.status_code}")
            logging.info(f"API Response Body: {response.text}")
            data = response.json()
            logging.info(f"Parsed JSON data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            if data.get('isNotAuth'):
                logging.warning('API key expired or invalid, requesting new key...')
                get_new_api_key()
                continue  # повторить запрос с новым ключом
            all_calls = data.get('data', [])
            # Фильтруем только исходящие звонки (accountcode = 'outbound')
            calls = [call for call in all_calls if call.get('accountcode') == 'outbound']
            # Сортируем звонки от новых к старым (по убыванию start_stamp)
            calls.sort(key=lambda call: call.get('start_stamp', 0), reverse=True)
            for call in calls:
                call['caller_id_number'] = call.get('gateway') or call.get('caller_id_number') or call.get('caller_id_name')
                call['billsec'] = call.get('billsec', call.get('duration', 0))
                call['formatted_start_stamp'] = format_timestamp(call.get('start_stamp', 0))
                # Добавляем описание номера из данных о trunk'ах
                caller_number = call['caller_id_number']
                call['description'] = trunks_dict.get(caller_number, '')
            
            # Сохраняем полученные данные в кеш
            save_calls_to_cache(calls, start_time, end_time)
            
            # Вычисляем статистику по номерам звонящих
            caller_stats = calculate_caller_stats(calls)
            break  # успешный запрос, выходим из цикла
        except requests.exceptions.Timeout:
            error = 'Превышено время ожидания ответа от API.'
            logging.error(error)
            break
        except requests.exceptions.RequestException as e:
            if '403' in str(e):
                logging.warning('API key expired (403 Forbidden), requesting new key...')
                get_new_api_key()
                continue  # повторить запрос с новым ключом
            error = f'Ошибка запроса к API: {e}'
            logging.error(error)
            break
        except Exception as e:
            error = f'Непредвиденная ошибка: {e}'
            logging.error(error)
            break
    # Инициализируем статистику если не была вычислена
    if 'caller_stats' not in locals():
        caller_stats = []
    
    return calls, caller_stats, error, period_label

def get_calls_data_with_offset(interval_seconds, title, offset_seconds=0):
    """Общая функция для получения данных о звонках за указанный интервал с возможным смещением"""
    logging.info(f'Entering get_calls_data_with_offset function for {title}')
    now = int(time.time())
    end_time = now - offset_seconds
    start_time = end_time - interval_seconds
    payload = {
        'start_stamp_from': start_time,
        'start_stamp_to': end_time
    }
    calls = []
    error = None
    period_label = format_period_label(start_time, end_time)
    
    # Получаем данные о trunk'ах для описаний номеров
    trunks_dict = get_trunks_data()
    
    # Проверяем, есть ли данные в кеше
    if is_period_cached(start_time, end_time):
        logging.info(f'Using cached data for period {start_time}-{end_time}')
        calls = get_calls_from_cache(start_time, end_time)
        
        # Добавляем форматированные поля и описания
        for call in calls:
            call['formatted_start_stamp'] = format_timestamp(call.get('start_stamp', 0))
            caller_number = call.get('caller_id_number', '')
            call['description'] = trunks_dict.get(caller_number, '')
        
        # Вычисляем статистику по номерам звонящих
        caller_stats = calculate_caller_stats(calls)
        return calls, caller_stats, error, period_label
    
    # Если нет в кеше, запрашиваем из API
    logging.info(f'Fetching data from API for period {start_time}-{end_time}')
    for attempt in range(2):  # максимум 2 попытки: с текущим ключом и с новым
        api_key = get_valid_api_key()
        if not api_key:
            error = 'Не удалось получить API-ключ для авторизации.'
            logging.error(error)
            break
        headers = {
            'x-pbx-authentication': api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = requests.post(API_URL, data=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logging.info(f"API Response Status Code: {response.status_code}")
            logging.info(f"API Response Body: {response.text}")
            data = response.json()
            logging.info(f"Parsed JSON data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            if data.get('isNotAuth'):
                logging.warning('API key expired or invalid, requesting new key...')
                get_new_api_key()
                continue  # повторить запрос с новым ключом
            all_calls = data.get('data', [])
            # Фильтруем только исходящие звонки (accountcode = 'outbound')
            calls = [call for call in all_calls if call.get('accountcode') == 'outbound']
            # Сортируем звонки от новых к старым (по убыванию start_stamp)
            calls.sort(key=lambda call: call.get('start_stamp', 0), reverse=True)
            for call in calls:
                call['caller_id_number'] = call.get('gateway') or call.get('caller_id_number') or call.get('caller_id_name')
                call['billsec'] = call.get('billsec', call.get('duration', 0))
                call['formatted_start_stamp'] = format_timestamp(call.get('start_stamp', 0))
                # Добавляем описание номера из данных о trunk'ах
                caller_number = call['caller_id_number']
                call['description'] = trunks_dict.get(caller_number, '')
            
            # Сохраняем полученные данные в кеш
            save_calls_to_cache(calls, start_time, end_time)
            
            # Вычисляем статистику по номерам звонящих
            caller_stats = calculate_caller_stats(calls)
            
            # Сохраняем статистику в БД
            save_daily_stats(caller_stats, start_time, end_time, date_str)
            
            break  # успешный запрос, выходим из цикла
        except requests.exceptions.Timeout:
            error = 'Превышено время ожидания ответа от API.'
            logging.error(error)
            break
        except requests.exceptions.RequestException as e:
            if '403' in str(e):
                logging.warning('API key expired (403 Forbidden), requesting new key...')
                get_new_api_key()
                continue  # повторить запрос с новым ключом
            error = f'Ошибка запроса к API: {e}'
            logging.error(error)
            break
        except Exception as e:
            error = f'Непредвиденная ошибка: {e}'
            logging.error(error)
            break
    # Инициализируем статистику если не была вычислена
    if 'caller_stats' not in locals():
        caller_stats = []
    
    return calls, caller_stats, error, period_label

@app.route('/yesterday')
def calls_yesterday():
    """Звонки за вчера"""
    from datetime import datetime, time, timedelta
    yesterday = datetime.now() - timedelta(days=1)
    start_of_yesterday = datetime.combine(yesterday.date(), time.min)
    end_of_yesterday = datetime.combine(yesterday.date(), time.max)
    # Используем фиксированные временные метки (в Unix timestamp)
    start_time = int(start_of_yesterday.timestamp())
    end_time = int(end_of_yesterday.timestamp())
    date_str_display = yesterday.strftime('%d.%m.%Y')
    date_str_db = yesterday.strftime('%Y-%m-%d')
    
    # Вызываем функцию с фиксированными временными метками
    calls, caller_stats, error, period_label = get_calls_data_for_period(start_time, end_time, f"вчера ({date_str_display})", date_str_db)
    return render_template('index.html', calls=calls, caller_stats=caller_stats, error=error, title=f"Звонки за вчера ({date_str_display})", period_label=period_label)

@app.route('/day_before_yesterday')
def calls_day_before_yesterday():
    """Звонки за позавчера"""
    from datetime import datetime, time, timedelta
    day_before_yesterday = datetime.now() - timedelta(days=2)
    start_of_day = datetime.combine(day_before_yesterday.date(), time.min)
    end_of_day = datetime.combine(day_before_yesterday.date(), time.max)
    # Используем фиксированные временные метки (в Unix timestamp)
    start_time = int(start_of_day.timestamp())
    end_time = int(end_of_day.timestamp())
    date_str_display = day_before_yesterday.strftime('%d.%m.%Y')
    date_str_db = day_before_yesterday.strftime('%Y-%m-%d')
    
    # Вызываем функцию с фиксированными временными метками
    calls, caller_stats, error, period_label = get_calls_data_for_period(start_time, end_time, f"позавчера ({date_str_display})", date_str_db)
    return render_template('index.html', calls=calls, caller_stats=caller_stats, error=error, title=f"Звонки за позавчера ({date_str_display})", period_label=period_label)

@app.route('/date/<date_str>')
def calls_by_date(date_str):
    """Звонки за выбранную дату"""
    from datetime import datetime, time
    try:
        # Проверяем формат даты (YYYY-MM-DD)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Проверяем, что дата не в будущем
        today = datetime.now().date()
        if date_obj.date() > today:
            return render_template('index.html', 
                                 calls=[], 
                                 caller_stats=[], 
                                 error='Нельзя выбрать дату в будущем', 
                                 title="Ошибка", 
                                 period_label="")
        
        # Создаем временные метки для начала и конца дня
        start_of_day = datetime.combine(date_obj.date(), time.min)
        end_of_day = datetime.combine(date_obj.date(), time.max)
        start_time = int(start_of_day.timestamp())
        end_time = int(end_of_day.timestamp())
        
        date_str_display = date_obj.strftime('%d.%m.%Y')
        
        # Вызываем функцию с фиксированными временными метками
        calls, caller_stats, error, period_label = get_calls_data_for_period(start_time, end_time, f"за {date_str_display}", date_str)
        return render_template('index.html', 
                             calls=calls, 
                             caller_stats=caller_stats, 
                             error=error, 
                             title=f"Звонки за {date_str_display}", 
                             period_label=period_label)
    except ValueError:
        return render_template('index.html', 
                             calls=[], 
                             caller_stats=[], 
                             error='Неверный формат даты. Используйте формат YYYY-MM-DD', 
                             title="Ошибка", 
                             period_label="")
    except Exception as e:
        logging.error(f'Error in calls_by_date: {e}')
        return render_template('index.html', 
                             calls=[], 
                             caller_stats=[], 
                             error=f'Ошибка: {e}', 
                             title="Ошибка", 
                             period_label="")

@app.route('/trunks')
def trunks():
    """Страница для отображения статуса номеров"""
    logging.info('Entering trunks function')
    
    trunks_data = []
    error = None
    
    for attempt in range(2):  # максимум 2 попытки: с текущим ключом и с новым
        api_key = get_valid_api_key()
        if not api_key:
            error = 'Не удалось получить API-ключ для авторизации.'
            logging.error(error)
            break
        
        headers = {
            'x-pbx-authentication': api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # URL для получения статуса номеров
        trunks_url = f'https://api2.onlinepbx.ru/{DOMAIN}/trunks/get.json'
        
        try:
            response = requests.post(trunks_url, headers=headers, timeout=10)
            response.raise_for_status()
            logging.info(f"Trunks API Response Status Code: {response.status_code}")
            logging.info(f"Trunks API Response Body: {response.text}")
            
            data = response.json()
            logging.info(f"Parsed Trunks JSON data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get('isNotAuth'):
                logging.warning('API key expired or invalid, requesting new key...')
                get_new_api_key()
                continue  # повторить запрос с новым ключом
            
            if data.get('status') == '1':
                trunks_data = data.get('data', [])
                logging.info(f"Successfully retrieved {len(trunks_data)} trunks")
            else:
                error = f"Ошибка API: {data}"
                logging.error(error)
            break  # успешный запрос, выходим из цикла
            
        except requests.exceptions.Timeout:
            error = 'Превышено время ожидания ответа от API.'
            logging.error(error)
            break
        except requests.exceptions.RequestException as e:
            if '403' in str(e):
                logging.warning('API key expired (403 Forbidden), requesting new key...')
                get_new_api_key()
                continue  # повторить запрос с новым ключом
            error = f'Ошибка запроса к API: {e}'
            logging.error(error)
            break
        except Exception as e:
            error = f'Непредвиденная ошибка: {e}'
            logging.error(error)
            break
    
    return render_template('trunks.html', trunks=trunks_data, error=error)

@app.route('/stats')
def stats_page():
    """Страница статистики по дням"""
    logging.info('Entering stats_page function')
    
    # Получаем список всех дат со статистикой
    stats_dates = get_all_stats_dates()
    
    # Получаем сводную статистику
    comprehensive_stats, dates = get_comprehensive_stats()
    
    # Форматируем даты для отображения
    for stat in stats_dates:
        date_obj = datetime.strptime(stat['date'], '%Y-%m-%d')
        stat['date_display'] = date_obj.strftime('%d.%m.%Y')
        stat['period_label'] = format_period_label(stat['start_stamp'], stat['end_stamp'])
    
    # Форматируем даты для заголовков таблицы
    formatted_dates = []
    for date in dates:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        formatted_dates.append({
            'date': date,
            'display': date_obj.strftime('%d.%m')
        })
    
    return render_template('stats.html', 
                         stats_dates=stats_dates, 
                         comprehensive_stats=comprehensive_stats,
                         formatted_dates=formatted_dates)

@app.route('/stats/<date>')
def stats_detail(date):
    """Детальная статистика за конкретный день"""
    logging.info(f'Entering stats_detail function for date {date}')
    
    try:
        # Проверяем формат даты (YYYY-MM-DD)
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        date_display = date_obj.strftime('%d.%m.%Y')
        
        # Получаем статистику за этот день
        caller_stats = get_daily_stats_by_date(date)
        
        # Вычисляем общую статистику
        total_calls = sum(stat['total_calls'] for stat in caller_stats)
        total_calls_over_45s = sum(stat['calls_over_45s'] for stat in caller_stats)
        
        return render_template('stats_detail.html', 
                             date=date, 
                             date_display=date_display,
                             caller_stats=caller_stats,
                             total_calls=total_calls,
                             total_calls_over_45s=total_calls_over_45s)
    except ValueError:
        return "Неверный формат даты", 400
    except Exception as e:
        logging.error(f'Error in stats_detail: {e}')
        return f"Ошибка: {e}", 500

@app.route('/api/debug')
def api_debug():
    """Отладочный endpoint для просмотра сырого JSON ответа от PBX API"""
    logging.info('Entering api_debug function')
    now = int(time.time())
    payload = {
        'start_stamp_from': now - 6000,
        'start_stamp_to': now
    }
    
    api_key = get_valid_api_key()
    if not api_key:
        return jsonify({'error': 'Не удалось получить API-ключ для авторизации.'}), 500
    
    headers = {
        'x-pbx-authentication': api_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(API_URL, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Возвращаем и сырой текст, и распарсенный JSON
        return jsonify({
            'status_code': response.status_code,
            'raw_response': response.text,
            'parsed_json': response.json(),
            'headers': dict(response.headers)
        })
    except Exception as e:
        return jsonify({'error': f'Ошибка запроса к API: {e}'}), 500

if __name__ == '__main__':
    logging.info("=" * 60)
    logging.info("STARTING FLASK APPLICATION IN DEBUG MODE")
    logging.info("=" * 60)
    app.run(host='0.0.0.0', port=8000, debug=False) 
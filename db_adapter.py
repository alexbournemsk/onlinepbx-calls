"""
Database Adapter для работы с SQLite и PostgreSQL (Supabase)
Автоматически определяет тип БД по переменным окружения
"""
import os
import logging
import json
from typing import Optional, List, Dict, Any, Tuple

# Определяем тип БД по наличию DATABASE_URL
DATABASE_URL = os.getenv('DATABASE_URL')
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import pool
    logging.info("Using PostgreSQL (Supabase)")
else:
    import sqlite3
    logging.info("Using SQLite")

DB_FILE = os.getenv('DB_FILE', 'calls_history.db')


class DatabaseAdapter:
    """Адаптер для работы с разными типами БД"""
    
    def __init__(self):
        self.use_postgres = USE_POSTGRES
        self.db_file = DB_FILE
        self.connection_pool = None
        
        if self.use_postgres:
            # Создаем пул соединений для PostgreSQL
            try:
                self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                    1, 20,  # min, max connections
                    DATABASE_URL
                )
                logging.info("PostgreSQL connection pool created successfully")
            except Exception as e:
                logging.error(f"Failed to create PostgreSQL connection pool: {e}")
                raise
    
    def get_connection(self):
        """Получить соединение с БД"""
        if self.use_postgres:
            return self.connection_pool.getconn()
        else:
            return sqlite3.connect(self.db_file)
    
    def release_connection(self, conn):
        """Освободить соединение"""
        if self.use_postgres:
            self.connection_pool.putconn(conn)
        else:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch: str = None) -> Any:
        """
        Выполнить SQL запрос
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            fetch: 'one', 'all', 'none' - тип возвращаемых данных
        
        Returns:
            Результат запроса в зависимости от fetch
        """
        conn = self.get_connection()
        try:
            if self.use_postgres:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = conn.cursor()
            
            # Преобразуем ? в %s для PostgreSQL
            if self.use_postgres and query:
                query = query.replace('?', '%s')
            
            cursor.execute(query, params or ())
            
            if fetch == 'one':
                result = cursor.fetchone()
                if self.use_postgres:
                    return dict(result) if result else None
                return result
            elif fetch == 'all':
                results = cursor.fetchall()
                if self.use_postgres:
                    return [dict(row) for row in results]
                return results
            else:
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logging.error(f"Database query error: {e}")
            logging.error(f"Query: {query}")
            logging.error(f"Params: {params}")
            raise
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Выполнить множественные INSERT/UPDATE"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Преобразуем ? в %s для PostgreSQL
            if self.use_postgres and query:
                query = query.replace('?', '%s')
            
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logging.error(f"Database executemany error: {e}")
            raise
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def init_database(self):
        """Инициализация схемы БД"""
        logging.info("=== DATABASE INITIALIZATION ===")
        logging.info(f"Database type: {'PostgreSQL' if self.use_postgres else 'SQLite'}")
        
        if self.use_postgres:
            self._init_postgres()
        else:
            self._init_sqlite()
        
        logging.info("Database initialized successfully")
    
    def _init_sqlite(self):
        """Инициализация SQLite"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверяем старую структуру таблицы calls
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calls'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                cursor.execute("PRAGMA table_info(calls)")
                columns = [column[1] for column in cursor.fetchall()]
                if 'end_stamp' not in columns or 'call_data' not in columns:
                    logging.info('Old table structure detected, recreating calls table...')
                    cursor.execute('DROP TABLE IF EXISTS calls')
                    table_exists = False
            
            # Таблица звонков
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
                logging.info('Created calls table')
            
            # Индексы
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_start_stamp ON calls(start_stamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_end_stamp ON calls(end_stamp)')
            
            # Таблица trunk'ов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trunks (
                    number TEXT PRIMARY KEY,
                    description TEXT,
                    trunk_data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица кеша запросов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_hash TEXT UNIQUE,
                    start_stamp INTEGER,
                    end_stamp INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица дневной статистики
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
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON daily_stats(date)')
            
            conn.commit()
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def _init_postgres(self):
        """Инициализация PostgreSQL"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Таблица звонков
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calls (
                    id TEXT PRIMARY KEY,
                    start_stamp BIGINT NOT NULL,
                    end_stamp BIGINT NOT NULL,
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
            
            # Индексы
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_start_stamp ON calls(start_stamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_end_stamp ON calls(end_stamp)')
            
            # Таблица trunk'ов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trunks (
                    number TEXT PRIMARY KEY,
                    description TEXT,
                    trunk_data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица кеша запросов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_requests (
                    id SERIAL PRIMARY KEY,
                    request_hash TEXT UNIQUE,
                    start_stamp BIGINT,
                    end_stamp BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица дневной статистики
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id SERIAL PRIMARY KEY,
                    date TEXT NOT NULL,
                    start_stamp BIGINT NOT NULL,
                    end_stamp BIGINT NOT NULL,
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
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON daily_stats(date)')
            
            conn.commit()
            logging.info("PostgreSQL schema created successfully")
        finally:
            cursor.close()
            self.release_connection(conn)


# Глобальный экземпляр адаптера
db_adapter = DatabaseAdapter()


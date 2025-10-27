#!/usr/bin/env python3
"""
Миграция для добавления таблиц рекомендательной системы
"""
import sqlite3
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

DB_PATH = 'Backend/aggregator.db'

def migrate():
    """Создает таблицы для рекомендательной системы"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Таблица для событий пользователей
        print("➕ Создаем таблицу interactions...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        
        # Индексы для быстрого доступа
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_interactions_user 
            ON interactions(user_id, ts DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_interactions_project 
            ON interactions(project_id, ts DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_interactions_event 
            ON interactions(event_type, ts DESC)
        ''')
        print("✅ Таблица interactions создана")
        
        # Таблица для логов поиска
        print("➕ Создаем таблицу search_logs...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_search_logs_user 
            ON search_logs(user_id, ts DESC)
        ''')
        print("✅ Таблица search_logs создана")
        
        # Таблица для кэша рекомендаций
        print("➕ Создаем таблицу recommendations_cache...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                score REAL NOT NULL,
                reason TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                UNIQUE(user_id, project_id)
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_recommendations_cache_user 
            ON recommendations_cache(user_id, score DESC)
        ''')
        print("✅ Таблица recommendations_cache создана")
        
        # Таблица для метрик проектов (опционально, для будущих трендов)
        print("➕ Создаем таблицу project_metrics...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                date DATE NOT NULL,
                subscribers INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                impressions INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                UNIQUE(project_id, date)
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_project_metrics 
            ON project_metrics(project_id, date DESC)
        ''')
        print("✅ Таблица project_metrics создана")
        
        # Таблица для профилей пользователей (кэш агрегированных данных)
        print("➕ Создаем таблицу user_profiles...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                profile_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("✅ Таблица user_profiles создана")
        
        conn.commit()
        print("\n✅ Миграция успешно выполнена!")
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Запуск миграции рекомендательной системы...")
    migrate()



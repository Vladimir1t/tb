#!/usr/bin/env python3
"""
Миграция для добавления полей опросника в таблицу users
"""
import sqlite3
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

DB_PATH = 'Backend/aggregator.db'

def migrate():
    """Добавляет поля preferences и survey_completed в таблицу users"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем существование столбцов
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Добавляем столбец preferences если его нет
        if 'preferences' not in columns:
            print("➕ Добавляем столбец 'preferences' в таблицу users...")
            cursor.execute("ALTER TABLE users ADD COLUMN preferences TEXT")
            print("✅ Столбец 'preferences' добавлен")
        else:
            print("ℹ️  Столбец 'preferences' уже существует")
        
        # Добавляем столбец survey_completed если его нет
        if 'survey_completed' not in columns:
            print("➕ Добавляем столбец 'survey_completed' в таблицу users...")
            cursor.execute("ALTER TABLE users ADD COLUMN survey_completed INTEGER DEFAULT 0")
            print("✅ Столбец 'survey_completed' добавлен")
        else:
            print("ℹ️  Столбец 'survey_completed' уже существует")
        
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
    print("🚀 Запуск миграции для добавления полей опросника...")
    migrate()


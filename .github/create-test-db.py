import sqlite3
import os

def create_ci_database():
    """Создает легковесную БД для CI"""
    db_path = "Backend/aggregator.db"
    
    # Удаляем если существует
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создаем структуру таблиц
    cursor.execute('''
    CREATE TABLE projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        name TEXT,
        link TEXT NOT NULL,
        theme TEXT NOT NULL,
        is_premium BOOLEAN DEFAULT 0,
        likes INTEGER DEFAULT 0,
        subscribers INTEGER DEFAULT 0,
        user_id INTEGER DEFAULT 1,
        icon BLOB
    )''')
    
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        stars INTEGER DEFAULT 0,
        balance REAL DEFAULT 0
    )''')
    
    cursor.execute('''
    CREATE TABLE tasks (
        user_id INTEGER,
        task_type TEXT,
        completed BOOLEAN DEFAULT 0,
        PRIMARY KEY (user_id, task_type)
    )''')
    
    # Добавляем 5 тестовых записей
    test_data = [
        ('channel', 'Test Channel 1', 'https://t.me/test1', 'technology', 1000),
        ('channel', 'Test Channel 2', 'https://t.me/test2', 'news', 2000),
        ('bot', 'Test Bot', 'https://t.me/bot1', 'utility', 500),
        ('channel', 'Test RU', 'https://t.me/rutest', 'russian', 1500),
        ('bot', 'Helper Bot', 'https://t.me/helper', 'service', 800)
    ]
    
    for item in test_data:
        cursor.execute('''
        INSERT INTO projects (type, name, link, theme, subscribers) 
        VALUES (?, ?, ?, ?, ?)
        ''', item)
    
    conn.commit()
    
    # Проверяем
    cursor.execute("SELECT COUNT(*) FROM projects")
    count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ CI Database created with {count} test records")
    return True

if __name__ == "__main__":
    create_ci_database()
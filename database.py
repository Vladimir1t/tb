import sqlite3
from urllib.parse import urlparse
import requests
from typing import List, Optional

def get_telegram_avatar(link: str) -> Optional[str]:
    """Получает URL аватарки Telegram канала/бота"""
    try:
        parsed = urlparse(link)
        if not parsed.netloc.endswith('t.me'):
            return None
        
        username = parsed.path.strip('/')
        if not username:
            return None
        
        avatar_url = f"https://t.me/i/userpic/320/{username}.jpg"
        response = requests.head(avatar_url, timeout=3)
        return avatar_url if response.status_code == 200 else None
    except Exception:
        return None

def init_db(db_path: str = 'aggregator.db'):
    """Инициализирует структуру базы данных"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Сначала проверяем существование столбца icon
    cursor.execute("PRAGMA table_info(projects)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Создаем таблицы с учетом возможного существования
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        name TEXT NOT NULL,
        link TEXT NOT NULL,
        theme TEXT NOT NULL,
        is_premium BOOLEAN DEFAULT 0,
        likes INTEGER DEFAULT 0,
        subscribers INTEGER DEFAULT 0,
        user_id INTEGER DEFAULT 1,
        icon TEXT
    )''')
    
    # Если столбца icon нет - добавляем
    if 'icon' not in columns:
        try:
            cursor.execute('ALTER TABLE projects ADD COLUMN icon TEXT')
        except sqlite3.OperationalError as e:
            print(f"Could not add icon column: {e}")

    # Остальные таблицы
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        stars INTEGER DEFAULT 0,
        balance REAL DEFAULT 0
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        user_id INTEGER,
        task_type TEXT,
        completed BOOLEAN DEFAULT 0,
        PRIMARY KEY (user_id, task_type)
    )''')
    
    
    # Добавляем тестовые данные, если таблица пуста
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        test_data = [
            ('channel', 'Хабр', 'https://t.me/habr_com', 'программирование', 1, 100, 122000, 1, get_telegram_avatar('https://t.me/habr_com')),
            ('channel', 'Новости Москвы', 'https://t.me/moscowmap', 'новости', 0, 50, 2730000, 1, get_telegram_avatar('https://t.me/moscowmap')),
            ('channel', 'Книга животных', 'https://t.me/knigajivotnih1', 'природа', 0, 50, 15000, 1, get_telegram_avatar('https://t.me/miptru')),
            ('channel', 'МФТИ', 'https://t.me/miptru', 'вузы', 0, 50, 15000, 1, get_telegram_avatar('https://t.me/truecatharsis')),
            ('channel', 'ТРУСЫ РАЙЗА', 'https://t.me/raiznews', 'Cs2', 0, 50, 335000, 1, get_telegram_avatar('https://t.me/raiznews')),
            ('channel', 'Банки, деньги, два офшора', 'https://t.me/bankrollo', 'экономика', 0, 50, 15000, 1, get_telegram_avatar('https://t.me/bankrollo')),
            ('channel', 'МЯЧ Production', 'https://t.me/myachPRO', 'футбол', 0, 50, 260000, 1, get_telegram_avatar('https://t.me/myachPRO')),
            ('channel', 'Фонтанка SPB Online', 'https://t.me/fontankaspb', 'новости', 0, 50, 350000, 1, get_telegram_avatar('https://t.me/fontankaspb')),
            ('channel', 'Real Madrid CF | Реал Мадрид', 'https://t.me/realmadridcdf', 'футбол', 0, 50, 280000, 1, get_telegram_avatar('https://t.me/realmadridcdf')),
            ('channel', 'Бестиарий', 'https://t.me/bestiariy_mif', 'искусство', 0, 50, 65000, 1, get_telegram_avatar('https://t.me/bestiariy_mif')),
            ('channel', 'OverDrive | 20 ЛЕТ В АРКАДЕ', 'https://t.me/ihuntnoobs', 'киберспорт', 0, 50, 205000, 1, get_telegram_avatar('https://t.me/ihuntnoobs')),
            ('channel', 'Белый Лебедь • Про Бизнес и Финансы', 'https://t.me/SwamCapital', 'экономика', 0, 50, 40000, 1, get_telegram_avatar('https://t.me/bestiariy_mif')),
            ('channel', 'catharsis', 'https://t.me/truecatharsis', 'art', 0, 50, 15000, 1, get_telegram_avatar('https://t.me/truecatharsis')),
            ('channel', 'Формула-1 | Прямые трансляции', 'https://t.me/f1_sports', 'гонки', 0, 50, 55000, 1, get_telegram_avatar('https://t.me/f1_sports')),
            ('channel', 'Семнадцатый номер', 'https://t.me/deginc17', 'футбол', 0, 50, 30000, 1, get_telegram_avatar('https://t.me/deginc17')),
            ('bot', 'Погодный Бот', 'https://t.me/weather_bot', 'utility', 0, 30, 5000, 1, get_telegram_avatar('https://t.me/weather_bot')),
            ('bot', 'Финансовый помощник', 'https://t.me/finance_bot', 'finance', 1, 80, 18000, 1, get_telegram_avatar('https://t.me/finance_bot')),
            ('mini_app', 'Головоломки', 'https://t.me/puzzle_app', 'games', 0, 20, 8000, 1, get_telegram_avatar('https://t.me/puzzle_app'))
        ]
        
        for item in test_data:
            icon = get_telegram_avatar(item[2])
            cursor.execute('''
                INSERT INTO projects 
                (type, name, link, theme, is_premium, likes, subscribers, user_id, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*item, icon))
    
    conn.commit()
    conn.close()



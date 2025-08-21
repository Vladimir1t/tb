import sqlite3
import asyncio
from telethon import TelegramClient
from telethon.errors import RPCError, UsernameInvalidError
from typing import Optional
import threading

API_ID = 23018155
API_HASH = '59054196d2bcd74bbd30b4415f66bfd2'
SESSION_NAME = 'session_1'
BOT_TOKEN = "8143528604:AAEiouPy36hamVNvQhJK3ptZsiaUXJjkwIs"
DB_NAME = 'aggregator.db'

def _run_in_thread(coro):
    """Запускает корутину в отдельном потоке с новым event loop"""
    result = None
    def run():
        nonlocal result
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coro)
        finally:
            loop.close()
    
    thread = threading.Thread(target=run)
    thread.start()
    thread.join()
    return result

async def _get_avatar_bytes(username: str) -> Optional[bytes]:
    """Асинхронно получает аватарку канала"""
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        await client.start(bot_token=BOT_TOKEN) 
        try:
            entity = await client.get_entity(username)
            return await client.download_profile_photo(entity, file=bytes)
        except Exception as e:
            print(f"Ошибка при получении аватара для {username}: {e}")
            return None

async def get_channel_name(username: str) -> Optional[str]:
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        await client.start(bot_token=BOT_TOKEN)
        try:
            entity = await client.get_entity(username)
            return entity.title if hasattr(entity, "title") else entity.username
        except RPCError as e:
            print(f"Ошибка при получении имени для {username}: {e}")
            return None


def get_avatar_bytes_sync(username: str) -> Optional[bytes]:
    """Синхронная обертка для получения аватарки"""
    return _run_in_thread(_get_avatar_bytes(username))

def get_channel_name_sync(username: str) -> Optional[str]:
    return _run_in_thread(get_channel_name(username))


def init_db(db_path: str = DB_NAME):
    """Инициализирует структуру базы данных"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
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

    # cursor.execute("SELECT COUNT(*) FROM projects") 
    # if cursor.fetchone()[0] == 0:
    #     test_data = [
    #         ('channel', 'Хабр', 'https://t.me/habr_com', 'программирование', 1, 100, 122000, 1, 'habr_com'),
    #         ('channel', 'Новости Москвы', 'https://t.me/moscowmap', 'новости', 0, 50, 2730000, 1, 'moscowmap'),
    #         ('channel', 'Книга животных', 'https://t.me/knigajivotnih1', 'природа', 0, 50, 15000, 1, 'miptru'),
    #         ('channel', 'МФТИ', 'https://t.me/miptru', 'вузы', 0, 50, 15000, 1, 'truecatharsis'),
    #         ('channel', 'ТРУСЫ РАЙЗА', 'https://t.me/raiznews', 'Cs2', 0, 50, 335000, 1, 'raiznews'),
    #         ('channel', 'Банки, деньги, два офшора', 'https://t.me/bankrollo', 'экономика', 0, 50, 15000, 1, 'bankrollo'),
    #         ('channel', 'МЯЧ Production', 'https://t.me/myachPRO', 'футбол', 0, 50, 260000, 1, 'myachPRO'),
    #         ('channel', 'Фонтанка SPB Online', 'https://t.me/fontankaspb', 'новости', 0, 50, 350000, 1, 'fontankaspb'),
    #         ('channel', 'Real Madrid CF | Реал Мадрид', 'https://t.me/realmadridcdf', 'футбол', 0, 50, 280000, 1, 'realmadridcdf'),
    #         ('channel', 'Бестиарий', 'https://t.me/bestiariy_mif', 'искусство', 0, 50, 65000, 1, 'bestiariy_mif'),
    #         ('channel', 'OverDrive | 20 ЛЕТ В АРКАДЕ', 'https://t.me/ihuntnoobs', 'киберспорт', 0, 50, 205000, 1, 'ihuntnoobs'),
    #         ('channel', 'Белый Лебедь • Про Бизнес и Финансы', 'https://t.me/SwamCapital', 'экономика', 0, 50, 40000, 1, 'bestiariy_mif'),
    #         ('channel', 'catharsis', 'https://t.me/truecatharsis', 'art', 0, 50, 15000, 1, 'truecatharsis'),
    #         ('channel', 'Формула-1 | Прямые трансляции', 'https://t.me/f1_sports', 'гонки', 0, 50, 55000, 1, 'f1_sports'),
    #         ('channel', 'Семнадцатый номер', 'https://t.me/deginc17', 'футбол', 0, 50, 30000, 1, 'deginc17'),
    #         ('bot', 'Погодный Бот', 'https://t.me/weather_bot', 'utility', 0, 30, 5000, 1, 'weather_bot'),
    #         ('bot', 'Финансовый помощник', 'https://t.me/finance_bot', 'finance', 1, 80, 18000, 1, 'finance_bot'),
    #         ('mini_app', 'Головоломки', 'https://t.me/puzzle_app', 'games', 0, 20, 8000, 1, 'puzzle_app')
    #     ]
        
    #     for item in test_data:
    #         avatar_bytes = get_avatar_bytes_sync(item[-1])
    #         cursor.execute('''
    #             INSERT INTO projects 
    #             (type, name, link, theme, is_premium, likes, subscribers, user_id, icon)
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    #         ''', (*item[:-1], avatar_bytes))
    
    # conn.commit()
    # conn.close()


    cursor.execute("SELECT COUNT(*) FROM projects") 
    if cursor.fetchone()[0] == 0:
        test_data = [
            ('channel', 'habr_com', 'программирование'),
            ('channel', 'moscowmap', 'новости'),
            ('channel', 'knigajivotnih1', 'природа'),
            ('channel', 'miptru', 'вузы'),
            ('channel', 'raiznews', 'Cs2'),
            ('channel', 'bankrollo', 'экономика'),
            ('channel', 'myachPRO', 'футбол'),
            ('channel', 'fontankaspb', 'новости'),
            ('channel', 'realmadridcdf', 'футбол'),
            ('channel', 'bestiariy_mif', 'искусство'),
            ('channel', 'ihuntnoobs', 'киберспорт'),
            ('channel', 'SwamCapital', 'экономика'),
            ('channel', 'truecatharsis', 'art'),
            ('channel', 'f1_sports', 'гонки'),
            ('channel', 'deginc17', 'футбол', 'deginc17'),
            ('bot', 'weather_bot', 'utility'),
            ('bot', 'finance_bot', 'finance'),
            ('mini_app', 'puzzle_app', 'games')
        ]
        
        for item in test_data:
            avatar_bytes = get_avatar_bytes_sync(item[1])
            channel_name = get_channel_name_sync(item[1])
            cursor.execute('''
                INSERT INTO projects 
                (type, name, link, theme, is_premium, likes, subscribers, user_id, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item[0], 
                  channel_name or "default",
                  f"https://t.me/{item[1]}",
                  item[2],
                  0,
                  0, 
                  0,
                  0,
                  avatar_bytes))
    conn.commit()
    conn.close()
import sqlite3
import asyncio
from telethon import TelegramClient
from telethon.errors import RPCError, UsernameInvalidError
from telethon.tl.functions.channels import GetFullChannelRequest
from typing import Optional
import threading
import os

from Backend.scripts.database_data import data


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

async def get_subscribers_count(username: str) -> int:
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        await client.start(bot_token=BOT_TOKEN)
        try:
            entity = await client.get_entity(username)
            full = await client(GetFullChannelRequest(channel=entity))
            return full.full_chat.participants_count
        except RPCError as e:
            print(f"Ошибка RPC при получении участников {username}: {e}")
            return 0
        except Exception as e:
            print(f"Ошибка при получении участников {username}: {e}")
            return 0

def get_subscribers_count_sync(username: str) -> int:
    return _run_in_thread(get_subscribers_count(username))

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

    cursor.execute("SELECT COUNT(*) FROM projects") 
    if cursor.fetchone()[0] == 0:
        
        for item in data:
            avatar_bytes = get_avatar_bytes_sync(item[1])
            channel_name = get_channel_name_sync(item[1])
            subscribers = get_subscribers_count_sync(item[1])
            cursor.execute('''
                INSERT INTO projects 
                (type, name, link, theme, is_premium, likes, subscribers, user_id, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item[0], 
                  channel_name,
                  f"https://t.me/{item[1]}",
                  item[2],
                  0,
                  0, 
                  subscribers,
                  0,
                  avatar_bytes))

    conn.commit()

    # # Загружаем модель для эмбеддингов
    # model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    # # Подключаемся к базе
    # conn = sqlite3.connect("aggregator.db")
    # cursor = conn.cursor()

    # # === 1. Создаём таблицу для эмбеддингов ===
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS project_embeddings (
    #     project_id INTEGER PRIMARY KEY,
    #     vector BLOB
    # );
    # """)
    # conn.commit()

    # # === 2. Заполняем эмбеддинги для всех проектов ===
    # cursor.execute("SELECT id, name, theme FROM projects;")
    # rows = cursor.fetchall()

    # for project_id, name, theme in rows:
    #     text = f"{name or ''} {theme or ''}"
    #     vector = model.encode([text])[0].astype("float32")
    #     blob = vector.tobytes()
    #     cursor.execute("INSERT OR REPLACE INTO project_embeddings (project_id, vector) VALUES (?, ?)", (project_id, blob))

    # conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
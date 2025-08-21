import sqlite3
import asyncio
from telethon import TelegramClient
from telethon.errors import RPCError, UsernameInvalidError
from telethon.tl.functions.channels import GetFullChannelRequest
from typing import Optional, Tuple
import threading
import os

API_ID = 23018155
API_HASH = '59054196d2bcd74bbd30b4415f66bfd2'
SESSION_NAME = 'session_1'
BOT_TOKEN = "8143528604:AAEiouPy36hamVNvQhJK3ptZsiaUXJjkwIs"
DB_NAME = 'aggregator.db'

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
            ('mini_app', 'puzzle_app', 'games'),
            ('channel', 'tsiskaridzenews', 'искусство'),
            ('channel', 'moscowach', 'новости'),
            ('channel', 'yuriyshatunov_live', 'музыка'),
            ('channel', 'nikitanya713', 'химия'),
            ('channel', 'ahmatova_anna1', 'литература'),
]

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


async def get_channel_info(username: str) -> Tuple[Optional[bytes], Optional[str], int]:
    """Возвращает аватарку, имя и количество участников канала"""
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        await client.start(bot_token=BOT_TOKEN)
        avatar_bytes = None
        channel_name = None
        subscribers_count = 0

        try:
            entity = await client.get_entity(username)
            
            # Получаем аватар
            try:
                avatar_bytes = await client.download_profile_photo(entity, file=bytes)
            except Exception as e:
                print(f"Ошибка при получении аватара для {username}: {e}")

            # Получаем имя
            channel_name = entity.title if hasattr(entity, "title") else entity.username

            # Получаем количество подписчиков
            try:
                full = await client(GetFullChannelRequest(channel=entity))
                subscribers_count = full.full_chat.participants_count
            except RPCError as e:
                print(f"Ошибка RPC при получении участников {username}: {e}")
            except Exception as e:
                print(f"Ошибка при получении участников {username}: {e}")

        except RPCError as e:
            print(f"Ошибка при получении entity {username}: {e}")
        except Exception as e:
            print(f"Общая ошибка при работе с {username}: {e}")

        return avatar_bytes, channel_name, subscribers_count

def get_channel_info_sync(username: str) -> Tuple[Optional[bytes], Optional[str], int]:
    return _run_in_thread(get_channel_info(username))


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
        
        for item in test_data:
            avatar, name, subs = get_channel_info_sync(item[1])
            cursor.execute('''
                INSERT INTO projects 
                (type, name, link, theme, is_premium, likes, subscribers, user_id, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item[0], 
                  name,
                  f"https://t.me/{item[1]}",
                  item[2],
                  0,
                  0, 
                  subs,
                  0,
                  avatar))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
import sqlite3
import asyncio
from telethon import TelegramClient
from telethon.errors import RPCError, UsernameInvalidError
from telethon.tl.functions.channels import GetFullChannelRequest
from typing import Optional, Tuple
from telethon.errors import RPCError, FloodWaitError
import threading
import time
import random
import os
from datetime import datetime, timedelta

from scripts import database_data

API_ID = 23018155
API_HASH = '59054196d2bcd74bbd30b4415f66bfd2'
SESSION_NAME = 'session_1'
BOT_TOKEN = "7864050009:AAEvftlbWNqYPFYt-F8_fHxdAa1YNn_aego"
DB_NAME = 'Backend/aggregator.db'

_request_lock = threading.Lock()
_last_request_time = 0
_flood_wait_times = {}


_flood_wait_times = {}

def shuffle_database(db_path: str = DB_NAME):
    """Случайным образом перемешивает все записи в таблице projects"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем все записи из таблицы projects
        cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()
        
        # Получаем названия колонок
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Перемешиваем записи
        random.shuffle(rows)
        
        # Очищаем таблицу
        cursor.execute("DELETE FROM projects")
        
        # Вставляем перемешанные записи
        for row in rows:
            # Создаем словарь для удобной вставки
            row_dict = dict(zip(columns, row))
            
            cursor.execute('''
                INSERT INTO projects 
                (type, name, link, theme, is_premium, likes, subscribers, user_id, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row_dict['type'],
                row_dict['name'],
                row_dict['link'],
                row_dict['theme'],
                row_dict['is_premium'],
                row_dict['likes'],
                row_dict['subscribers'],
                row_dict['user_id'],
                row_dict['icon']
            ))
        
        conn.commit()
        print(f"✅ База данных перемешана! Перемешанно {len(rows)} записей")
        
    except Exception as e:
        print(f"❌ Ошибка при перемешивании БД: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

def _run_in_thread(coro):
    """Запускает корутину в отдельном потоке с новым event loop"""
    result = None
    def run():
        nonlocal result
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coro)
        except Exception as e:
            print(f"Ошибка в потоке: {e}")
            result = (None, None, 0) 
        finally:
            loop.close()
    
    thread = threading.Thread(target=run)
    thread.start()
    thread.join()
    return result

def should_skip_due_to_flood_wait(username: str) -> bool:
    """Проверяет, нужно ли пропустить канал из-за flood wait"""
    if username in _flood_wait_times:
        wait_until = _flood_wait_times[username]
        if datetime.now() < wait_until:
            remaining = (wait_until - datetime.now()).total_seconds()
            print(f"⏳ Пропускаем {username} из-за flood wait, осталось {remaining:.0f} сек")
            return True
        else:
            del _flood_wait_times[username]
    return False

async def _get_avatar_bytes_with_client(username: str, client: TelegramClient) -> Optional[bytes]:
    """Асинхронно получает аватарку канала"""
    try:
        entity = await client.get_entity(username)
        avatar = await client.download_profile_photo(entity, file=bytes)
        print(f"✓ Аватар получен для {username}")
        return avatar
    except FloodWaitError as e:
        print(f"⏳ Flood wait для {username}: {e.seconds} секунд")
        # Сохраняем время, до которого нужно ждать
        wait_until = datetime.now() + timedelta(seconds=e.seconds + 60)  
        _flood_wait_times[username] = wait_until
        return None
    except Exception as e:
        print(f"❌ Ошибка аватара для {username}: {e}")
        return None

async def get_channel_name_with_client(username: str, client: TelegramClient) -> Optional[str]:
    try:
        entity = await client.get_entity(username)
        name = entity.title if hasattr(entity, "title") else entity.username
        print(f"✓ Имя получено для {username}: {name}")
        return name
    except FloodWaitError as e:
        print(f"⏳ Flood wait для {username}: {e.seconds} секунд")
        wait_until = datetime.now() + timedelta(seconds=e.seconds + 60)
        _flood_wait_times[username] = wait_until
        return username  
    except Exception as e:
        print(f"❌ Ошибка имени для {username}: {e}")
        return username

async def get_subscribers_count_with_client(username: str, client: TelegramClient) -> int:
    try:
        entity = await client.get_entity(username)
        full = await client(GetFullChannelRequest(channel=entity))
        count = full.full_chat.participants_count
        print(f"✓ Подписчики получены для {username}: {count}")
        return count
    except FloodWaitError as e:
        print(f"⏳ Flood wait для {username}: {e.seconds} секунд")
        wait_until = datetime.now() + timedelta(seconds=e.seconds + 60)
        _flood_wait_times[username] = wait_until
        return 0
    except Exception as e:
        print(f"❌ Ошибка подписчиков для {username}: {e}")
        return 0

def get_telegram_data_sync(username: str) -> Tuple[Optional[bytes], Optional[str], int]:
    """Получает все данные для одного канала"""
    
    if should_skip_due_to_flood_wait(username):
        return None, username, 0
    
    async def get_all_data():
        global _last_request_time
        
        with _request_lock:
            current_time = time.time()
            if _last_request_time > 0:
                time_to_wait = max(0, 4 - (current_time - _last_request_time))
                if time_to_wait > 0:
                    print(f"⏸️  Ожидание {time_to_wait:.1f} сек перед запросом {username}")
                    await asyncio.sleep(time_to_wait)
            
            _last_request_time = time.time()
        
        # Создаем нового клиента для каждого запроса
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        
        try:
            await client.start(bot_token=BOT_TOKEN)
            
            avatar_bytes = await _get_avatar_bytes_with_client(username, client)
            channel_name = await get_channel_name_with_client(username, client)
            subscribers = await get_subscribers_count_with_client(username, client)
            
            return avatar_bytes, channel_name, subscribers
            
        except FloodWaitError as e:
            print(f"⏳ Серьезный Flood wait для {username}: {e.seconds} секунд")
            wait_until = datetime.now() + timedelta(seconds=e.seconds + 60)
            _flood_wait_times[username] = wait_until
            return None, username, 0
            
        except Exception as e:
            print(f"❌ Критическая ошибка для {username}: {e}")
            return None, username, 0
            
        finally:
            try:
                if client.is_connected():
                    await client.disconnect()
            except:
                pass
    
    return _run_in_thread(get_all_data())

def add_new_chanels(db_path: str = DB_NAME):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM projects")
    count = cursor.fetchone()[0]
       
    if not data:
        print("⚠️  Нет данных для инициализации")
        return
    
    print(f"🚀 Начинаем загрузку данных для {len(data)} каналов...")
    print("⚠️  ВНИМАНИЕ: Процесс может занять несколько часов из-за ограничений Telegram API")
    
    successful = 0
    skipped = 0
    
    for i, item in enumerate(data, 1):
        username = item[1]
        print(f"\n📊 Обрабатываем канал {i}/{len(data)}: {username}")

        cursor.execute("SELECT 1 FROM projects WHERE link = ?", (f"https://t.me/{username}",))
        if cursor.fetchone():
            print(f"⚠️  Канал {username} уже есть в базе, пропускаем")
            skipped += 1
            continue
        
        result = get_telegram_data_sync(username)
        
        if result is None:
            print(f"⚠️  Не удалось получить данные для {username}, пропускаем")
            skipped += 1
            continue
            
        avatar_bytes, channel_name, subscribers = result
        
        if username in _flood_wait_times:
            print(f"⏳ Пропускаем вставку {username} из-за flood wait")
            skipped += 1
            continue
        
        if not channel_name:
            channel_name = username
        
        cursor.execute('''
            INSERT INTO projects 
            (type, name, link, theme, is_premium, likes, subscribers, user_id, icon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item[0], 
            channel_name,
            f"https://t.me/{username}",
            item[2],
            0,
            0, 
            subscribers,
            0,
            avatar_bytes
        ))
        
        conn.commit()
        successful += 1
        print(f"✅ Завершено: {i}/{len(data)} - {channel_name}")
        print(f"📈 Успешно: {successful}, Пропущено: {skipped}")
        
        if i < len(data):
            delay = random.uniform(1, 2)
            print(f"⏸️  Длинная пауза {delay:.1f} сек перед следующим каналом")
            time.sleep(delay)


def init_db(db_path: str = DB_NAME):
    """Инициализирует структуру базы данных"""
    try:
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

        # Проверяем, нужно ли заполнять данными
        cursor.execute("SELECT COUNT(*) FROM projects")
        count = cursor.fetchone()[0]
        
        if count == 0:
        
            if not data:
                print("⚠️  Нет данных для инициализации")
                return
            
            print(f"🚀 Начинаем загрузку данных для {len(data)} каналов...")
            print("⚠️  ВНИМАНИЕ: Процесс может занять несколько часов из-за ограничений Telegram API")
            
            successful = 0
            skipped = 0
            
            for i, item in enumerate(data, 1):
                username = item[1]
                print(f"\n📊 Обрабатываем канал {i}/{len(data)}: {username}")
                
                # Получаем данные с задержками
                result = get_telegram_data_sync(username)
                
                # Проверяем, что результат не None
                if result is None:
                    print(f"⚠️  Не удалось получить данные для {username}, пропускаем")
                    skipped += 1
                    continue
                    
                avatar_bytes, channel_name, subscribers = result
                
                # Если канал пропущен из-за flood wait
                if username in _flood_wait_times:
                    print(f"⏳ Пропускаем вставку {username} из-за flood wait")
                    skipped += 1
                    continue
                
                # Если не удалось получить имя, используем username
                if not channel_name:
                    channel_name = username
                
                cursor.execute('''
                    INSERT INTO projects 
                    (type, name, link, theme, is_premium, likes, subscribers, user_id, icon)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item[0], 
                    channel_name,
                    f"https://t.me/{username}",
                    item[2],
                    0,
                    0, 
                    subscribers,
                    0,
                    avatar_bytes
                ))
                
                conn.commit()
                successful += 1
                print(f"✅ Завершено: {i}/{len(data)} - {channel_name}")
                print(f"📈 Успешно: {successful}, Пропущено: {skipped}")
                
                # Увеличиваем задержку между каналами до 15-30 секунд
                if i < len(data):
                    delay = random.uniform(2, 3)
                    print(f"⏸️  Длинная пауза {delay:.1f} сек перед следующим каналом")
                    time.sleep(delay)
        
        else:
            print("✅ База данных уже инициализирована")
            
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()
        print("🏁 Инициализация завершена")

def remove_duplicate_channels(db_path: str = DB_NAME):
    """Удаляет повторяющиеся каналы/боты из базы данных по полю link"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Сначала посчитаем общее количество записей
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_before = cursor.fetchone()[0]
        
        print(f"🔍 Поиск дубликатов в базе данных...")
        print(f"📊 Всего записей до очистки: {total_before}")
        
        # Находим дубликаты по полю link
        cursor.execute('''
            SELECT link, COUNT(*) as count 
            FROM projects 
            GROUP BY link 
            HAVING COUNT(*) > 1
        ''')
        duplicates = cursor.fetchall()
        
        if not duplicates:
            print("✅ Дубликаты не найдены")
            return
        
        print(f"📋 Найдено {len(duplicates)} ссылок с дубликатами:")
        
        total_duplicates_to_remove = 0
        
        for link, count in duplicates:
            print(f"   {link}: {count} записей")
            total_duplicates_to_remove += (count - 1)
        
        print(f"🗑️  Всего будет удалено {total_duplicates_to_remove} дубликатов")
        
        # Удаляем дубликаты, оставляя только первую запись для каждого link
        cursor.execute('''
            DELETE FROM projects 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM projects 
                GROUP BY link
            )
        ''')
        
        conn.commit()
        
        # Проверяем результат
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_after = cursor.fetchone()[0]
        
        removed_count = total_before - total_after
        
        print(f"✅ Очистка завершена!")
        print(f"📊 Статистика:")
        print(f"   • Было записей: {total_before}")
        print(f"   • Стало записей: {total_after}")
        print(f"   • Удалено дубликатов: {removed_count}")
        
        # Проверяем, что дубликатов больше нет
        cursor.execute('''
            SELECT COUNT(*) 
            FROM (
                SELECT link 
                FROM projects 
                GROUP BY link 
                HAVING COUNT(*) > 1
            )
        ''')
        remaining_duplicates = cursor.fetchone()[0]
        
        if remaining_duplicates == 0:
            print("✅ Все дубликаты успешно удалены!")
        else:
            print(f"⚠️  Осталось {remaining_duplicates} групп дубликатов")
            
    except Exception as e:
        print(f"❌ Ошибка при удалении дубликатов: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # add_new_chanels()
    # shuffle_database()
    remove_duplicate_channels()
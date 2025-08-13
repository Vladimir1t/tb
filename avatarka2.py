import sqlite3
import asyncio
from telethon import TelegramClient

# -----------------------------
# 1️⃣ Настройки Telegram
# -----------------------------
api_id = 23018155          # вставь свой api_id
api_hash = '59054196d2bcd74bbd30b4415f66bfd2'    # вставь свой api_hash
session_name = 'session_1' # имя сессии Telethon

# -----------------------------
# 2️⃣ Настройка базы данных
# -----------------------------
db_name = 'channels.db'

def init_db():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Таблица с каналами
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        avatar BLOB,
        last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица с списком каналов для проверки
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS channel_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE
    )
    ''')
    
    conn.commit()
    conn.close()

# -----------------------------
# 3️⃣ Функция скачивания аватарки и сохранения в БД
# -----------------------------
async def save_avatar_to_db(client, channel_username):
    try:
        channel = await client.get_entity(channel_username)
        avatar_bytes = await client.download_profile_photo(channel, file=bytes)

        if avatar_bytes:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO channels (username, avatar)
            VALUES (?, ?)
            ON CONFLICT(username) DO UPDATE SET
                avatar=excluded.avatar,
                last_update=CURRENT_TIMESTAMP
            ''', (channel_username, avatar_bytes))
            conn.commit()
            conn.close()
            print(f"[OK] Аватарка канала {channel_username} сохранена/обновлена")
        else:
            print(f"[INFO] У канала {channel_username} нет аватарки")
    except Exception as e:
        print(f"[ERROR] Канал {channel_username}: {e}")

# -----------------------------
# 4️⃣ Основной цикл
# -----------------------------
async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()
    
    # Получаем список каналов из базы
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM channel_list")
    channel_rows = cursor.fetchall()
    conn.close()
    
    channel_list = [row[0] for row in channel_rows]
    
    if not channel_list:
        print("[INFO] Нет каналов для обработки. Добавьте их в таблицу channel_list.")
        await client.disconnect()
        return
    
    for username in channel_list:
        await save_avatar_to_db(client, username)
    
    await client.disconnect()

# -----------------------------
# 5️⃣ Запуск
# -----------------------------
if __name__ == "__main__":
    init_db()
    asyncio.run(main())

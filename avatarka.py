from telethon import TelegramClient
import asyncio

# 1️⃣ Вставь свои данные из my.telegram.org
api_id = 23018155         # число
api_hash = '59054196d2bcd74bbd30b4415f66bfd2'   # строка

# 2️⃣ Юзернейм канала (без @)
channel_username = 'habr_com'

# 3️⃣ Имя файла для сохранения аватарки
output_file = 'habr.jpg'

# Создаем клиент Telethon
client = TelegramClient('session_name', api_id, api_hash)

async def download_avatar():
    await client.start()  # Запуск клиента (нужно будет подтвердить телефон)
    
    try:
        # Получаем объект канала
        channel = await client.get_entity(channel_username)
        
        # Скачиваем аватарку
        result = await client.download_profile_photo(channel, file=output_file)
        
        if result:
            print(f"Аватарка успешно сохранена как {output_file}")
        else:
            print("У канала нет аватарки")
    except Exception as e:
        print(f"Ошибка: {e}")

# Запуск асинхронного скрипта
asyncio.run(download_avatar())

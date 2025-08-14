import sqlite3

# Подключаемся к базе
conn = sqlite3.connect('channels.db')
cursor = conn.cursor()

# Добавляем каналы (без @)
channels_to_add = [
    'miptru',
    'raiznews',
    'bankrollo',
    'myachPRO',
    'fontankaspb',
    'realmadridcdf',
    'bestiariy_mif',
    'ihuntnoobs',
    'SwamCapital',
    'truecatharsis',
    'f1_sports',
    'deginc17'
    ]

for username in channels_to_add:
    cursor.execute("INSERT OR IGNORE INTO channel_list (username) VALUES (?)", (username,))

conn.commit()
conn.close()
print("Каналы добавлены в таблицу channel_list")

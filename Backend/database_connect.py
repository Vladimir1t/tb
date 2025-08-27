# database.py
import sqlite3

def get_db_connection():
    """Создает и возвращает соединение с базой данных."""
    conn = sqlite3.connect('aggregator.db')
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к столбцам по имени
    return conn
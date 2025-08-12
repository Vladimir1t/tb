import sqlite3

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        """Создаем таблицы в базе данных с правильными столбцами"""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            stars INTEGER DEFAULT 0,
            balance REAL DEFAULT 0
        )
        """)
        
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            project_type TEXT,
            name TEXT,
            link TEXT,
            theme TEXT,
            is_premium BOOLEAN DEFAULT 0,
            likes INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """)
        
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            user_id INTEGER,
            task_type TEXT,
            completed BOOLEAN DEFAULT 0,
            PRIMARY KEY (user_id, task_type)
        )
        """)
        self.connection.commit()

    def add_user(self, user_id, username):
        """Добавляем нового пользователя"""
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        self.connection.commit()

    def get_user_info(self, user_id):
        """Получаем информацию о пользователе и количество его проектов"""
        # Получаем базовую информацию о пользователе
        self.cursor.execute(
            "SELECT stars, balance FROM users WHERE user_id = ?",
            (user_id,)
        )
        user_data = self.cursor.fetchone()
        
        if not user_data:
            return None
            
        # Получаем количество проектов пользователя
        self.cursor.execute(
            "SELECT COUNT(*) FROM projects WHERE user_id = ?",
            (user_id,)
        )
        projects_count = self.cursor.fetchone()[0]
        
        return {
            'stars': user_data[0],
            'balance': user_data[1],
            'projects_count': projects_count
        }

    def get_available_chanals(self, user_id):
        """Получаем список каналов для подписки"""
        chanals = []
        self.cursor.execute(
            "SELECT task_type FROM tasks WHERE user_id = ? AND completed = 0",  ##исправить
            (user_id,)
        )
        # chanals_db = [row[0] for row in self.cursor.fetchall()]
        
        if "subscribe" not in chanals_db:
            chanals.append({"id": "subscribe", "description": "Подписаться на канал",  "reward": "https://t.me/+O2g2YKynlB1jNGEy"})
            
        return chanals

    def get_available_tasks(self, user_id):
        """Получаем доступные задания для пользователя"""
        tasks = []
        self.cursor.execute(
            "SELECT task_type FROM tasks WHERE user_id = ? AND completed = 0",
            (user_id,)
        )
        completed_tasks = [row[0] for row in self.cursor.fetchall()]
        
        if "subscribe" not in completed_tasks:
            tasks.append({"id": "subscribe", "description": "Подписаться на канал", "reward": 3})
        if "invite" not in completed_tasks:
            tasks.append({"id": "invite", "description": "Пригласить друга", "reward": 10})
        
        return chanals

    def complete_task(self, user_id, task_type):
        """Отмечаем задание как выполненное"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO tasks (user_id, task_type, completed) VALUES (?, ?, 1)",
            (user_id, task_type)
        )
        self.cursor.execute(
            "UPDATE users SET stars = stars + ? WHERE user_id = ?",
            (5 if task_type == "banner" else 3 if task_type == "subscribe" else 10, user_id)
        )
        self.connection.commit()
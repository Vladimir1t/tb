from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List, Optional
import uvicorn
from fastapi import Request
import hmac
import hashlib
import requests
from urllib.parse import urlparse
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class Project(BaseModel):
    id: int = None
    icon: Optional[str] = None
    type: str
    name: str
    link: str
    theme: str
    is_premium: bool = False
    likes: int = 0
    subscribers: int = 0

class User(BaseModel):
    id: int
    username: Optional[str] = None
    stars: int = 0
    balance: float = 0
    projects_count: int = 0

    class Config:
        json_encoders = {type(None): lambda _: None}

# Функция для получения аватарки. пока не работает 
def get_telegram_avatar(link: str) -> Optional[str]:
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
    except Exception as e:
        logger.error(f"Error getting avatar: {str(e)}")
        return None

# Инициализация БД
def init_db():
    conn = sqlite3.connect('aggregator.db')
    cursor = conn.cursor()
    
    # Создаем таблицы (если они не существуют)
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
    
    # Проверяем существование столбца icon (для уже созданных таблиц)
    try:
        cursor.execute("SELECT icon FROM projects LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE projects ADD COLUMN icon TEXT')
    
    # Остальные таблицы...
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
    
    # данные без sqlite
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        test_data = [
            ('channel', 'Хабр', 'https://t.me/habr_com', 'technology', 1, 100, 122000, 1, get_telegram_avatar('https://t.me/habr_com')),
            ('channel', 'Новости Москвы', 'https://t.me/moscowmap', 'news', 0, 50, 2730000, 1, get_telegram_avatar('https://t.me/moscowmap')),
            ('channel', 'Книга животных', 'https://t.me/knigajivotnih1', 'animals', 0, 50, 15000, 1, get_telegram_avatar('https://t.me/miptru')),
            ('channel', 'МФТИ', 'https://t.me/miptru', 'university', 0, 50, 15000, 1, get_telegram_avatar('https://t.me/truecatharsis')),
            ('channel', 'catharsis', 'https://t.me/truecatharsis', 'art', 0, 50, 15000, 1, get_telegram_avatar('https://t.me/truecatharsis')),
            ('bot', 'Погодный Бот', 'https://t.me/weather_bot', 'utility', 0, 30, 5000, 1, get_telegram_avatar('https://t.me/weather_bot')),
            ('bot', 'Финансовый помощник', 'https://t.me/finance_bot', 'finance', 1, 80, 18000, 1, get_telegram_avatar('https://t.me/finance_bot')),
            ('mini_app', 'Головоломки', 'https://t.me/puzzle_app', 'games', 0, 20, 8000, 1, get_telegram_avatar('https://t.me/puzzle_app'))
        ]
        
        cursor.executemany('''
            INSERT INTO projects 
            (type, name, link, theme, is_premium, likes, subscribers, user_id, icon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_data)
    
    conn.commit()
    conn.close()

init_db()

# Валидация Telegram WebApp
def validate_telegram_data(token: str, init_data: str):
    try:
        secret = hmac.new(
            key=hashlib.sha256(token.encode()).digest(),
            msg=init_data.encode(),
            digestmod=hashlib.sha256
        )
        return secret.hexdigest()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# API Endpoints
@app.get("/projects/", response_model=List[Project])
async def get_projects(type: str = None, theme: str = None):
    conn = sqlite3.connect('aggregator.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM projects"
    params = []
    
    if type:
        type_mapping = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
        query += " WHERE type = ?"
        params.append(type_mapping.get(type, type))
        if theme:
            query += " AND theme = ?"
            params.append(theme)
    elif theme:
        query += " WHERE theme = ?"
        params.append(theme)
    
    query += " ORDER BY is_premium DESC, likes DESC"
    cursor.execute(query, params)
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return projects

@app.post("/projects/", response_model=Project)
async def create_project(project: Project, request: Request):
    if not request.headers.get('X-Telegram-Init-Data'):
        raise HTTPException(status_code=401, detail="Auth required")
    
    project.icon = project.icon or get_telegram_avatar(project.link)
    
    conn = sqlite3.connect('aggregator.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO projects (type, name, link, theme, is_premium, icon)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (project.type, project.name, project.link, project.theme, project.is_premium, project.icon))
    
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {**project.dict(), "id": project_id}

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    conn = sqlite3.connect('aggregator.db')
    conn.row_factory = sqlite3.Row
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE user_id = ?", (user_id,))
        projects_count = cursor.fetchone()[0]
        
        return {
            "id": user["id"],
            "username": user["username"],
            "stars": user["stars"],
            "balance": user["balance"],
            "projects_count": projects_count
        }
    finally:
        conn.close()

@app.post("/users/{user_id}/complete_task")
async def complete_task(user_id: int, task_type: str, request: Request):
    if not request.headers.get('X-Telegram-Init-Data'):
        raise HTTPException(status_code=401, detail="Auth required")
    
    rewards = {'banner': 5, 'subscribe': 3, 'invite': 10}
    if task_type not in rewards:
        raise HTTPException(status_code=400, detail="Invalid task type")
    
    conn = sqlite3.connect('aggregator.db')
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO tasks (user_id, task_type, completed)
            VALUES (?, ?, 1)
        ''', (user_id, task_type))
        
        cursor.execute('''
            UPDATE users SET stars = stars + ? WHERE id = ?
        ''', (rewards[task_type], user_id))
        
        conn.commit()
        return {"status": "success", "stars_added": rewards[task_type]}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Отладочные endpoints
@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Backend is running"}

@app.get("/debug/db")
async def debug_db():
    conn = sqlite3.connect('aggregator.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cursor.fetchone()[0]
    
    conn.close()
    return {"tables": tables, "counts": counts}

@app.get("/debug/projects")
async def debug_projects():
    conn = sqlite3.connect('aggregator.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return projects

@app.on_event("startup")
async def startup_db():
    init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
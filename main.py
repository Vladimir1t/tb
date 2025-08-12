from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List
import uvicorn
from fastapi import Request
import hmac
import hashlib
from typing import Optional  

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://telegram-bot-chi-lyart.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class Project(BaseModel):
    id: int = None
    type: str  # 'channel', 'bot' или 'mini_app'
    name: str
    link: str
    theme: str
    is_premium: bool = False
    likes: int = 0
    subscribers: int = 0

class User(BaseModel):
    id: int
    username: Optional[str] = None  # Явно указываем, что может быть None
    stars: int = 0
    balance: float = 0
    projects_count: int = 0  # Добавляем отсутствующее поле

    class Config:
        json_encoders = {
            type(None): lambda _: None  # Корректная сериализация None
        }

# Инициализация БД
def init_db():
    conn = sqlite3.connect('aggregator.db')
    cursor = conn.cursor()
    
    # Create tables if they don't exist
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
        user_id INTEGER DEFAULT 1
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        stars INTEGER DEFAULT 0,
        balance REAL DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        user_id INTEGER,
        task_type TEXT,
        completed BOOLEAN DEFAULT 0,
        PRIMARY KEY (user_id, task_type),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Add test data only if tables are empty
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        test_projects = [
            ('channel', 'IT Новости', 'https://t.me/it_news', 'technology', 1, 100, 25000, 1),
            ('channel', 'Маркетинг', 'https://t.me/marketing', 'business', 0, 50, 15000, 1),
            ('bot', 'Погодный Бот', 'https://t.me/weather_bot', 'utility', 0, 30, 5000, 1),
            ('bot', 'Финансовый помощник', 'https://t.me/finance_bot', 'finance', 1, 80, 18000, 1),
            ('mini_app', 'Головоломки', 'https://t.me/puzzle_app', 'games', 0, 20, 8000, 1)
        ]
        cursor.executemany('''
            INSERT INTO projects 
            (type, name, link, theme, is_premium, likes, subscribers, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_projects)
    
    conn.commit()
    conn.close()

init_db()

# Валидация данных Telegram
def validate_telegram_data(token: str, init_data: str):
    try:
        secret_key = hmac.new(
            key=hashlib.sha256(token.encode()).digest(),
            msg=init_data.encode(),
            digestmod=hashlib.sha256
        )
        return secret_key.hexdigest()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# API endpoints
@app.get("/projects/", response_model=List[Project])
async def get_projects(type: str = None, theme: str = None):
    conn = sqlite3.connect('aggregator.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM projects"
    params = []
    
    if type:
        query += " WHERE type = ?"
        params.append(type)
        if theme:
            query += " AND theme = ?"
            params.append(theme)
    elif theme:
        query += " WHERE theme = ?"
        params.append(theme)
    
    query += " ORDER BY is_premium DESC, likes DESC"
    
    cursor.execute(query, params)
    projects = cursor.fetchall()
    conn.close()
    
    return [dict(project) for project in projects]

@app.post("/projects/", response_model=Project)
async def create_project(project: Project, request: Request):
    init_data = request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        raise HTTPException(status_code=401, detail="Telegram auth required")
    
    # В реальном приложении нужно проверить init_data
    # validate_telegram_data("YOUR_BOT_TOKEN", init_data)
    
    conn = sqlite3.connect('aggregator.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO projects (type, name, link, theme, is_premium)
    VALUES (?, ?, ?, ?, ?)
    ''', (project.type, project.name, project.link, project.theme, project.is_premium))
    
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {**project.dict(), "id": project_id}

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    conn = sqlite3.connect('aggregator.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
    
    # Получаем количество проектов пользователя
    cursor.execute("SELECT COUNT(*) FROM projects WHERE user_id = ?", (user_id,))
    projects_count = cursor.fetchone()[0]
    
    conn.close()
    
    user_dict = dict(user)
    user_dict['projects_count'] = projects_count
    return user_dict

@app.post("/users/{user_id}/complete_task")
async def complete_task(user_id: int, task_type: str, request: Request):
    init_data = request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        raise HTTPException(status_code=401, detail="Telegram auth required")
    
    rewards = {
        'banner': 5,
        'subscribe': 3,
        'invite': 10
    }
    
    if task_type not in rewards:
        raise HTTPException(status_code=400, detail="Invalid task type")
    
    conn = sqlite3.connect('aggregator.db')
    cursor = conn.cursor()
    
    try:
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

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Backend is running"}

# Remove the duplicate get_user endpoint and keep this one:
@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    conn = sqlite3.connect('aggregator.db')
    conn.row_factory = sqlite3.Row
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
    
    conn.close()
    
    user_dict = dict(user)
    user_dict['projects_count'] = projects_count
    return user_dict

@app.get("/debug/db")
async def debug_db():
    conn = sqlite3.connect('aggregator.db')
    cursor = conn.cursor()
    
    # Check tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    # Count rows in each table
    counts = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        counts[table_name] = cursor.fetchone()[0]
    
    conn.close()
    return {"tables": tables, "counts": counts}

@app.get("/debug/projects")
async def debug_projects():
    conn = sqlite3.connect('aggregator.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    
    conn.close()
    return [dict(project) for project in projects]

@app.on_event("startup")
async def startup_db():
    init_db()  # Ваша существующая функция инициализации

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
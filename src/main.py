from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://telegram-bot-chi-lyart.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Модели Pydantic
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
    username: str = None
    stars: int = 0
    balance: float = 0

# Инициализация БД
def init_db():
    conn = sqlite3.connect('aggregator.db')
    cursor = conn.cursor()
    
    # Таблица проектов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT CHECK(type IN ('channel', 'bot', 'mini_app')),
        name TEXT,
        link TEXT,
        theme TEXT,
        is_premium BOOLEAN DEFAULT 0,
        likes INTEGER DEFAULT 0,
        subscribers INTEGER DEFAULT 0,
        user_id INTEGER
    )
    ''')
    
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        stars INTEGER DEFAULT 0,
        balance REAL DEFAULT 0
    )
    ''')
    
    # Таблица заданий
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        user_id INTEGER,
        task_type TEXT,
        completed BOOLEAN DEFAULT 0,
        PRIMARY KEY (user_id, task_type)
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# API endpoints
@app.get("/projects/", response_model=List[Project])
def get_projects(type: str = None, theme: str = None):
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
    
    cursor.execute(query, params)
    projects = cursor.fetchall()
    conn.close()
    
    return [dict(project) for project in projects]

@app.post("/projects/", response_model=Project)
def create_project(project: Project, user_id: int):
    conn = sqlite3.connect('aggregator.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO projects (type, name, link, theme, is_premium, user_id)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (project.type, project.name, project.link, project.theme, project.is_premium, user_id))
    
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {**project.dict(), "id": project_id}

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    conn = sqlite3.connect('aggregator.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        # Создаем нового пользователя при первом обращении
        cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
    
    conn.close()
    return dict(user)

@app.post("/users/{user_id}/complete_task")
def complete_task(user_id: int, task_type: str):
    conn = sqlite3.connect('aggregator.db')
    cursor = conn.cursor()
    
    # Определяем награду за задание
    rewards = {
        'banner': 5,
        'subscribe': 3,
        'invite': 10
    }
    
    if task_type not in rewards:
        raise HTTPException(status_code=400, detail="Invalid task type")
    
    # Отмечаем задание как выполненное и начисляем звезды
    cursor.execute('''
    INSERT OR REPLACE INTO tasks (user_id, task_type, completed)
    VALUES (?, ?, 1)
    ''', (user_id, task_type))
    
    cursor.execute('''
    UPDATE users SET stars = stars + ? WHERE id = ?
    ''', (rewards[task_type], user_id))
    
    conn.commit()
    conn.close()
    
    return {"status": "success", "stars_added": rewards[task_type]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

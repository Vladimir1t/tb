from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import base64
from fastapi import Response
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
import threading

from database import init_db
from bot import run_bot 

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
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
    rows = cursor.fetchall()
    conn.close()
    
    projects = []
    for row in rows:
        project = dict(row)
        if project["icon"]: 
            project["icon"] = (
                f"data:image/png;base64,{base64.b64encode(project['icon']).decode()}"
            )
        else:
            project["icon"] = None
        projects.append(project)
    
    return projects

@app.post("/projects/", response_model=Project)
async def create_project(project: Project, request: Request):
    if not request.headers.get('X-Telegram-Init-Data'):
        raise HTTPException(status_code=401, detail="Auth required")
    
    # project.icon = project.icon or get_telegram_avatar(project.link)
    
    conn = sqlite3.connect('aggregator.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO projects (type, name, link, theme, is_premium, icon)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (project.type, project.name, project.link, project.theme, project.is_premium,
    sqlite3.Binary(project.icon) if project.icon else None))

    
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    icon_str = None
    if icon_bytes:
        icon_str = f"data:image/png;base64,{base64.b64encode(icon_bytes).decode()}"
    return {**project.dict(), "id": project_id, "icon": icon_str}

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
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

if __name__ == "__main__":
    # mini app
    uvicorn.run(app, host="0.0.0.0", port=8000)
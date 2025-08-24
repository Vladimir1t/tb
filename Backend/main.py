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

# from database import init_db
from bot import run_bot 

# AI search
from fastapi import Query
# from sentence_transformers import SentenceTransformer
# import faiss

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


# model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# def load_embeddings():
#     conn = sqlite3.connect("aggregator.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT project_id, vector FROM project_embeddings;")
#     rows = cursor.fetchall()
#     conn.close()
#     ids = [r[0] for r in rows]
#     vectors = [np.frombuffer(r[1], dtype="float32") for r in rows]
#     return ids, np.vstack(vectors)

# ids, embeddings = load_embeddings()
# index = faiss.IndexFlatL2(embeddings.shape[1])
# index.add(embeddings)

# # API Endpoints
# @app.get("/projects/search/")
# async def search_projects(query: str, top_k: int = 10):
#     q_vec = model.encode([query]).astype("float32")
#     D, I = index.search(q_vec, k=top_k)

#     conn = sqlite3.connect("aggregator.db")
#     conn.row_factory = sqlite3.Row
#     cursor = conn.cursor()

#     results = []
#     for idx, dist in zip(I[0], D[0]):
#         pid = ids[idx]
#         cursor.execute("SELECT * FROM projects WHERE id=?", (pid,))
#         row = cursor.fetchone()
#         if row:
#             project = dict(row)
#             if project["icon"]:
#                 project["icon"] = f"data:image/png;base64,{base64.b64encode(project['icon']).decode()}"
#             else:
#                 project["icon"] = None
#             project["similarity"] = float(dist)
#             results.append(project)

#     conn.close()
#     return results

@app.get("/projects/", response_model=List[Project])
async def get_projects(
    type: Optional[str] = None,
    theme: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    conn = sqlite3.connect('aggregator.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM projects WHERE 1=1"
    params = []

    if type:
        type_mapping = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
        query += " AND type = ?"
        params.append(type_mapping.get(type, type))

    if theme:
        query += " AND theme = ?"
        params.append(theme)

    if search:
        # безопасно ищем по name и description даже если description NULL
        query += " AND (name LIKE ? OR IFNULL(description,'') LIKE ?)"
        like_pattern = f"%{search}%"
        params.extend([like_pattern, like_pattern])

    query += " ORDER BY is_premium DESC, likes DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    except Exception as e:
        conn.close()
        raise Exception(f"Ошибка SQL-запроса: {e}")

    conn.close()

    projects = []
    for row in rows:
        project = dict(row)
        if project.get("icon"): 
            project["icon"] = f"data:image/png;base64,{base64.b64encode(project['icon']).decode()}"
        else:
            project["icon"] = None
        projects.append(project)

    return projects

@app.post("/projects/", response_model=Project)
async def create_project(project: Project, request: Request):
    if not request.headers.get('X-Telegram-Init-Data'):
        raise HTTPException(status_code=401, detail="Auth required")
   
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
async def startup_bot():
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

if __name__ == "__main__":
    # mini app
    uvicorn.run(app, host="0.0.0.0", port=8000)
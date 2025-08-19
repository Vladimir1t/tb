<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Projects</title>
</head>
<body>
  <h1>Проекты</h1>
  <div id="projects"></div>

  <script>
    async function loadProjects() {
      const response = await fetch("http://127.0.0.1:8000/projects/");
      const projects = await response.json();

      const container = document.getElementById("projects");
      container.innerHTML = "";

      projects.forEach(async (project) => {
        const projectEl = document.createElement("div");
        projectEl.style.border = "1px solid #ccc";
        projectEl.style.margin = "10px";
        projectEl.style.padding = "10px";

        // создаём элемент img
        let img = document.createElement("img");
        img.style.width = "64px";
        img.style.height = "64px";

        // пробуем загрузить иконку по эндпоинту
        try {
          let res = await fetch(`http://127.0.0.1:8000/projects/${project.id}/icon`);
          if (res.ok) {
            let blob = await res.blob();
            img.src = URL.createObjectURL(blob);
          } else {
            img.src = "default.png"; // fallback
          }
        } catch (e) {
          img.src = "default.png"; // если ошибка сети
        }

        let title = document.createElement("h3");
        title.innerText = project.name;

        let link = document.createElement("a");
        link.href = project.link;
        link.innerText = "Перейти";

        projectEl.appendChild(img);
        projectEl.appendChild(title);
        projectEl.appendChild(link);

        container.appendChild(projectEl);
      });
    }

    loadProjects();
  </script>
</body>
</html>



# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import base64
# from fastapi import Response
# from pydantic import BaseModel
# import sqlite3
# from typing import List, Optional
# import uvicorn
# from fastapi import Request
# import hmac
# import hashlib
# import requests
# from urllib.parse import urlparse
# import logging
# from database import init_db

# # Настройка логирования
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI()

# # Настройка CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Модели данных
# class Project(BaseModel):
#     id: int = None
#     icon: Optional[bytes] = None
#     type: str
#     name: str
#     link: str
#     theme: str
#     is_premium: bool = False
#     likes: int = 0
#     subscribers: int = 0

# class User(BaseModel):
#     id: int
#     username: Optional[str] = None
#     stars: int = 0
#     balance: float = 0
#     projects_count: int = 0

#     class Config:
#         json_encoders = {type(None): lambda _: None}

# # Bнициализация базы данных в database.py
# init_db()

# # Валидация Telegram WebApp
# def validate_telegram_data(token: str, init_data: str):
#     try:
#         secret = hmac.new(
#             key=hashlib.sha256(token.encode()).digest(),
#             msg=init_data.encode(),
#             digestmod=hashlib.sha256
#         )
#         return secret.hexdigest()
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# # API Endpoints
# @app.get("/projects/", response_model=List[Project])
# async def get_projects(type: str = None, theme: str = None):
#     conn = sqlite3.connect('aggregator.db')
#     conn.row_factory = sqlite3.Row
#     cursor = conn.cursor()

#     query = "SELECT * FROM projects"
#     params = []

#     if type:
#         type_mapping = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
#         query += " WHERE type = ?"
#         params.append(type_mapping.get(type, type))
#         if theme:
#             query += " AND theme = ?"
#             params.append(theme)
#     elif theme:
#         query += " WHERE theme = ?"
#         params.append(theme)

#     query += " ORDER BY is_premium DESC, likes DESC"
#     cursor.execute(query, params)
#     projects = [dict(row) for row in cursor.fetchall()]
#     conn.close()

#     # 👇 конвертация icon → base64
#     for p in projects:
#         if p["icon"]:
#             p["icon"] = f"data:image/png;base64,{base64.b64encode(p['icon']).decode('utf-8')}"

#     return projects

# @app.get("/projects/{project_id}/icon")
# async def get_project_icon(project_id: int):
#     conn = sqlite3.connect("aggregator.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT icon FROM projects WHERE id = ?", (project_id,))
#     row = cursor.fetchone()
#     conn.close()
#     if row and row[0]:
#         return Response(content=row[0], media_type="image/png")
#     return Response(status_code=404)

# @app.post("/projects/", response_model=Project)
# async def create_project(project: Project, request: Request):
#     if not request.headers.get('X-Telegram-Init-Data'):
#         raise HTTPException(status_code=401, detail="Auth required")
    
#     project.icon = project.icon or get_telegram_avatar(project.link)
    
#     conn = sqlite3.connect('aggregator.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT INTO projects (type, name, link, theme, is_premium, icon)
#         VALUES (?, ?, ?, ?, ?, ?)
#     ''', (project.type, project.name, project.link, project.theme, project.is_premium,
#     sqlite3.Binary(project.icon) if project.icon else None))

    
#     project_id = cursor.lastrowid
#     conn.commit()
#     conn.close()
    
#     return {**project.dict(), "id": project_id}

# @app.get("/users/{user_id}", response_model=User)
# async def get_user(user_id: int):
#     conn = sqlite3.connect('aggregator.db')
#     conn.row_factory = sqlite3.Row
    
#     try:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
#         user = cursor.fetchone()
        
#         if not user:
#             cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
#             conn.commit()
#             cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
#             user = cursor.fetchone()
        
#         cursor.execute("SELECT COUNT(*) FROM projects WHERE user_id = ?", (user_id,))
#         projects_count = cursor.fetchone()[0]
        
#         return {
#             "id": user["id"],
#             "username": user["username"],
#             "stars": user["stars"],
#             "balance": user["balance"],
#             "projects_count": projects_count
#         }
#     finally:
#         conn.close()

# @app.post("/users/{user_id}/complete_task")
# async def complete_task(user_id: int, task_type: str, request: Request):
#     if not request.headers.get('X-Telegram-Init-Data'):
#         raise HTTPException(status_code=401, detail="Auth required")
    
#     rewards = {'banner': 5, 'subscribe': 3, 'invite': 10}
#     if task_type not in rewards:
#         raise HTTPException(status_code=400, detail="Invalid task type")
    
#     conn = sqlite3.connect('aggregator.db')
#     try:
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT OR REPLACE INTO tasks (user_id, task_type, completed)
#             VALUES (?, ?, 1)
#         ''', (user_id, task_type))
        
#         cursor.execute('''
#             UPDATE users SET stars = stars + ? WHERE id = ?
#         ''', (rewards[task_type], user_id))
        
#         conn.commit()
#         return {"status": "success", "stars_added": rewards[task_type]}
#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         conn.close()

# # Отладочные endpoints
# @app.get("/ping")
# async def ping():
#     return {"status": "ok", "message": "Backend is running"}

# @app.get("/debug/db")
# async def debug_db():
#     conn = sqlite3.connect('aggregator.db')
#     cursor = conn.cursor()
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
#     tables = [row[0] for row in cursor.fetchall()]
    
#     counts = {}
#     for table in tables:
#         cursor.execute(f"SELECT COUNT(*) FROM {table}")
#         counts[table] = cursor.fetchone()[0]
    
#     conn.close()
#     return {"tables": tables, "counts": counts}

# @app.get("/debug/projects")
# async def debug_projects():
#     conn = sqlite3.connect('aggregator.db')
#     conn.row_factory = sqlite3.Row
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM projects")
#     projects = [dict(row) for row in cursor.fetchall()]
#     conn.close()
#     return projects

# @app.on_event("startup")
# async def startup_db():
#     init_db()

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
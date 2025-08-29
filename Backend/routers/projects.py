# routers/projects.py
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Optional
import sqlite3
import base64
from models import Project
from database_connect import get_db_connection
from auth import verify_telegram_auth

router = APIRouter()

@router.get("/projects/", response_model=List[Project])
async def get_projects(
    type: Optional[str] = None,
    theme: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM projects WHERE 1=1"
        params = []

        if type:
            type_mapping = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
            query += " AND LOWER(type) = ?"
            params.append(type_mapping.get(type.lower(), type.lower()))
        if theme:
            query += " AND (LOWER(name) LIKE ? OR LOWER(theme) LIKE ?)"
            like_pattern = f"%{theme.lower()}%"
            params.extend([like_pattern, like_pattern])
        if search:
            query += " AND (LOWER(name) LIKE ? OR LOWER(theme) LIKE ?)"
            like_pattern = f"%{search.lower()}%"
            params.extend([like_pattern, like_pattern])

        query += " ORDER BY is_premium DESC, likes DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        projects = []
        for row in rows:
            project_data = dict(row)
            if project_data.get("icon"):
                project_data["icon"] = f"data:image/png;base64,{base64.b64encode(project_data['icon']).decode()}"
            else:
                project_data["icon"] = None
            projects.append(project_data)
        return projects
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Ошибка SQL-запроса: {e}")
    finally:
        if conn:
            conn.close()

@router.post("/projects/", response_model=Project)
async def create_project(project: Project, request: Request, _=Depends(verify_telegram_auth)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    icon_bytes = None
    if project.icon:
        # Предполагаем, что иконка приходит в формате base64
        try:
            # Отделяем метаданные от самих данных base64
            header, encoded = project.icon.split(",", 1)
            icon_bytes = base64.b64decode(encoded)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid icon format")

    try:
        cursor.execute('''
            INSERT INTO projects (type, name, link, theme, is_premium, icon)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (project.type, project.name, project.link, project.theme, project.is_premium, icon_bytes))
        
        project_id = cursor.lastrowid
        conn.commit()
        
        return {**project.dict(), "id": project_id}
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()
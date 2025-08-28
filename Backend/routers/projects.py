# routers/projects.py
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Optional, Dict, Any
import sqlite3
import base64
from models import Project
from database_connect import get_db_connection
from auth import verify_telegram_auth

router = APIRouter()

@router.get("/projects/", response_model=Dict[str, Any])
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
        
        # Базовый запрос для данных с DISTINCT
        query = """
            SELECT DISTINCT 
                id, name, type, theme, description, 
                link, is_premium, likes, icon, created_at
            FROM projects 
            WHERE 1=1
        """
        params = []
        count_params = []

        if type:
            type_mapping = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
            query += " AND LOWER(type) = ?"
            type_value = type_mapping.get(type.lower(), type.lower())
            params.append(type_value)
            count_params.append(type_value)
        
        if theme:
            query += " AND LOWER(theme) = ?"
            theme_value = theme.lower()
            params.append(theme_value)
            count_params.append(theme_value)
        
        if search:
            query += " AND (LOWER(name) LIKE ? OR LOWER(theme) LIKE ?)"
            like_pattern = f"%{search.lower()}%"
            params.extend([like_pattern, like_pattern])
            count_params.extend([like_pattern, like_pattern])

        # Запрос для подсчета общего количества уникальных записей
        count_query = "SELECT COUNT(DISTINCT id) FROM projects WHERE 1=1"
        if type:
            count_query += " AND LOWER(type) = ?"
        if theme:
            count_query += " AND LOWER(theme) = ?"
        if search:
            count_query += " AND (LOWER(name) LIKE ? OR LOWER(theme) LIKE ?)"

        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]

        # Добавляем сортировку и пагинацию к основному запросу
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

        # Возвращаем данные с информацией о пагинации
        return {
            "projects": projects,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
        }
        
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
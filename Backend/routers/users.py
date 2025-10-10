# routers/users.py
from fastapi import APIRouter, HTTPException, Request, Depends
from models import User, UserPreferences
from database_connect import get_db_connection
from auth import verify_telegram_auth
import json

router = APIRouter()

@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    conn = get_db_connection()
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
            "projects_count": projects_count,
            "preferences": user.get("preferences"),
            "survey_completed": bool(user.get("survey_completed", 0))
        }
    finally:
        conn.close()

@router.post("/users/{user_id}/complete_task")
async def complete_task(user_id: int, task_type: str, _=Depends(verify_telegram_auth)):
    rewards = {'banner': 5, 'subscribe': 3, 'invite': 10}
    if task_type not in rewards:
        raise HTTPException(status_code=400, detail="Invalid task type")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO tasks (user_id, task_type, completed)
            VALUES (?, ?, 1)
        ''', (user_id, task_type))
        
        cursor.execute('UPDATE users SET stars = stars + ? WHERE id = ?', (rewards[task_type], user_id))
        conn.commit()
        return {"status": "success", "stars_added": rewards[task_type]}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/users/{user_id}/survey")
async def save_survey(user_id: int, preferences: UserPreferences):
    """Сохранение результатов опроса пользователя"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Проверяем существует ли пользователь
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            # Создаем пользователя если его нет
            cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        
        # Сохраняем предпочтения в JSON формате
        preferences_json = json.dumps({
            "main_topics": preferences.main_topics,
            "sub_topics": preferences.sub_topics
        }, ensure_ascii=False)
        
        cursor.execute('''
            UPDATE users 
            SET preferences = ?, survey_completed = 1 
            WHERE id = ?
        ''', (preferences_json, user_id))
        
        conn.commit()
        return {"status": "success", "message": "Предпочтения сохранены"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/users/{user_id}/survey_status")
async def get_survey_status(user_id: int):
    """Проверка статуса прохождения опроса"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT survey_completed, preferences FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return {"survey_completed": False, "preferences": None}
        
        return {
            "survey_completed": bool(user["survey_completed"]) if user["survey_completed"] is not None else False,
            "preferences": user["preferences"]
        }
    finally:
        conn.close()
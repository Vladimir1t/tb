# routers/users.py
from fastapi import APIRouter, HTTPException, Request, Depends
from models import User
from database_connect import get_db_connection
from auth import verify_telegram_auth

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
            "projects_count": projects_count
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
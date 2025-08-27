# routers/debug.py
from fastapi import APIRouter
from database_connect import get_db_connection

router = APIRouter()

@router.get("/ping")
async def ping():
    return {"status": "ok", "message": "Backend is running"}

@router.get("/debug/db")
async def debug_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cursor.fetchone()[0]
    
    conn.close()
    return {"tables": tables, "counts": counts}

@router.get("/debug/projects")
async def debug_projects():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return projects
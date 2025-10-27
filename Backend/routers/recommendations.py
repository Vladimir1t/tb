# routers/recommendations.py
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import base64

from database_connect import get_db_connection
from auth import verify_telegram_auth
import recommendation_engine

router = APIRouter()

class Event(BaseModel):
    user_id: int
    project_id: int
    event_type: str  # 'impression', 'click', 'like', 'dislike', 'not_interested'
    ts: Optional[str] = None

class EventBatch(BaseModel):
    events: List[Event]

class SearchLog(BaseModel):
    user_id: int
    query: str

@router.post("/events")
async def log_events(batch: EventBatch):
    """
    Логирует события пользователей (клики, показы, лайки и т.д.)
    Принимает батч событий для эффективности
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        user_ids_to_invalidate = set()
        
        for event in batch.events:
            # Валидация типа события
            valid_types = ['impression', 'click', 'like', 'dislike', 'not_interested']
            if event.event_type not in valid_types:
                continue
            
            # Используем переданный timestamp или текущее время
            ts = event.ts if event.ts else datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO interactions (user_id, project_id, event_type, ts)
                VALUES (?, ?, ?, ?)
            ''', (event.user_id, event.project_id, event.event_type, ts))
            
            # Помечаем пользователя для инвалидации кэша
            if event.event_type in ['click', 'like', 'dislike', 'not_interested']:
                user_ids_to_invalidate.add(event.user_id)
        
        conn.commit()
        
        # Инвалидируем кэш профилей пользователей
        for user_id in user_ids_to_invalidate:
            recommendation_engine.invalidate_user_cache(user_id)
        
        return {
            "status": "success", 
            "logged_events": len(batch.events),
            "invalidated_users": len(user_ids_to_invalidate)
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка логирования событий: {e}")
    finally:
        if conn:
            conn.close()

@router.post("/search_log")
async def log_search(search_log: SearchLog):
    """
    Логирует поисковые запросы пользователей
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_logs (user_id, query, ts)
            VALUES (?, ?, ?)
        ''', (search_log.user_id, search_log.query, datetime.now().isoformat()))
        
        conn.commit()
        
        return {"status": "success"}
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка логирования поиска: {e}")
    finally:
        if conn:
            conn.close()

@router.get("/users/{user_id}/recommendations")
async def get_user_recommendations(
    user_id: int,
    type: Optional[str] = Query(None, description="Фильтр по типу: channel, bot, mini_app или all"),
    limit: int = Query(100, ge=1, le=200, description="Количество рекомендаций")
):
    """
    Получает персональные рекомендации для пользователя
    
    Работает в 3 этапа:
    1. Сбор сигналов (профиль пользователя из опроса + поведение)
    2. Генерация ~1000 кандидатов
    3. Легкий реранкинг и диверсификация, топ-N
    """
    conn = None
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        
        # Проверяем существование пользователя
        cursor = conn.cursor()
        cursor.execute("SELECT id, preferences, survey_completed FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            # Создаем пользователя если его нет
            cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
            conn.commit()
        
        # Строим индекс если нужно
        if not recommendation_engine._inverted_index_built:
            recommendation_engine.build_inverted_index()
        
        # Получаем рекомендации
        recommendations = recommendation_engine.get_recommendations(
            user_id=user_id,
            conn=conn,
            content_type=type,
            limit=limit
        )
        
        # Форматируем результат (добавляем base64 иконки)
        formatted_results = []
        for project in recommendations:
            if project.get("icon"):
                project["icon"] = f"data:image/png;base64,{base64.b64encode(project['icon']).decode()}"
            else:
                project["icon"] = None
            formatted_results.append(project)
        
        # Логируем показы (impression) асинхронно
        project_ids = [p['id'] for p in formatted_results]
        if project_ids:
            try:
                for project_id in project_ids:
                    cursor.execute('''
                        INSERT INTO interactions (user_id, project_id, event_type, ts)
                        VALUES (?, ?, 'impression', ?)
                    ''', (user_id, project_id, datetime.now().isoformat()))
                conn.commit()
            except:
                pass  # Не критично если не залогировали
        
        return {
            "user_id": user_id,
            "total": len(formatted_results),
            "recommendations": formatted_results
        }
        
    except Exception as e:
        print(f"❌ Ошибка получения рекомендаций: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка получения рекомендаций: {e}")
    finally:
        if conn:
            conn.close()

@router.get("/projects/{project_id}/similar")
async def get_similar_projects(
    project_id: int,
    limit: int = Query(20, ge=1, le=50, description="Количество похожих проектов")
):
    """
    Получает проекты, похожие на указанный (по контенту)
    """
    conn = None
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        
        # Проверяем существование проекта
        if project_id not in recommendation_engine.search_index:
            raise HTTPException(status_code=404, detail="Проект не найден")
        
        # Строим индекс если нужно
        if not recommendation_engine._inverted_index_built:
            recommendation_engine.build_inverted_index()
        
        # Получаем токены исходного проекта
        source_tokens = recommendation_engine.search_index[project_id].get('all_tokens', set())
        source_tf = recommendation_engine.search_index[project_id].get('tf', {})
        
        # Находим похожие проекты
        similar_scores = []
        
        for candidate_id in recommendation_engine._inverted_index.get(list(source_tokens)[0], set()):
            if candidate_id == project_id:
                continue
            
            if candidate_id in recommendation_engine.search_index:
                candidate_tf = recommendation_engine.search_index[candidate_id].get('tf', {})
                
                # Косинусное сходство
                similarity = recommendation_engine.calculate_cosine_similarity(source_tf, candidate_tf)
                
                if similarity > 0.1:  # Минимальный порог
                    similar_scores.append((candidate_id, similarity))
        
        # Сортируем по сходству
        similar_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Берем топ-N
        top_similar = similar_scores[:limit]
        
        # Формируем результат
        results = []
        for candidate_id, similarity in top_similar:
            if candidate_id in recommendation_engine.project_data_cache:
                project = dict(recommendation_engine.project_data_cache[candidate_id])
                
                # Добавляем иконку
                cursor = conn.cursor()
                cursor.execute("SELECT icon FROM projects WHERE id = ?", (candidate_id,))
                row = cursor.fetchone()
                if row and row['icon']:
                    project["icon"] = f"data:image/png;base64,{base64.b64encode(row['icon']).decode()}"
                else:
                    project["icon"] = None
                
                project['similarity_score'] = similarity
                results.append(project)
        
        return {
            "source_project_id": project_id,
            "total": len(results),
            "similar_projects": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка получения похожих проектов: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка получения похожих проектов: {e}")
    finally:
        if conn:
            conn.close()

@router.get("/users/{user_id}/stats")
async def get_user_stats(user_id: int):
    """
    Получает статистику пользователя (для отладки)
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Статистика по событиям
        cursor.execute('''
            SELECT event_type, COUNT(*) as count
            FROM interactions
            WHERE user_id = ?
            GROUP BY event_type
        ''', (user_id,))
        
        event_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Последние действия
        cursor.execute('''
            SELECT event_type, project_id, ts
            FROM interactions
            WHERE user_id = ?
            ORDER BY ts DESC
            LIMIT 10
        ''', (user_id,))
        
        recent_actions = [
            {"event_type": row[0], "project_id": row[1], "ts": row[2]}
            for row in cursor.fetchall()
        ]
        
        # Предпочтения
        cursor.execute("SELECT preferences FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        preferences = None
        if row and row[0]:
            import json
            preferences = json.loads(row[0])
        
        return {
            "user_id": user_id,
            "event_stats": event_stats,
            "recent_actions": recent_actions,
            "preferences": preferences
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {e}")
    finally:
        if conn:
            conn.close()


@router.get("/debug/cache_stats")
async def get_cache_stats_endpoint():
    """
    Получить статистику кэша профилей пользователей для мониторинга
    """
    return recommendation_engine.get_cache_stats()


@router.post("/debug/clear_cache")
async def clear_cache_endpoint():
    """
    Очистить весь кэш профилей (для отладки)
    """
    return recommendation_engine.clear_all_cache()
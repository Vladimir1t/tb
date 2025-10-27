"""
Движок рекомендательной системы
Реализует 3-этапную архитектуру:
1. Сбор сигналов (профиль пользователя)
2. Генерация кандидатов (~1000)
3. Легкий реранкинг (топ-100)
"""
import sqlite3
import json
import math
import time
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter, defaultdict, OrderedDict
from datetime import datetime, timedelta
import threading

# Импорты из существующих модулей
from routers.projects import (
    search_index, 
    project_data_cache,
    normalize_and_stem,
    expand_query_with_synonyms,
    calculate_cosine_similarity,
    stem_word
)

# Глобальные кэши с LRU
_USER_PROFILE_CACHE_MAX_SIZE = 10000  # Максимум 10К пользователей в кэше
_user_profile_cache = OrderedDict()  # OrderedDict для LRU (Least Recently Used)
_user_profile_cache_lock = threading.Lock()
_USER_PROFILE_TTL = 86400  # 24 часа (было 5 минут)

_inverted_index = {}  # {token: set(project_ids)}
_inverted_index_lock = threading.Lock()
_inverted_index_built = False

# Веса для ранжирования (можно настраивать)
WEIGHTS = {
    'sim_content': 1.0,      # Косинусное сходство с профилем
    'theme_match': 2.0,      # Точные совпадения тем
    'popularity': 0.3,       # Популярность (subscribers/likes)
    'recency_boost': 0.5,    # Похожесть на недавние клики
    'seen_penalty': -2.0,    # Штраф за недавно показанное
}

# Настройки генерации кандидатов
CANDIDATE_LIMITS = {
    'from_preferences': 400,
    'similar_to_clicks': 300,
    'popular_in_themes': 200,
    'exploration': 100,
}

def build_inverted_index():
    """Строит инвертированный индекс token -> set(project_ids)"""
    global _inverted_index, _inverted_index_built
    
    with _inverted_index_lock:
        if _inverted_index_built:
            return
        
        print("🔨 Строим инвертированный индекс для рекомендаций...")
        _inverted_index = defaultdict(set)
        
        for project_id, project_data in search_index.items():
            tokens = project_data.get('all_tokens', set())
            for token in tokens:
                _inverted_index[token].add(project_id)
        
        # Конвертируем в обычный dict для экономии памяти
        _inverted_index = dict(_inverted_index)
        _inverted_index_built = True
        print(f"✅ Инвертированный индекс построен: {len(_inverted_index)} токенов")


def get_user_profile(user_id: int, conn: sqlite3.Connection) -> Dict:
    """
    Получает или строит профиль пользователя с LRU кэшем
    Профиль содержит:
    - preferences_tokens: токены из опроса (main_topics, sub_topics)
    - click_tokens: токены из последних кликов
    - tf_vector: усредненный TF-вектор
    - recent_project_ids: последние просмотренные проекты
    """
    # Проверяем кэш
    with _user_profile_cache_lock:
        if user_id in _user_profile_cache:
            profile, timestamp = _user_profile_cache[user_id]
            
            # Проверяем TTL
            if time.time() - timestamp < _USER_PROFILE_TTL:
                # Перемещаем в конец OrderedDict (обновляем "recency")
                _user_profile_cache.move_to_end(user_id)
                return profile
            else:
                # TTL истек - удаляем
                del _user_profile_cache[user_id]
    
    # Строим профиль
    profile = {
        'preferences_tokens': set(),
        'click_tokens': set(),
        'tf_vector': {},
        'recent_project_ids': [],
        'themes': set(),
    }
    
    cursor = conn.cursor()
    
    # 1. Получаем предпочтения из опроса
    cursor.execute("SELECT preferences FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row and row[0]:
        try:
            prefs = json.loads(row[0])
            main_topics = prefs.get('main_topics', [])
            sub_topics = prefs.get('sub_topics', [])
            
            # Расширяем синонимами и стеммингом
            all_topics = main_topics + sub_topics
            for topic in all_topics:
                # Добавляем сам топик
                profile['themes'].add(topic.lower())
                
                # Расширяем синонимами
                expanded = expand_query_with_synonyms(topic)
                profile['preferences_tokens'].update(expanded)
                
                # Добавляем стеммы
                words = topic.lower().split()
                for word in words:
                    stemmed = stem_word(word)
                    if stemmed:
                        profile['preferences_tokens'].add(stemmed)
        except:
            pass
    
    # 2. Получаем последние клики/лайки (последние 1000)
    cursor.execute('''
        SELECT DISTINCT project_id 
        FROM interactions 
        WHERE user_id = ? AND event_type IN ('click', 'like')
        ORDER BY ts DESC 
        LIMIT 1000
    ''', (user_id,))
    
    clicked_projects = [row[0] for row in cursor.fetchall()]
    profile['recent_project_ids'] = clicked_projects[:100]  # Храним последние 100 для быстрого доступа
    
    # Собираем токены из кликнутых проектов
    tf_vectors = []
    for project_id in clicked_projects:
        if project_id in search_index:
            project_tokens = search_index[project_id].get('all_tokens', set())
            profile['click_tokens'].update(project_tokens)
            
            # Собираем TF-векторы для усреднения
            tf_vectors.append(search_index[project_id].get('tf', {}))
            
            # Добавляем темы проектов
            if project_id in project_data_cache:
                theme = project_data_cache[project_id].get('theme', '')
                if theme:
                    profile['themes'].add(theme.lower())
    
    # 3. Усредняем TF-векторы
    if tf_vectors:
        all_terms = set()
        for tf in tf_vectors:
            all_terms.update(tf.keys())
        
        for term in all_terms:
            values = [tf.get(term, 0) for tf in tf_vectors]
            profile['tf_vector'][term] = sum(values) / len(tf_vectors)
    else:
        # Если нет кликов, используем только preferences
        for token in profile['preferences_tokens']:
            profile['tf_vector'][token] = 1.0 / max(len(profile['preferences_tokens']), 1)
    
    # Кэшируем профиль с LRU управлением
    with _user_profile_cache_lock:
        # Проверяем размер кэша
        if len(_user_profile_cache) >= _USER_PROFILE_CACHE_MAX_SIZE:
            # Удаляем самый старый (первый в OrderedDict)
            oldest_user_id = next(iter(_user_profile_cache))
            del _user_profile_cache[oldest_user_id]
        
        # Добавляем в конец (самый свежий)
        _user_profile_cache[user_id] = (profile, time.time())
    
    return profile


def generate_candidates(
    user_profile: Dict, 
    user_id: int,
    conn: sqlite3.Connection,
    content_type: Optional[str] = None
) -> List[int]:
    """
    Генерирует ~1000 кандидатов из разных источников
    """
    if not _inverted_index_built:
        build_inverted_index()
    
    candidates = set()
    cursor = conn.cursor()
    
    # Получаем недавно показанные проекты для исключения
    cursor.execute('''
        SELECT DISTINCT project_id 
        FROM interactions 
        WHERE user_id = ? AND event_type IN ('impression', 'click', 'not_interested')
        AND ts > datetime('now', '-7 days')
    ''', (user_id,))
    recently_seen = set(row[0] for row in cursor.fetchall())
    
    # 1. Кандидаты по предпочтениям (опрос + синонимы)
    pref_tokens = user_profile['preferences_tokens']
    pref_candidates = set()
    
    for token in pref_tokens:
        if token in _inverted_index:
            pref_candidates.update(_inverted_index[token])
            if len(pref_candidates) >= CANDIDATE_LIMITS['from_preferences']:
                break
    
    # Фильтруем по типу
    if content_type and content_type != 'all':
        type_map = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
        target_type = type_map.get(content_type, content_type)
        pref_candidates = {
            pid for pid in pref_candidates 
            if project_data_cache.get(pid, {}).get('type') == target_type
        }
    
    candidates.update(list(pref_candidates)[:CANDIDATE_LIMITS['from_preferences']])
    
    # 2. Похожие на недавние клики
    recent_clicks = user_profile['recent_project_ids'][:5]
    similar_candidates = set()
    
    for clicked_id in recent_clicks:
        if clicked_id in search_index:
            clicked_tokens = search_index[clicked_id].get('all_tokens', set())
            
            # Находим проекты с пересечением токенов
            for token in list(clicked_tokens)[:50]:  # Ограничиваем для скорости
                if token in _inverted_index:
                    similar_candidates.update(_inverted_index[token])
                    if len(similar_candidates) >= CANDIDATE_LIMITS['similar_to_clicks']:
                        break
    
    # Фильтруем по типу
    if content_type and content_type != 'all':
        similar_candidates = {
            pid for pid in similar_candidates 
            if project_data_cache.get(pid, {}).get('type') == target_type
        }
    
    candidates.update(list(similar_candidates)[:CANDIDATE_LIMITS['similar_to_clicks']])
    
    # 3. Популярные в темах пользователя
    user_themes = user_profile['themes']
    popular_candidates = []
    
    if user_themes:
        # Ищем проекты с совпадающими темами, сортируем по популярности
        for project_id, project_info in project_data_cache.items():
            project_theme = project_info.get('theme', '').lower()
            
            # Проверяем совпадение тем
            theme_match = any(theme in project_theme for theme in user_themes)
            if theme_match:
                # Фильтруем по типу
                if content_type and content_type != 'all':
                    if project_info.get('type') != target_type:
                        continue
                
                subscribers = project_info.get('subscribers', 0)
                likes = project_info.get('likes', 0)
                popularity = subscribers + likes * 10
                popular_candidates.append((project_id, popularity))
        
        # Сортируем по популярности
        popular_candidates.sort(key=lambda x: x[1], reverse=True)
        candidates.update([pid for pid, _ in popular_candidates[:CANDIDATE_LIMITS['popular_in_themes']]])
    
    # 4. Exploration: случайные из близких тем
    if len(candidates) < 800:
        all_project_ids = list(project_data_cache.keys())
        
        # Фильтруем по типу
        if content_type and content_type != 'all':
            all_project_ids = [
                pid for pid in all_project_ids 
                if project_data_cache.get(pid, {}).get('type') == target_type
            ]
        
        import random
        exploration_pool = [pid for pid in all_project_ids if pid not in candidates]
        exploration_sample = random.sample(
            exploration_pool, 
            min(CANDIDATE_LIMITS['exploration'], len(exploration_pool))
        )
        candidates.update(exploration_sample)
    
    # Убираем недавно показанные
    candidates = candidates - recently_seen
    
    # Убираем недавние клики (чтобы не показывать повторно)
    candidates = candidates - set(user_profile['recent_project_ids'])
    
    return list(candidates)


def rerank_candidates(
    candidates: List[int],
    user_profile: Dict,
    user_id: int,
    conn: sqlite3.Connection
) -> List[Tuple[int, float, str]]:
    """
    Легкий реранкинг кандидатов с весами
    Возвращает список (project_id, score, reason)
    """
    cursor = conn.cursor()
    
    # Получаем недавно показанные для штрафа
    cursor.execute('''
        SELECT project_id, MAX(ts) as last_seen
        FROM interactions 
        WHERE user_id = ? AND event_type = 'impression'
        AND ts > datetime('now', '-3 days')
        GROUP BY project_id
    ''', (user_id,))
    
    recently_shown = {}
    for row in cursor.fetchall():
        project_id, last_seen_str = row
        try:
            last_seen = datetime.fromisoformat(last_seen_str)
            hours_ago = (datetime.now() - last_seen).total_seconds() / 3600
            recently_shown[project_id] = hours_ago
        except:
            pass
    
    # Нормализация популярности (min-max)
    all_subscribers = [
        project_data_cache.get(pid, {}).get('subscribers', 0) 
        for pid in candidates
    ]
    max_subs = max(all_subscribers) if all_subscribers else 1
    min_subs = min(all_subscribers) if all_subscribers else 0
    subs_range = max_subs - min_subs if max_subs > min_subs else 1
    
    scored_candidates = []
    user_tf = user_profile['tf_vector']
    recent_click_ids = set(user_profile['recent_project_ids'][:5])
    user_themes = user_profile['themes']
    
    for project_id in candidates:
        if project_id not in search_index or project_id not in project_data_cache:
            continue
        
        project_index = search_index[project_id]
        project_info = project_data_cache[project_id]
        
        # 1. Косинусное сходство с профилем
        project_tf = project_index.get('tf', {})
        sim_content = calculate_cosine_similarity(user_tf, project_tf)
        
        # 2. Совпадение тем
        project_theme = project_info.get('theme', '').lower()
        project_name = project_info.get('name', '').lower()
        
        theme_match_score = 0
        matched_themes = []
        for theme in user_themes:
            if theme in project_theme:
                theme_match_score += 1.0
                matched_themes.append(theme)
            elif theme in project_name:
                theme_match_score += 0.5
                matched_themes.append(theme)
        
        # 3. Популярность (нормализованная)
        subscribers = project_info.get('subscribers', 0)
        likes = project_info.get('likes', 0)
        popularity_raw = subscribers + likes * 10
        popularity_norm = (subscribers - min_subs) / subs_range if subs_range > 0 else 0
        
        # 4. Recency boost (похожесть на недавние клики)
        recency_boost = 0
        if recent_click_ids:
            # Проверяем пересечение токенов с недавними кликами
            project_tokens = project_index.get('all_tokens', set())
            for clicked_id in recent_click_ids:
                if clicked_id in search_index:
                    clicked_tokens = search_index[clicked_id].get('all_tokens', set())
                    overlap = len(project_tokens & clicked_tokens)
                    if overlap > 5:
                        recency_boost += 0.5
        
        # 5. Штраф за недавно показанное (до 48 часов)
        seen_penalty = 0
        if project_id in recently_shown:
            hours_ago = recently_shown[project_id]
            if hours_ago < 48:  # Штраф действует до 48 часов
                seen_penalty = 1.0 - (hours_ago / 48)  # Чем свежее, тем больше штраф
        
        # Итоговый скор
        score = (
            WEIGHTS['sim_content'] * sim_content +
            WEIGHTS['theme_match'] * theme_match_score +
            WEIGHTS['popularity'] * popularity_norm +
            WEIGHTS['recency_boost'] * recency_boost +
            WEIGHTS['seen_penalty'] * seen_penalty
        )
        
        # Формируем причину рекомендации
        reason_parts = []
        if matched_themes:
            reason_parts.append(f"Темы: {', '.join(matched_themes[:2])}")
        if recency_boost > 0:
            reason_parts.append("Похоже на ваши клики")
        if popularity_raw > 10000:
            reason_parts.append("Популярное")
        
        reason = " • ".join(reason_parts) if reason_parts else "Рекомендуем"
        
        scored_candidates.append((project_id, score, reason))
    
    # Сортируем по скору
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    return scored_candidates


def diversify_results(
    scored_candidates: List[Tuple[int, float, str]],
    max_same_theme: int = 4
) -> List[Tuple[int, float, str]]:
    """
    Диверсификация результатов: не более N подряд одной темы
    (Проверка на типы удалена - каналы могут идти друг за другом)
    """
    diversified = []
    theme_counter = Counter()
    last_theme = None
    
    for project_id, score, reason in scored_candidates:
        if project_id not in project_data_cache:
            continue
        
        project_info = project_data_cache[project_id]
        project_theme = project_info.get('theme', '').lower()
        
        # Проверяем, не слишком ли много подряд одной темы
        if project_theme == last_theme:
            theme_counter[project_theme] += 1
            if theme_counter[project_theme] > max_same_theme:
                continue  # Пропускаем
        else:
            theme_counter.clear()
            theme_counter[project_theme] = 1
            last_theme = project_theme
        
        diversified.append((project_id, score, reason))
    
    return diversified


def get_recommendations(
    user_id: int,
    conn: sqlite3.Connection,
    content_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Главная функция: получает рекомендации для пользователя
    """
    # 1. Получаем профиль пользователя
    user_profile = get_user_profile(user_id, conn)
    
    # 2. Генерируем кандидатов
    candidates = generate_candidates(user_profile, user_id, conn, content_type)
    
    if not candidates:
        # Fallback: популярные проекты
        return get_fallback_recommendations(conn, content_type, limit)
    
    # 3. Реранкинг
    scored_candidates = rerank_candidates(candidates, user_profile, user_id, conn)
    
    # 4. Диверсификация
    diversified = diversify_results(scored_candidates)
    
    # 5. Берем топ-N
    top_candidates = diversified[:limit]
    
    # 6. Формируем результат
    results = []
    for project_id, score, reason in top_candidates:
        if project_id in project_data_cache:
            project = dict(project_data_cache[project_id])
            project['recommendation_score'] = score
            project['recommendation_reason'] = reason
            results.append(project)
    
    return results


def get_fallback_recommendations(
    conn: sqlite3.Connection,
    content_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Fallback рекомендации для холодного старта
    """
    cursor = conn.cursor()
    
    query = "SELECT * FROM projects WHERE 1=1"
    params = []
    
    if content_type and content_type != 'all':
        type_map = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
        target_type = type_map.get(content_type, content_type)
        query += " AND type = ?"
        params.append(target_type)
    
    query += " ORDER BY subscribers DESC, likes DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        project = dict(row)
        project['recommendation_score'] = 0.0
        project['recommendation_reason'] = "Популярное"
        results.append(project)
    
    return results


def invalidate_user_cache(user_id: int):
    """Инвалидирует кэш профиля пользователя"""
    with _user_profile_cache_lock:
        if user_id in _user_profile_cache:
            del _user_profile_cache[user_id]


def get_cache_stats() -> Dict:
    """
    Возвращает статистику кэша для мониторинга
    """
    with _user_profile_cache_lock:
        current_time = time.time()
        
        # Подсчет истекших записей
        expired_count = sum(
            1 for _, (_, timestamp) in _user_profile_cache.items()
            if current_time - timestamp > _USER_PROFILE_TTL
        )
        
        return {
            "total_cached_users": len(_user_profile_cache),
            "max_size": _USER_PROFILE_CACHE_MAX_SIZE,
            "usage_percent": round(len(_user_profile_cache) / _USER_PROFILE_CACHE_MAX_SIZE * 100, 2),
            "expired_entries": expired_count,
            "ttl_seconds": _USER_PROFILE_TTL,
            "ttl_hours": _USER_PROFILE_TTL / 3600
        }


def clear_all_cache():
    """
    Очищает весь кэш профилей (для отладки или принудительного обновления)
    """
    with _user_profile_cache_lock:
        cleared_count = len(_user_profile_cache)
        _user_profile_cache.clear()
        return {"cleared_profiles": cleared_count}
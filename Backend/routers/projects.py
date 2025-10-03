# routers/projects.py
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Optional, Dict, Set
import sqlite3
import base64
import re
import math
from collections import Counter
from models import Project
from database_connect import get_db_connection
from .synonyms import SYNONYM_DB
from auth import verify_telegram_auth

router = APIRouter()

# Кэш для поискового индекса
search_index = {}
project_data_cache = {}

def levenshtein_distance(s1: str, s2: str) -> int:
    """Вычисляет расстояние Левенштейна между двумя строками"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def find_similar_words_in_index(query_word: str, project_tokens: Set[str], max_distance: int = 2) -> List[str]:
    """Находит похожие слова в токенах проекта"""
    similar_words = []
    for token in project_tokens:
        distance = levenshtein_distance(query_word, token)
        if distance <= max_distance and distance > 0:  # Исключаем точные совпадения
            # Вычисляем степень похожести (1 - normalized_distance)
            max_len = max(len(query_word), len(token))
            similarity = 1 - (distance / max_len)
            similar_words.append((token, similarity))
    
    # Сортируем по убыванию похожести
    similar_words.sort(key=lambda x: x[1], reverse=True)
    return [word for word, score in similar_words[:3]]  # Возвращаем топ-3 похожих слов

def expand_with_synonyms(word: str) -> Set[str]:
    """Расширяет слово синонимами"""
    synonyms = set()
    word_lower = word.lower()
    
    # Добавляем само слово
    synonyms.add(word_lower)
    
    # Ищем синонимы в базе
    if word_lower in SYNONYM_DB:
        synonyms.update(SYNONYM_DB[word_lower])
    
    # Также проверяем возможные основы слов
    for key, synonym_list in SYNONYM_DB.items():
        if word_lower in synonym_list:
            synonyms.add(key)
            synonyms.update(synonym_list)
    
    return synonyms

def expand_query_with_synonyms(query: str) -> Set[str]:
    """Расширяет поисковый запрос синонимами"""
    words = re.findall(r'\b\w{2,}\b', query.lower())
    expanded_terms = set()
    
    for word in words:
        synonyms = expand_with_synonyms(word)
        expanded_terms.update(synonyms)
    
    # print(f"🔤 Query expansion: '{query}' → {expanded_terms}")
    return expanded_terms

# routers/projects.py

def build_search_index(conn):
    """Строим улучшенный поисковый индекс с поддержкой синонимов"""
    global search_index, project_data_cache
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, theme, type FROM projects")
    rows = cursor.fetchall()
    
    search_index = {}
    project_data_cache = {}
    
    # print(f"🔍 Building search index for {len(rows)} projects")
    
    # Собираем все уникальные токены для быстрого поиска похожих слов
    all_unique_tokens = set()
    
    for row in rows:
        project = dict(row)
        project_id = project['id']
        project_data_cache[project_id] = project
        
        # Создаем текстовый контент для индексации
        content = f"{project['name']} {project['theme']} {project['type']}".lower()
        
        # Токенизация
        words = re.findall(r'\b\w{2,}\b', content)
        
        # Добавляем синонимы в индекс
        enhanced_tokens = set()
        for word in words:
            enhanced_tokens.add(word)
            # Добавляем синонимы для каждого слова
            synonyms = expand_with_synonyms(word)
            enhanced_tokens.update(synonyms)
            
            # Добавляем n-grams для частичного поиска
            if len(word) > 3:
                for i in range(len(word) - 2):
                    enhanced_tokens.add(word[i:i+3])
        
        word_count = Counter(enhanced_tokens)
        total_words = len(enhanced_tokens)
        
        # Сохраняем TF (Term Frequency)
        search_index[project_id] = {
            'tf': {word: count/total_words for word, count in word_count.items()},
            'content': content,
            'original_words': words,
            'all_tokens': set(enhanced_tokens)  # Сохраняем все токены для поиска похожих слов
        }
        
        # Собираем все уникальные токены
        all_unique_tokens.update(enhanced_tokens)
    
    # Сохраняем глобальный список всех токенов для быстрого поиска
    global ALL_TOKENS
    ALL_TOKENS = list(all_unique_tokens)
    
    # print(f"📊 Search index built with {len(ALL_TOKENS)} unique tokens")

def find_similar_words_fast(query_word: str, max_distance: int = 2) -> List[str]:
    """Быстрый поиск похожих слов среди всех токенов индекса"""
    similar_words = []
    query_lower = query_word.lower()
    
    for token in ALL_TOKENS:
        # Быстрая проверка длины перед вычислением расстояния
        if abs(len(query_lower) - len(token)) > max_distance:
            continue
            
        distance = levenshtein_distance(query_lower, token)
        if distance <= max_distance and distance > 0:  # Исключаем точные совпадения
            max_len = max(len(query_lower), len(token))
            similarity = 1 - (distance / max_len)
            similar_words.append((token, similarity))
    
    # Сортируем по убыванию похожести и берем топ-3
    similar_words.sort(key=lambda x: x[1], reverse=True)
    return [word for word, score in similar_words[:3]]

def spell_aware_semantic_search(query, threshold=0.01, top_k=30):
    """Оптимизированный умный поиск с поддержкой синонимов и орфографических ошибок"""
    global search_index
    
    # print(f"🔍 Starting optimized spell-aware search for: '{query}'")
    # print(f"🔍 Threshold: {threshold}, Top K: {top_k}")
    
    if not search_index:
        # print("❌ Search index is empty!")
        return []
    
    # Расширяем запрос синонимами
    expanded_terms = expand_query_with_synonyms(query)
    
    if not expanded_terms:
        # print("❌ No valid terms after expansion")
        return []
    
    # print(f"🔍 Expanded terms: {len(expanded_terms)} terms")
    
    # Токены оригинального запроса
    original_query_words = re.findall(r'\b\w{2,}\b', query.lower())
    
    # Предварительно находим похожие слова для всех слов запроса
    similar_words_cache = {}
    for query_word in original_query_words:
        similar_words = find_similar_words_fast(query_word)
        if similar_words:
            similar_words_cache[query_word] = similar_words
            # print(f"   📝 Found similar words for '{query_word}': {similar_words}")
    
    # Создаем TF для расширенного запроса
    query_tf = {term: 1.0/len(expanded_terms) for term in expanded_terms}
    
    similarities = []
    
    for project_id, project_data in search_index.items():
        similarity = 0
        project_info = project_data_cache.get(project_id, {})
        project_name = project_info.get('name', '').lower()
        project_theme = project_info.get('theme', '').lower()
        project_tokens = project_data['all_tokens']
        
        # Способ 1: Быстрые совпадения с расширенными терминами
        for term in expanded_terms:
            if term in project_name:
                # Полное слово в названии - максимальный score
                if any(term == word for word in project_data['original_words']):
                    similarity += 2.0
                else:
                    similarity += 1.5
            
            if term in project_theme:
                if any(term == word for word in project_data['original_words']):
                    similarity += 1.5
                else:
                    similarity += 1.0
        
        # Способ 2: Быстрый поиск похожих слов (орфографические ошибки)
        for query_word, similar_words in similar_words_cache.items():
            # Проверяем, есть ли похожие слова в токенах проекта
            matched_similar = set(similar_words) & project_tokens
            if matched_similar:
                # Добавляем бонус за похожие слова
                similarity += 0.8 * len(matched_similar)
        
        # Способ 3: Косинусное сходство с расширенными терминами
        cosine_sim = calculate_cosine_similarity(query_tf, project_data['tf'])
        similarity = max(similarity, cosine_sim)
        
        # Способ 4: Бонус за точное совпадение с оригинальным запросом
        for orig_word in original_query_words:
            if orig_word in project_name:
                similarity += 0.5
            if orig_word in project_theme:
                similarity += 0.3
        
        if similarity >= threshold:
            similarities.append((project_id, similarity))
    
    # Сортируем по убыванию сходства
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # print(f"📊 Found {len(similarities)} results above threshold {threshold}")
    
    # Выводим детальную информацию только о топ-результатах
    for pid, score in similarities[:3]:
        project_info = project_data_cache.get(pid, {})
        # print(f"   🎯 Project {pid}: '{project_info.get('name', 'N/A')}' - Score: {score:.4f}")
    
    return [{'id': pid, 'score': score} for pid, score in similarities[:top_k]]

# Добавим глобальную переменную для всех токенов
ALL_TOKENS = []

def calculate_cosine_similarity(query_tf, doc_tf):
    """Вычисляет косинусное сходство между запросом и документом"""
    all_words = set(query_tf.keys()) | set(doc_tf.keys())
    
    dot_product = 0
    query_magnitude = 0
    doc_magnitude = 0
    
    for word in all_words:
        query_val = query_tf.get(word, 0)
        doc_val = doc_tf.get(word, 0)
        
        dot_product += query_val * doc_val
        query_magnitude += query_val ** 2
        doc_magnitude += doc_val ** 2
    
    if query_magnitude == 0 or doc_magnitude == 0:
        return 0
    
    return dot_product / (math.sqrt(query_magnitude) * math.sqrt(doc_magnitude))

def normalize_search_term(term):
    """Нормализация поискового запроса"""
    if not term:
        return ""
    
    term = re.sub(r'\s+', ' ', term.lower()).strip()
    return term

@router.get("/projects/", response_model=List[Project])
async def get_projects(
    type: Optional[str] = None,
    theme: Optional[str] = None,
    search: Optional[str] = None,
    smart_search: Optional[str] = None,
    use_synonyms: bool = Query(True, description="Использовать поиск по синонимам"),
    spell_check: bool = Query(True, description="Исправлять орфографические ошибки"),  # Новый параметр
    similarity_threshold: float = Query(0.01, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    conn = None
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        
        # print(f"🎯 RECEIVED REQUEST: type={type}, theme={theme}, search={search}, smart_search={smart_search}, use_synonyms={use_synonyms}, spell_check={spell_check}")
        
        # Инициализируем поисковый индекс при первом вызове
        if not search_index:
            print("🔄 Building search index...")
            build_search_index(conn)
        else:
            print(f"✅ Search index ready with {len(search_index)} projects")
        
        # Создаем функцию для регистронезависимого LIKE
        def ilike(pattern, value):
            if pattern is None or value is None:
                return False
            pattern_regex = pattern.replace('%', '.*').replace('_', '.')
            return bool(re.match(f"^{pattern_regex}$", value, re.IGNORECASE))
        
        conn.create_function("ilike", 2, ilike)
        cursor = conn.cursor()
        
        query = "SELECT * FROM projects WHERE 1=1"
        params = []

        # Обработка умного поиска
        semantic_ids = []
        fallback_search = False
        
        if smart_search:
            # print(f"🎯 SMART SEARCH ACTIVATED: '{smart_search}'")
            normalized_search = normalize_search_term(smart_search)
            # print(f"🎯 Use synonyms: {use_synonyms}, Spell check: {spell_check}")
            
            if use_synonyms or spell_check:
                # Используем улучшенный поиск с синонимами и исправлением ошибок
                semantic_results = spell_aware_semantic_search(normalized_search, similarity_threshold, limit * 5)
            else:
                # Используем обычный улучшенный поиск
                semantic_results = enhanced_semantic_search(normalized_search, similarity_threshold, limit * 5)
            
            # print(f"🎯 Semantic results: {len(semantic_results)} projects found")
            
            semantic_ids = [result['id'] for result in semantic_results]
            
            if semantic_ids:
                # print(f"✅ Found {len(semantic_ids)} projects via semantic search")
                placeholders = ','.join('?' * len(semantic_ids))
                query += f" AND id IN ({placeholders})"
                params.extend(semantic_ids)
            else:
                # print("❌ No results from semantic search, using fallback...")
                fallback_search = True
                query += " AND (ilike(?, name) OR ilike(?, theme))"
                like_pattern = f"%{smart_search}%"
                params.extend([like_pattern, like_pattern])

        # Обычный поиск
        elif search:
            # print(f"🔍 REGULAR SEARCH: '{search}'")
            query += " AND (ilike(?, name) OR ilike(?, theme) OR ilike(?, type))"
            like_pattern = f"%{search}%"
            params.extend([like_pattern, like_pattern, like_pattern])

        # Фильтрация по типу
        if type:
            type_mapping = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
            normalized_type = type_mapping.get(type.lower(), type.lower())
            query += " AND ilike(?, type)"
            params.append(normalized_type)
            # print(f"🔧 Type filter: {normalized_type}")
        
        # Фильтрация по теме
        if theme:
            query += " AND (ilike(?, name) OR ilike(?, theme))"
            like_pattern = f"%{theme}%"
            params.extend([like_pattern, like_pattern])
            # print(f"🔧 Theme filter: {theme}")

        # Сортировка
        if smart_search and semantic_ids and not fallback_search:
            order_case = "CASE "
            for i, project_id in enumerate(semantic_ids):
                order_case += f"WHEN id = {project_id} THEN {i} "
            order_case += f"ELSE {len(semantic_ids)} END"
            query += f" ORDER BY {order_case}, is_premium DESC, likes DESC"
            # print(f"📊 Sorting by semantic relevance")
        else:
            query += " ORDER BY is_premium DESC, likes DESC"
            # print(f"📊 Sorting by premium & likes")

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        # print(f"📝 Final SQL: {query}")
        # print(f"📝 Params count: {len(params)}")

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
        
        # print(f"✅ Returning {len(projects)} projects")
        return projects
        
    except sqlite3.Error as e:
        # print(f"❌ SQL error: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка SQL-запроса: {e}")
    finally:
        if conn:
            conn.close()

def enhanced_semantic_search(query, threshold=0.01, top_k=20):
    """Улучшенный семантический поиск с поддержкой частичных совпадений"""
    global search_index
    
    # print(f"🔍 Starting enhanced search for: '{query}'")
    # print(f"🔍 Threshold: {threshold}, Top K: {top_k}")
    
    if not search_index:
        # print("❌ Search index is empty!")
        return []
    
    query_lower = query.lower()
    query_words = re.findall(r'\b\w{2,}\b', query_lower)
    
    if not query_words:
        # print("❌ No valid words in query")
        return []
    
    # print(f"🔍 Query words: {query_words}")
    
    # Вычисляем сходство для каждого проекта
    similarities = []
    
    for project_id, project_data in search_index.items():
        similarity = 0
        
        # Способ 1: Частичные совпадения
        partial_matches = find_partial_matches(query_lower, project_data['tf'])
        if partial_matches:
            best_match_score = max(score for _, score in partial_matches)
            similarity = max(similarity, best_match_score)
        
        # Способ 2: Косинусное сходство по словам
        if query_words:
            query_tf = {word: 1.0/len(query_words) for word in query_words}
            cosine_sim = calculate_cosine_similarity(query_tf, project_data['tf'])
            similarity = max(similarity, cosine_sim)
        
        # Увеличиваем score для проектов, где слова запроса в названии
        project_info = project_data_cache.get(project_id, {})
        project_name = project_info.get('name', '').lower()
        project_theme = project_info.get('theme', '').lower()
        
        # Проверяем вхождение в название
        for q_word in query_words:
            if q_word in project_name:
                similarity += 0.3
            if q_word in project_theme:
                similarity += 0.2
        
        if similarity >= threshold:
            similarities.append((project_id, similarity))
    
    # Сортируем по убыванию сходства
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # print(f"📊 Found {len(similarities)} results above threshold {threshold}")
    
    # Выводим детальную информацию о топ-результатах
    for pid, score in similarities[:5]:
        project_info = project_data_cache.get(pid, {})
        # print(f"   🎯 Project {pid}: '{project_info.get('name', 'N/A')}'")
        # print(f"      Theme: {project_info.get('theme', 'N/A')}")
        # print(f"      Score: {score:.4f}")
    
    return [{'id': pid, 'score': score} for pid, score in similarities[:top_k]]





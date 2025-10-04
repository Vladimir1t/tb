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

# def find_similar_words_in_index(query_word: str, project_tokens: Set[str], max_distance: int = 2) -> List[str]:
#     """Находит похожие слова в токенах проекта"""
#     similar_words = []
#     for token in project_tokens:
#         distance = levenshtein_distance(query_word, token)
#         if distance <= max_distance and distance > 0:  # Исключаем точные совпадения
#             # Вычисляем степень похожести (1 - normalized_distance)
#             max_len = max(len(query_word), len(token))
#             similarity = 1 - (distance / max_len)
#             similar_words.append((token, similarity))
    
#     # Сортируем по убыванию похожести
#     similar_words.sort(key=lambda x: x[1], reverse=True)
#     return [word for word, score in similar_words[:3]]  

def expand_with_synonyms(word: str) -> Set[str]:
    """Расширяет слово синонимами"""
    synonyms = set()
    word_lower = word.lower()
    
    synonyms.add(word_lower)
    
    # Ищем синонимы в базе
    if word_lower in SYNONYM_DB:
        synonyms.update(SYNONYM_DB[word_lower])
    
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

def build_search_index(conn):
    """Строим улучшенный поисковый индекс с поддержкой синонимов"""
    global search_index, project_data_cache
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, theme, type FROM projects")
    rows = cursor.fetchall()
    
    search_index = {}
    project_data_cache = {}
    
    # print(f"🔍 Building search index for {len(rows)} projects")
    
    all_unique_tokens = set()
    
    for row in rows:
        project = dict(row)
        project_id = project['id']
        project_data_cache[project_id] = project
        
        content = f"{project['name']} {project['theme']} {project['type']}".lower()
        
        words = re.findall(r'\b\w{2,}\b', content)
        
        enhanced_tokens = set()
        for word in words:
            enhanced_tokens.add(word)
            synonyms = expand_with_synonyms(word)
            enhanced_tokens.update(synonyms)
            
            if len(word) > 3:
                for i in range(len(word) - 2):
                    enhanced_tokens.add(word[i:i+3])
        
        word_count = Counter(enhanced_tokens)
        total_words = len(enhanced_tokens)
        
        search_index[project_id] = {
            'tf': {word: count/total_words for word, count in word_count.items()},
            'content': content,
            'original_words': words,
            'all_tokens': set(enhanced_tokens) 
        }        
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
        if distance <= max_distance and distance > 0:  
            max_len = max(len(query_lower), len(token))
            similarity = 1 - (distance / max_len)
            similar_words.append((token, similarity))
    
    # Сортируем по убыванию похожести и берем топ-3
    similar_words.sort(key=lambda x: x[1], reverse=True)
    return [word for word, score in similar_words[:3]]

def spell_aware_semantic_search(query, threshold=0.2, top_k=30):
    """Умный поиск с правильными приоритетами"""
    global search_index
    
    print(f"🔍 Starting spell-aware search for: '{query}'")
    
    if not search_index:
        print("❌ Search index is empty!")
        return []
    
    expanded_terms = expand_query_with_synonyms(query)
    
    if not expanded_terms:
        print("❌ No valid terms after expansion")
        return []
    
    original_query_words = re.findall(r'\b\w{2,}\b', query.lower())
    
    use_detailed_spell_check = len(original_query_words) <= 3
    
    similar_words_cache = {}
    if use_detailed_spell_check:
        for query_word in original_query_words:
            similar_words = find_similar_words_fast(query_word)
            if similar_words:
                similar_words_cache[query_word] = similar_words
    
    query_tf = {term: 1.0/len(expanded_terms) for term in expanded_terms}
    
    similarities = []
    
    for project_id, project_data in search_index.items():
        similarity = 0
        project_info = project_data_cache.get(project_id, {})
        project_name = project_info.get('name', '').lower()
        project_theme = project_info.get('theme', '').lower()
        project_tokens = project_data['all_tokens']
        
        # ПРИОРИТЕТ 1: Точные совпадения в названии (самый высокий приоритет)
        exact_name_matches = 0
        for term in expanded_terms:
            if term in project_name and any(term == word for word in project_data['original_words']):
                exact_name_matches += 1
        if exact_name_matches > 0:
            similarity += exact_name_matches * 3.0  
        
        # ПРИОРИТЕТ 2: Точные совпадения в теме
        exact_theme_matches = 0
        for term in expanded_terms:
            if term in project_theme and any(term == word for word in project_data['original_words']):
                exact_theme_matches += 1
        if exact_theme_matches > 0:
            similarity += exact_theme_matches * 2.0  
        
        # ПРИОРИТЕТ 3: Частичные совпадения в названии
        partial_name_matches = 0
        for term in expanded_terms:
            if term in project_name and not any(term == word for word in project_data['original_words']):
                partial_name_matches += 1
        if partial_name_matches > 0:
            similarity += partial_name_matches * 1.5
        
        # ПРИОРИТЕТ 4: Частичные совпадения в теме
        partial_theme_matches = 0
        for term in expanded_terms:
            if term in project_theme and not any(term == word for word in project_data['original_words']):
                partial_theme_matches += 1
        if partial_theme_matches > 0:
            similarity += partial_theme_matches * 1.0
        
        # ПРИОРИТЕТ 5: Похожие слова
        if use_detailed_spell_check and similar_words_cache:
            similar_word_bonus = 0
            for query_word, similar_words in similar_words_cache.items():
                matched_similar = set(similar_words) & project_tokens
                if matched_similar:
                    similar_word_bonus += min(0.5, 0.2 * len(matched_similar))
            similarity += similar_word_bonus
        
        # ПРИОРИТЕТ 6: 
        cosine_sim = calculate_cosine_similarity(query_tf, project_data['tf'])
        similarity += min(cosine_sim, 1.0)
        
        # Бонус за премиум проекты
        if project_info.get('is_premium'):
            similarity += 0.1
        
        if similarity >= threshold:
            similarities.append((project_id, similarity, exact_name_matches, exact_theme_matches))

    if similarities:
        similarities.sort(key=lambda x: x[1], reverse=True)
        scores = [score for _, score, _, _ in similarities]
        
        if len(scores) > 5:
            top_score = scores[0]
            
            # Динамический порог: минимум 60% от лучшего результата
            dynamic_threshold = max(threshold, top_score * 0.60)
            absolute_min_threshold = 0.4  
            final_threshold = min(dynamic_threshold, absolute_min_threshold)
            
            print(f"🎯 Dynamic threshold: {final_threshold:.3f} (top_score: {top_score:.3f})")
            
            filtered_count_before = len(similarities)
            similarities = [
                (pid, score, name_m, theme_m) 
                for pid, score, name_m, theme_m in similarities 
                if score >= final_threshold
            ]
            filtered_count_after = len(similarities)
            
            print(f"📊 Filtered: {filtered_count_before} → {filtered_count_after} results")
    
    # print(f"📊 Found {len(similarities)} results above threshold {threshold}")
    
    # for pid, score, name_matches, theme_matches in similarities[:5]:
    #     project_info = project_data_cache.get(pid, {})
        # print(f"   🎯 Project {pid}: '{project_info.get('name', 'N/A')}'")
        # print(f"      Theme: {project_info.get('theme', 'N/A')}")
        # print(f"      Score: {score:.4f} (name_matches: {name_matches}, theme_matches: {theme_matches})")
    
    return [{'id': pid, 'score': score} for pid, score, _, _ in similarities[:top_k]]

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
    spell_check: bool = Query(True, description="Исправлять орфографические ошибки"),  
    similarity_threshold: float = Query(0.01, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    conn = None
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        
        # print(f"🎯 RECEIVED REQUEST: type={type}, theme={theme}, search={search}, smart_search={smart_search}, use_synonyms={use_synonyms}, spell_check={spell_check}")
        
        if not search_index:
            print("🔄 Building search index...")
            build_search_index(conn)
        else:
            print(f"✅ Search index ready with {len(search_index)} projects")
        
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
                semantic_results = spell_aware_semantic_search(normalized_search, similarity_threshold, limit * 5)
            else:
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

        if type:
            type_mapping = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
            normalized_type = type_mapping.get(type.lower(), type.lower())
            query += " AND ilike(?, type)"
            params.append(normalized_type)
            # print(f"🔧 Type filter: {normalized_type}")
        
        if theme:
            query += " AND (ilike(?, name) OR ilike(?, theme))"
            like_pattern = f"%{theme}%"
            params.extend([like_pattern, like_pattern])
            # print(f"🔧 Theme filter: {theme}")

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
        
        project_info = project_data_cache.get(project_id, {})
        project_name = project_info.get('name', '').lower()
        project_theme = project_info.get('theme', '').lower()
        
        for q_word in query_words:
            if q_word in project_name:
                similarity += 0.3
            if q_word in project_theme:
                similarity += 0.2
        
        if similarity >= threshold:
            similarities.append((project_id, similarity))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # print(f"📊 Found {len(similarities)} results above threshold {threshold}")
    
    for pid, score in similarities[:5]:
        project_info = project_data_cache.get(pid, {})
        # print(f"   🎯 Project {pid}: '{project_info.get('name', 'N/A')}'")
        # print(f"      Theme: {project_info.get('theme', 'N/A')}")
        # print(f"      Score: {score:.4f}")
    
    return [{'id': pid, 'score': score} for pid, score in similarities[:top_k]]





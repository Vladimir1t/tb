from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Optional, Dict, Set, Tuple
import sqlite3
import base64
import re
import math
from collections import Counter
import threading
from models import Project
from database_connect import get_db_connection
from .synonyms import SYNONYM_DB
from auth import verify_telegram_auth
from functools import lru_cache
import time
import hashlib
import gc
import psutil
import os
import random 
from datetime import datetime, timedelta

router = APIRouter()

search_index = {}
project_data_cache = {}
ALL_TOKENS = []
_index_lock = threading.Lock()

_search_cache = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 300

class SearchCache:
    def __init__(self, max_size=500, ttl=300):
        self._cache = {}
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.Lock()
    
    def get(self, key):
        with self._lock:
            if key in self._cache:
                data, timestamp = self._cache[key]
                if time.time() - timestamp < self._ttl:
                    return data
                else:
                    del self._cache[key]
            return None
    
    def set(self, key, data):
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._cleanup()
            self._cache[key] = (data, time.time())
    
    def _cleanup(self):
        """Очистка устаревших записей"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self._ttl
        ]
        for key in expired_keys:
            del self._cache[key]
        
        if len(self._cache) >= self._max_size:
            sorted_keys = sorted(
                self._cache.keys(), 
                key=lambda k: self._cache[k][1]
            )
            for key in sorted_keys[:self._max_size // 2]:
                del self._cache[key]
    
    def clear(self):
        with self._lock:
            self._cache.clear()
    
    def size(self):
        with self._lock:
            return len(self._cache)

# ЗАМЕНА простого словаря на умный кэш
_search_cache = SearchCache(max_size=500, ttl=300)

def get_search_cache_key(query: str, params: dict) -> str:
    """Генерирует ключ для кэша поиска"""
    key_data = f"{query}_{params}"
    return hashlib.md5(key_data.encode()).hexdigest()

def clear_memory():
    """Очистка памяти"""
    gc.collect()

    # Очистка кэша поиска если он слишком большой
    if _search_cache.size() > 1000:
        print(f"🧹 Clearing large cache: {_search_cache.size()} entries")
        _search_cache.clear()

@lru_cache(maxsize=100)
def perform_search_once(query: str, use_synonyms: bool, spell_check: bool, threshold: float) -> tuple:
    """Оптимизированный поиск с ограничениями"""
    print(f"🔍 Performing search for: '{query}'")
    
    if len(query) > 100:
        query = query[:100]
    
    normalized_search = normalize_search_term(query)
    search_limit = 500 if use_synonyms or spell_check else 200
    
    if use_synonyms or spell_check:
        semantic_results = spell_aware_semantic_search(normalized_search, threshold, search_limit)
    else:
        semantic_results = enhanced_semantic_search(normalized_search, threshold, search_limit)
    
    semantic_ids = [result['id'] for result in semantic_results]
    print(f"✅ Found {len(semantic_ids)} total projects via semantic search")
    
    return tuple(semantic_ids)

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
        
        with _index_lock:
            if not search_index:
                print("🔄 Building search index...")
                build_search_index(conn)
            else:
                print(f"✅ Use ready Search index for {len(search_index)} projects")
        
        def ilike(pattern, value):
            if pattern is None or value is None:
                return False
            pattern_regex = pattern.replace('%', '.*').replace('_', '.')
            return bool(re.match(f"^{pattern_regex}$", value, re.IGNORECASE))
        
        conn.create_function("ilike", 2, ilike)
        cursor = conn.cursor()
        
        query = "SELECT * FROM projects WHERE 1=1"
        params = []

        semantic_ids_smart = []
        semantic_ids_theme = []
        fallback_smart_search = False
        fallback_theme_search = False
        
        # ОБРАБОТКА SMART_SEARCH (по всем полям)
        if smart_search:
            print(f"====== 🔍 Smart search: '{smart_search}' ======")
            
            cache_key_smart = f"smart_{smart_search}_{use_synonyms}_{spell_check}_{similarity_threshold}"
            cached_result = _search_cache.get(cache_key_smart)
            
            if cached_result is None:
                semantic_results_smart = perform_search_once(smart_search, use_synonyms, spell_check, similarity_threshold)
                _search_cache.set(cache_key_smart, semantic_results_smart)
            else:
                semantic_results_smart = cached_result
                print(f"📦 Using cached smart search results ({len(semantic_results_smart)} items)")
            
            semantic_ids_smart = list(semantic_results_smart)
            
            if not semantic_ids_smart:
                print("❌ No results from smart search, using fallback...")
                fallback_smart_search = True
                query += " AND (ilike(?, name) OR ilike(?, theme) OR ilike(?, type))"
                like_pattern = f"%{smart_search}%"
                params.extend([like_pattern, like_pattern, like_pattern])
        
        # ОБРАБОТКА THEME (только по темам с smart search)
        if theme:
            print(f"====== 🎨 Theme smart search: '{theme}' ======")
            
            cache_key_theme = f"theme_{theme}_{use_synonyms}_{spell_check}_{similarity_threshold}"
            cached_result = _search_cache.get(cache_key_theme)
            
            if cached_result is None:
                semantic_results_theme = perform_search_once(theme, use_synonyms, spell_check, similarity_threshold)
                _search_cache.set(cache_key_theme, semantic_results_theme)
            else:
                semantic_results_theme = cached_result
                print(f"Using cached theme search results ({len(semantic_results_theme)} items)")
            
            semantic_ids_theme = list(semantic_results_theme)
            
            if not semantic_ids_theme:
                print("❌ No results from theme search, using fallback...")
                fallback_theme_search = True
                query += " AND ilike(?, theme)"
                like_pattern = f"%{theme}%"
                params.append(like_pattern)
        
        # ОБРАБОТКА REGULAR SEARCH
        elif search:
            #print(f"🔍 Regular search: '{search}'")
            query += " AND (ilike(?, name) OR ilike(?, theme) OR ilike(?, type))"
            like_pattern = f"%{search}%"
            params.extend([like_pattern, like_pattern, like_pattern])

        # ПРИМЕНЕНИЕ SEMANTIC IDS ЕСЛИ ЕСТЬ РЕЗУЛЬТАТЫ
        semantic_ids_to_use = []
        
        if semantic_ids_smart and semantic_ids_theme:
            semantic_ids_to_use = list(set(semantic_ids_smart) & set(semantic_ids_theme))
            print(f"===== 🎯 Combined smart + theme search: {len(semantic_ids_smart)} smart ∩ {len(semantic_ids_theme)} theme = {len(semantic_ids_to_use)} projects")
            
        elif semantic_ids_smart:
            semantic_ids_to_use = semantic_ids_smart
            print(f"===== 🎯 Using smart search results: {len(semantic_ids_to_use)} projects =====")
            
        elif semantic_ids_theme:
            semantic_ids_to_use = semantic_ids_theme
            print(f"===== 🎯 Using theme search results: {len(semantic_ids_to_use)} projects =====")
        
        # ДОБАВЛЯЕМ SEMANTIC IDS В ЗАПРОС
        if semantic_ids_to_use and type:
            type_mapping = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
            normalized_type = type_mapping.get(type.lower(), type.lower())
            
            filtered_semantic_ids = []
            for project_id in semantic_ids_to_use:
                project_info = project_data_cache.get(project_id, {})
                if project_info.get('type', '').lower() == normalized_type:
                    filtered_semantic_ids.append(project_id)
            
            print(f"🔍 After type filter: {len(filtered_semantic_ids)}/{len(semantic_ids_to_use)} projects are {normalized_type}s")
            semantic_ids_to_use = filtered_semantic_ids

        # ТЕПЕРЬ применяем пагинацию к отфильтрованным ID
        paginated_ids = []
        if semantic_ids_to_use:
            start_idx = offset
            end_idx = offset + limit
            paginated_ids = semantic_ids_to_use[start_idx:end_idx]
            
            if paginated_ids:
                placeholders = ','.join('?' * len(paginated_ids))
                query += f" AND id IN ({placeholders})"
                params.extend(paginated_ids)
                print(f"📄 Pagination: {start_idx}-{end_idx} of {len(semantic_ids_to_use)} {type} projects")
            else:
                query += " AND 1=0"
                print(f"❌ No {type} projects in paginated range")

        # ФИЛЬТР ПО TYPE (применяется всегда если указан)
        if type:
            type_mapping = {'channels': 'channel', 'bots': 'bot', 'apps': 'mini_app'}
            normalized_type = type_mapping.get(type.lower(), type.lower())
            query += " AND ilike(?, type)"
            params.append(normalized_type)

        # СОРТИРОВКА
        if semantic_ids_to_use and paginated_ids:
            order_case = "CASE "
            for i, project_id in enumerate(paginated_ids):
                order_case += f"WHEN id = {project_id} THEN {i} "
            order_case += f"ELSE {len(paginated_ids)} END"
            query += f" ORDER BY {order_case}"
        else:
            query += " ORDER BY is_premium DESC, likes DESC"

        # ПАГИНАЦИЯ для случаев без semantic results или при fallback
        if (not semantic_ids_to_use or not paginated_ids) and (not smart_search or fallback_smart_search) and (not theme or fallback_theme_search):
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

       # print(f"📝 Executing query with {len(params)} params")

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
        
        print(f"✅ Returning {len(projects)} projects")
        return projects
        
    except sqlite3.Error as e:
        print(f"❌ SQL error: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка SQL-запроса: {e}")
    finally:
        if random.random() < 0.1:  # 10% chance чтобы не замедлять
            clear_memory()
        if conn:
            conn.close()

@router.post("/memory-status")
async def memory_status():
    """Статус использования памяти"""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
        "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
        "search_index_size": len(search_index),
        "project_cache_size": len(project_data_cache),
        "tokens_count": len(ALL_TOKENS),
        "search_cache_size": _search_cache.size()
    }

@router.post("/clear-search-cache")
async def clear_search_cache():
    """Очищает кэш поиска и освобождает память"""
    perform_search_once.cache_clear()
    _search_cache.clear()    
    gc.collect()
    
    return {
        "message": "Search cache cleared and memory freed",
        "memory_status": await memory_status()
    }

def find_partial_matches(query: str, doc_tf: Dict[str, float]) -> List[Tuple[str, float]]:
    """Находит частичные совпадения в документе"""
    matches = []
    query_terms = query.lower().split()
    
    for term in query_terms:
        if len(term) < 2:
            continue
            
        for doc_term, score in doc_tf.items():
            if term in doc_term or doc_term in term:
                similarity = min(len(term), len(doc_term)) / max(len(term), len(doc_term))
                if similarity > 0.6:  # Порог схожести
                    matches.append((doc_term, score * similarity))
    
    return matches

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

def stem_word(word: str) -> str:
    """Базовая стеммизация для русского и английского языков"""
    if not word or len(word) < 3:
        return word
    
    russian_endings = [
        'ов', 'ев', 'ин', 'ын', 'ых', 'их', 'ое', 'ее', 'ые', 'ие', 'ому', 'ему', 
        'ыми', 'ими', 'ом', 'ем', 'ах', 'ях', 'ами', 'ями', 'ую', 'юю', 'ей', 'ой',
        'а', 'я', 'о', 'е', 'и', 'ы', 'у', 'ю', 'ь', 'й', 'ть', 'ти', 'л', 'ла', 'ло', 'ли'
    ]
    
    english_endings = [
        'ing', 'ed', 'es', 's', 'ly', 'er', 'est', 'ment', 'ness', 'tion', 'sion'
    ]
    
    for ending in english_endings:
        if word.endswith(ending) and len(word) > len(ending) + 2:
            return word[:-len(ending)]
    
    for ending in russian_endings:
        if word.endswith(ending) and len(word) > len(ending) + 2:
            return word[:-len(ending)]
    
    return word

def normalize_and_stem(text: str) -> Set[str]:
    """Нормализация текста со стеммингом"""
    words = re.findall(r'\b\w{2,}\b', text.lower())
    stemmed_words = set()
    
    for word in words:
        stemmed_words.add(word)
        stemmed = stem_word(word)
        if stemmed != word and len(stemmed) >= 2:
            stemmed_words.add(stemmed)
    
    return stemmed_words

def expand_with_synonyms(word: str) -> Set[str]:
    """Расширяет слово синонимами с учетом стемминга"""
    synonyms = set()
    word_lower = word.lower()
    
    synonyms.add(word_lower)
    
    stemmed = stem_word(word_lower)
    if stemmed != word_lower:
        synonyms.add(stemmed)
    
    # Ищем синонимы в базе
    if word_lower in SYNONYM_DB:
        synonyms.update(SYNONYM_DB[word_lower])
    
    if stemmed in SYNONYM_DB:
        synonyms.update(SYNONYM_DB[stemmed])
    
    for key, synonym_list in SYNONYM_DB.items():
        if word_lower in synonym_list or stemmed in synonym_list:
            synonyms.add(key)
            synonyms.update(synonym_list)
    
    return synonyms

def expand_query_with_synonyms(query: str) -> Set[str]:
    """Расширяет поисковый запрос синонимами с учетом стемминга"""
    words = re.findall(r'\b\w{2,}\b', query.lower())
    expanded_terms = set()
    
    for word in words:
        synonyms = expand_with_synonyms(word)
        expanded_terms.update(synonyms)
    
    return expanded_terms

def build_search_index(conn):
    """Оптимизированное построение индекса с очисткой памяти"""
    global search_index, project_data_cache, ALL_TOKENS
    
    with _index_lock:
        print(f"🔄 Building optimized search index...")
        
        # ОЧИСТКА ПАМЯТИ ПЕРЕД СОЗДАНИЕМ НОВОГО ИНДЕКСА
        old_index_size = len(search_index)
        old_cache_size = len(project_data_cache)
        old_tokens_size = len(ALL_TOKENS)
        
        # Явная очистка
        search_index.clear()
        project_data_cache.clear()
        ALL_TOKENS.clear()
        
        # Принудительная сборка мусора
        gc.collect()
        
        print(f"🧹 Cleared: index={old_index_size}, cache={old_cache_size}, tokens={old_tokens_size}")
        
        # НОВОЕ: Ограничиваем размер данных
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, theme, type, is_premium FROM projects")
        rows = cursor.fetchall()
        
        all_unique_tokens = set()
        processed_count = 0
        
        for row in rows:
            project = dict(row)
            project_id = project['id']
            project_data_cache[project_id] = project
            
            content = f"{project['name']} {project['theme']} {project['type']}".lower()
            
            # ОПТИМИЗАЦИЯ: Ограничиваем количество токенов на проект
            stemmed_words = normalize_and_stem(content)
            enhanced_tokens = set()
            
            for word in list(stemmed_words)[:50]:  # Максимум 50 слов на проект
                enhanced_tokens.add(word)
                synonyms = expand_with_synonyms(word)
                # Ограничиваем синонимы
                enhanced_tokens.update(list(synonyms)[:10])
                
                if len(word) > 3:
                    for i in range(min(len(word) - 2, 5)):  # Максимум 5 n-gram
                        enhanced_tokens.add(word[i:i+3])
            
            word_count = Counter(enhanced_tokens)
            total_words = len(enhanced_tokens)
            
            search_index[project_id] = {
                'tf': {word: count/total_words for word, count in word_count.items()},
                'content': content,
                'original_words': stemmed_words,
                'all_tokens': set(enhanced_tokens),
                'is_premium': project.get('is_premium', False)
            }
            
            all_unique_tokens.update(enhanced_tokens)
            processed_count += 1
            
            # Периодическая сборка мусора для больших баз
            if processed_count % 100 == 0:
                gc.collect()
        
        ALL_TOKENS = list(all_unique_tokens)
        print(f"📊 Optimized index built: {len(ALL_TOKENS)} tokens for {processed_count} projects")
        
        # Очищаем кэш поиска при обновлении индекса
        clear_search_cache()

def find_similar_words_fast(query_word: str, max_distance: int = 2) -> List[str]:
    """Быстрый поиск похожих слов среди всех токенов индекса"""
    similar_words = []
    query_lower = query_word.lower()
    query_stemmed = stem_word(query_lower)
    
    for token in ALL_TOKENS:
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
    """Умный поиск с правильными приоритетами и отбрасыванием по score"""
    global search_index
    
   # print(f"🔍 Starting spell-aware search for: '{query}'")
    
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
        
        # ПРИОРИТЕТ 6: Косинусное сходство
        cosine_sim = calculate_cosine_similarity(query_tf, project_data['tf'])
        similarity += min(cosine_sim, 1.0)
        
        # Бонус за премиум проекты
        if project_info.get('is_premium'):
            similarity += 0.1
        
        if similarity >= threshold:
            similarities.append((project_id, similarity, exact_name_matches, exact_theme_matches))

    # ВАЖНО: Сохраняем оригинальную логику сортировки и отбрасывания
    if similarities:
        similarities.sort(key=lambda x: x[1], reverse=True)
        scores = [score for _, score, _, _ in similarities]
        
        if len(scores) > 2:
            top_score = scores[0]
            
            # Динамический порог: минимум 60% от лучшего результата
            dynamic_threshold = max(threshold, top_score * 0.60)
            absolute_min_threshold = 0.4  
            final_threshold = min(dynamic_threshold, absolute_min_threshold)
            
            # print(f"🎯 Dynamic threshold: {final_threshold:.3f}")
            
            filtered_count_before = len(similarities)
            similarities = [
                (pid, score, name_m, theme_m) 
                for pid, score, name_m, theme_m in similarities 
                if score >= final_threshold
            ]
            filtered_count_after = len(similarities)
            
            print(f"📊 Filtered: {filtered_count_before} → {filtered_count_after} results")
    
   # print(f"📊 Found {len(similarities)} results above threshold {threshold}")
    
    for pid, score, name_matches, theme_matches in similarities[:5]:
        project_info = project_data_cache.get(pid, {})
        print(f"   🎯 Project {pid}: '{project_info.get('name', 'N/A')}'")
        print(f"      Theme: {project_info.get('theme', 'N/A')}")
        print(f"      Score: {score:.4f} (name_matches: {name_matches}, theme_matches: {theme_matches})")
    
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

def enhanced_semantic_search(query, threshold=0.01, top_k=20):
    """Улучшенный семантический поиск с поддержкой частичных совпадений"""
    global search_index
    
   # print(f"🔍 Starting enhanced search for: '{query}'")
   # print(f"🔍 Threshold: {threshold}, Top K: {top_k}")
    
    if not search_index:
        print("❌ Search index is empty!")
        return []
    
    query_lower = query.lower()
    query_words = re.findall(r'\b\w{2,}\b', query_lower)
    
    if not query_words:
        print("❌ No valid words in query")
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
    
    print(f"📊 Found {len(similarities)} results above threshold {threshold}")
    
    for pid, score in similarities[:5]:
        project_info = project_data_cache.get(pid, {})
        print(f"   🎯 Project {pid}: '{project_info.get('name', 'N/A')}'")
        print(f"      Theme: {project_info.get('theme', 'N/A')}")
        print(f"      Score: {score:.4f}")
    
    return [{'id': pid, 'score': score} for pid, score in similarities[:top_k]]

def refresh_search_index(conn):
    """Принудительное обновление поискового индекса"""
    print("🔄 Forced search index refresh...")
    build_search_index(conn)
#!/bin/bash

echo "🧪 Запуск режима локального тестирования..."

DEBUG_USER_ID=${1:-999001}
BACKEND_PORT=8000
FRONTEND_PORT=5500

# Проверяем что venv существует
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено!"
    echo "Запустите: python3 -m venv venv"
    exit 1
fi

# Активируем venv
source venv/bin/activate

# Проверяем и создаем таблицы если их нет
echo "🔍 Проверка базы данных..."

# Если файл БД — это Git LFS-пойнтер, удаляем и создаем заново
if [ -f "Backend/aggregator.db" ]; then
    if head -n 1 Backend/aggregator.db | grep -q "git-lfs.github.com/spec/v1"; then
        echo "⚠️ Найден LFS-пойнтер базы данных. Переинициализируем локальную БД..."
        rm -f Backend/aggregator.db
    fi
fi

# Базовые таблицы
sqlite3 Backend/aggregator.db "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, stars INTEGER DEFAULT 0, balance REAL DEFAULT 0, preferences TEXT, survey_completed INTEGER DEFAULT 0);" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE TABLE IF NOT EXISTS tasks (user_id INTEGER, task_type TEXT, completed BOOLEAN DEFAULT 0, PRIMARY KEY (user_id, task_type));" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, name TEXT, link TEXT NOT NULL, theme TEXT NOT NULL, is_premium BOOLEAN DEFAULT 0, likes INTEGER DEFAULT 0, subscribers INTEGER DEFAULT 0, user_id INTEGER DEFAULT 1, icon BLOB);" 2>/dev/null

# Таблицы рекомендательной системы (идемпотентно)
sqlite3 Backend/aggregator.db "CREATE TABLE IF NOT EXISTS interactions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, project_id INTEGER NOT NULL, event_type TEXT NOT NULL, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP);" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE INDEX IF NOT EXISTS idx_interactions_user ON interactions(user_id, ts DESC);" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE INDEX IF NOT EXISTS idx_interactions_project ON interactions(project_id, ts DESC);" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE INDEX IF NOT EXISTS idx_interactions_event ON interactions(event_type, ts DESC);" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE TABLE IF NOT EXISTS search_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, query TEXT NOT NULL, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP);" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE INDEX IF NOT EXISTS idx_search_logs_user ON search_logs(user_id, ts DESC);" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE TABLE IF NOT EXISTS recommendations_cache (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, project_id INTEGER NOT NULL, score REAL NOT NULL, reason TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id, project_id));" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE INDEX IF NOT EXISTS idx_recommendations_cache_user ON recommendations_cache(user_id, score DESC);" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE TABLE IF NOT EXISTS project_metrics (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, date DATE NOT NULL, subscribers INTEGER DEFAULT 0, likes INTEGER DEFAULT 0, impressions INTEGER DEFAULT 0, clicks INTEGER DEFAULT 0, UNIQUE(project_id, date));" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE INDEX IF NOT EXISTS idx_project_metrics ON project_metrics(project_id, date DESC);" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE TABLE IF NOT EXISTS user_profiles (user_id INTEGER PRIMARY KEY, profile_json TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);" 2>/dev/null

# Тестовые данные для проектов, если таблица пуста
PROJECTS_COUNT=$(sqlite3 Backend/aggregator.db "SELECT COUNT(*) FROM projects;" 2>/dev/null || echo 0)
if [ -z "$PROJECTS_COUNT" ] || [ "$PROJECTS_COUNT" = "0" ]; then
    echo "🌱 Наполняем тестовыми данными..."
    sqlite3 Backend/aggregator.db "INSERT INTO projects (type,name,link,theme,is_premium,likes,subscribers,user_id,icon) VALUES
        ('channel','Tech News','https://t.me/technews','технологии',0,120,35000,1,NULL),
        ('channel','Sport Daily','https://t.me/sportdaily','спорт',0,80,22000,1,NULL),
        ('bot','WeatherBot','https://t.me/weather_bot','погода',0,45,0,1,NULL),
        ('bot','TranslateBot','https://t.me/translate_bot','образование',0,60,0,1,NULL),
        ('mini_app','Task Tracker','https://t.me/tasktracker','бизнес',0,30,0,1,NULL),
        ('mini_app','Learn English','https://t.me/learnenglish','образование',0,75,0,1,NULL)
    ;" 2>/dev/null
fi

echo "✅ База данных готова"

# Запускаем миграции рекомендательной системы (идемпотентно)
echo "🧩 Запуск миграций..."
bash ./run_migrations.sh >/dev/null 2>&1 || true

# Запускаем Backend в фоне
echo "🔄 Запуск Backend..."
cd Backend
uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT} --reload &
BACKEND_PID=$!
cd ..

echo "✅ Backend запущен (PID: $BACKEND_PID)"
echo "📡 API: http://localhost:${BACKEND_PORT}"
echo ""

# Запускаем простой http сервер для Frontend
echo "🌐 Запуск локального сервера Frontend..."
cd Frontend
python3 -m http.server ${FRONTEND_PORT} >/dev/null 2>&1 &
FRONTEND_PID=$!
cd ..

echo "✅ Frontend сервер запущен (PID: $FRONTEND_PID)"
echo ""

# Ждем запуска
echo "⏳ Ожидание запуска сервисов (3 сек)..."
sleep 3

# Открываем Frontend c debug_user
TEST_URL="http://localhost:${FRONTEND_PORT}/index.html?debug_user=${DEBUG_USER_ID}"
echo "🌍 Открытие Frontend в браузере (debug_user=${DEBUG_USER_ID})..."
open "${TEST_URL}"

echo ""
echo "✅ Тестовый режим запущен!"
echo "   Frontend: ${TEST_URL}"
echo ""
echo "📋 Для остановки приложений:"
echo "   kill $BACKEND_PID"
echo "   kill $FRONTEND_PID"

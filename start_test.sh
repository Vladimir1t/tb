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
sqlite3 Backend/aggregator.db "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, stars INTEGER DEFAULT 0, balance REAL DEFAULT 0, preferences TEXT, survey_completed INTEGER DEFAULT 0);" 2>/dev/null
sqlite3 Backend/aggregator.db "CREATE TABLE IF NOT EXISTS tasks (user_id INTEGER, task_type TEXT, completed BOOLEAN DEFAULT 0, PRIMARY KEY (user_id, task_type));" 2>/dev/null
echo "✅ База данных готова"

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

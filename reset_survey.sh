#!/bin/bash

# Скрипт для сброса статуса опроса

echo "🔄 Сброс статуса опроса"
echo ""

if [ -z "$1" ]; then
    echo "Использование: ./reset_survey.sh USER_ID"
    echo "Например: ./reset_survey.sh 123456"
    echo ""
    echo "Или сбросить для всех пользователей:"
    echo "./reset_survey.sh all"
    exit 1
fi

cd Backend

if [ "$1" = "all" ]; then
    echo "🗑️  Сброс для ВСЕХ пользователей..."
    sqlite3 aggregator.db "UPDATE users SET survey_completed = 0, preferences = NULL;"
    echo "✅ Сброс выполнен для всех пользователей"
else
    echo "🗑️  Сброс для пользователя ID: $1"
    sqlite3 aggregator.db "UPDATE users SET survey_completed = 0, preferences = NULL WHERE id = $1;"
    echo "✅ Сброс выполнен"
    echo ""
    echo "📊 Текущий статус:"
    sqlite3 aggregator.db "SELECT id, survey_completed, preferences FROM users WHERE id = $1;"
fi

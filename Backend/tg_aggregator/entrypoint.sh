#!/bin/sh

# Выходим из скрипта, если любая команда завершится с ошибкой
set -e

# 1. Применяем миграции базы данных
echo "Applying database migrations..."
python manage.py migrate --noinput

# 2. Запускаем Gunicorn сервер
echo "Starting Gunicorn server..."
exec gunicorn tg_aggregator.wsgi:application --bind 0.0.0.0:8000
# Используем современный и легковесный образ Python
FROM python:3.11-slim

# Устанавливаем переменные окружения для чистоты сборки и логирования
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# --- ШАГ 1: Установка зависимостей ---
# Копируем файл с зависимостями из локальной папки Backend/
# в корень рабочей директории /app контейнера
COPY Backend/requirements.txt .

# Устанавливаем Gunicorn и все зависимости из requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir gunicorn && \
    pip install --no-cache-dir -r requirements.txt

# --- ШАГ 2: Копирование кода приложения ---
# Копируем весь код Django-проекта из локальной папки Backend/tg_aggregator/
# в рабочую директорию /app контейнера.
# Теперь manage.py будет лежать в /app/manage.py
COPY Backend/tg_aggregator/ .

# Открываем порт, на котором будет работать Gunicorn
EXPOSE 8000

# Указываем, что при старте контейнера нужно запустить скрипт entrypoint.sh
# Этот скрипт уже находится в /app, так как мы скопировали его на шаге 2
ENTRYPOINT ["/app/entrypoint.sh"]
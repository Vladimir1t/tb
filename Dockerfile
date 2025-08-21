FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /app/Backend

COPY aggregator.db aggregator.db

EXPOSE 8000

# Запускаем Uvicorn из папки Backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
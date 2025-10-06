FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Явно копируем БД и проверяем её наличие
RUN ls -la Backend/ && \
    if [ -f Backend/aggregator.db ]; then \
        echo "✅ Database file found, checking integrity..." && \
        sqlite3 Backend/aggregator.db "PRAGMA integrity_check;" || echo "⚠️ Database may be corrupted"; \
    else \
        echo "❌ Database file not found!"; \
    fi

WORKDIR /app/Backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
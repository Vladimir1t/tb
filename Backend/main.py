# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
import logging
from contextlib import asynccontextmanager
from scripts import database

from routers import projects, users, debug
from bot import run_bot

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет запуском и остановкой фоновых задач (например, бота).
    """
    logger.info("Starting bot in a background thread...")
    # bot_thread = threading.Thread(target=run_bot, daemon=True)
    # bot_thread.start()
    database.shuffle_database('aggregator.db')
    
    yield 
    
    logger.info("Application is shutting down.")

# Создаем приложение FastAPI и передаем ему lifespan менеджер
app = FastAPI(lifespan=lifespan)

# Middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[*],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Подключение роутеров
app.include_router(projects.router, tags=["Projects"])
app.include_router(users.router, tags=["Users"])
app.include_router(debug.router, tags=["Debug"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
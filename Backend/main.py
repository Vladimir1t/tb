from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
import logging
import asyncio
from contextlib import asynccontextmanager
from scripts import database

from routers import projects, users, debug
from bot import run_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def periodic_shuffle():
    """Фоновая задача для периодического перемешивания БД"""
    while True:
        try:
            # перемешивание бд каждые 3 часа
            await asyncio.sleep(3 * 60 * 60)  
            logger.info("Starting scheduled database shuffle...")
            database.shuffle_database('aggregator.db')
            logger.info("Database shuffle completed successfully")
        except Exception as e:
            logger.error(f"Error during scheduled shuffle: {e}")
            await asyncio.sleep(300)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет запуском и остановкой фоновых задач.
    """
    logger.info("Initial database shuffle...")
    database.shuffle_database('aggregator.db')
    # Запускаем фоновую задачу
    task = asyncio.create_task(periodic_shuffle())
    
    yield 
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Background shuffle task stopped")
    
    logger.info("Application is shutting down.")

# Создаем приложение FastAPI и передаем ему lifespan менеджер
app = FastAPI(lifespan=lifespan)

# Middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(projects.router, tags=["Projects"])
app.include_router(users.router, tags=["Users"])
app.include_router(debug.router, tags=["Debug"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
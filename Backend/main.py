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

class IndexManager:
    """Менеджер для управления поисковым индексом"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IndexManager, cls).__new__(cls)
            cls._instance.needs_refresh = True
            cls._instance.lock = asyncio.Lock()
        return cls._instance
    
    async def mark_refreshed(self):
        """Пометить индекс как обновленный"""
        async with self.lock:
            self.needs_refresh = False
            logger.info("Search index marked as refreshed")

index_manager = IndexManager()

async def refresh_search_index():
    """Принудительно обновить поисковый индекс"""
    try:
        logger.info("Forcing search index refresh...")
        
        from routers.projects import build_search_index
        from database_connect import get_db_connection
        
        conn = None
        try:
            conn = get_db_connection()
            build_search_index(conn)
            await index_manager.mark_refreshed()
            logger.info("Search index refreshed successfully")
        except Exception as e:
            logger.error(f"❌ Failed to refresh search index: {e}")
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        logger.error(f"❌ Error in refresh_search_index: {e}")

async def periodic_shuffle():
    """Фоновая задача для периодического перемешивания БД с обновлением индекса"""
    while True:
        try:
            # Перемешивание БД каждые 2 часа 
            await asyncio.sleep(3 * 60 * 60)  
            #logger.info("🔄 Starting scheduled database shuffle...")
            
            database.shuffle_database('aggregator.db')
            logger.info("--- Database shuffle completed successfully ---")
            await refresh_search_index()
            
        except Exception as e:
            logger.error(f"❌ Error during scheduled shuffle: {e}")
            await asyncio.sleep(300)  

async def initial_setup():
    """Первоначальная настройка при запуске приложения"""
    try:
        logger.info("--- Starting initial setup ---")
        # logger.info("🔄 Initial database shuffle...")
        # database.shuffle_database('aggregator.db')
        
        await refresh_search_index()
        logger.info("Initial setup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during initial setup: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет запуском и остановкой фоновых задач.
    """
    await initial_setup()
    
    shuffle_task = asyncio.create_task(periodic_shuffle())
    yield 
    
    shuffle_task.cancel()
    try:
        await shuffle_task
    except asyncio.CancelledError:
        logger.info("🛑 Background shuffle task stopped")
    
    logger.info("🔴 Application is shutting down.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # тут поменять для сервака
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Простой health check"""
    return {"status": "healthy", "message": "Server is running"}

app.include_router(projects.router, tags=["Projects"]) # тут поменять для сервака prefix="/api"
app.include_router(users.router, tags=["Users"])       # тут поменять для сервака prefix="/api"
app.include_router(debug.router, tags=["Debug"])       # тут поменять для сервака prefix="/api"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
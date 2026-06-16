import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database.redis import get_redis, close_redis
from src.routes.generation import router as core_generation_router

logger = logging.getLogger("ai_service.main")
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Establish connection layer on startup boot
    await get_redis(logger)
    yield
    # Tear down connections gracefully when stopping
    await close_redis(logger)

app = FastAPI(title="Central Intelligent Inference Engine", lifespan=app_lifespan)

# Include unified agent adapter path
app.include_router(core_generation_router)
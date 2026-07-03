import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.config.config import USER_ID_HEADER_NAME, TRACE_ID_HEADER_NAME, TIME_ZONE_HEADER_NAME
from src.database.redis import get_redis, close_redis
from src.middlewares.LoggingMiddleware import LoggingMiddleware
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

custom_headers = [
    USER_ID_HEADER_NAME,
    TRACE_ID_HEADER_NAME,
    TIME_ZONE_HEADER_NAME
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "DELETE", "PUT", "UPDATE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=custom_headers,
)
app.add_middleware(LoggingMiddleware)
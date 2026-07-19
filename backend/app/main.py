import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.db.seed import seed_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("iqe")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.sqlite_path.exists():
        logger.info("No database found at %s — seeding it now.", settings.sqlite_path)
        seed_database()
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY is not set — /api/query will fail until backend/.env is filled in.")
    yield


app = FastAPI(
    title="Intelligent Query Engine",
    description="Natural language to SQL over a t-shirt store inventory, powered by Gemini.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

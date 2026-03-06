import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.api.webhooks import router as webhooks_router
from src.api.admin import router as admin_router
from src.store.image_dedup import ImageDedupStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize SQLite store
    app.state.image_dedup = ImageDedupStore()
    logging.info("KB Processor started")
    yield
    # Shutdown
    logging.info("KB Processor shutting down")


app = FastAPI(title="Focus Service Knowledge Base Processor", lifespan=lifespan)

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

app.include_router(webhooks_router, prefix="/webhooks")
app.include_router(admin_router, prefix="/admin")


@app.get("/health-check")
async def health_check():
    return {"status": "ok"}

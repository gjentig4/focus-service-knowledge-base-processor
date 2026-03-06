import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from src.pipeline.orchestrator import process_article

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/process/{article_id}", status_code=202)
async def process_single(article_id: int, background_tasks: BackgroundTasks):
    logger.info(f"Manual trigger: processing article {article_id}")
    background_tasks.add_task(process_article, article_id)
    return {"status": "accepted", "article_id": article_id}


@router.post("/retry/{article_id}", status_code=202)
async def retry_article(article_id: int, background_tasks: BackgroundTasks):
    logger.info(f"Retry: processing article {article_id}")
    background_tasks.add_task(process_article, article_id)
    return {"status": "accepted", "article_id": article_id}

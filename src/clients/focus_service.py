import logging

import httpx

from src.config import settings
from src.models.processed_document import ProcessedDocument

logger = logging.getLogger(__name__)


async def send_document(document: ProcessedDocument) -> None:
    url = f"{settings.focus_service_url}/api/knowledge-base/documents"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=document.model_dump(),
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        response.raise_for_status()
        logger.info(f"Sent document {document.filename} to focus-service")


async def delete_document(article_id: int) -> None:
    url = f"{settings.focus_service_url}/api/knowledge-base/documents/{article_id}"

    async with httpx.AsyncClient() as client:
        response = await client.delete(url, timeout=30)
        response.raise_for_status()
        logger.info(f"Deleted document zendesk-{article_id} from focus-service")

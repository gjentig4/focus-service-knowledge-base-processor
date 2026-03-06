import hashlib
import hmac
import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from src.config import settings
from src.models.webhook import ZendeskWebhookPayload
from src.pipeline.orchestrator import process_article, delete_article

logger = logging.getLogger(__name__)

router = APIRouter()


def verify_zendesk_signature(payload: bytes, signature: str | None) -> bool:
    if not settings.zendesk_webhook_secret:
        return True  # Skip verification in dev if no secret configured
    if not signature:
        return False
    expected = hmac.new(
        settings.zendesk_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/zendesk", status_code=202)
async def zendesk_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_zendesk_webhook_signature: str | None = Header(None),
):
    body = await request.body()

    if not verify_zendesk_signature(body, x_zendesk_webhook_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = ZendeskWebhookPayload.model_validate_json(body)

    logger.info(f"Received webhook: {payload.type} for article {payload.article_id}")

    if payload.type == "article.published":
        background_tasks.add_task(process_article, payload.article_id)
    elif payload.type == "article.unpublished":
        background_tasks.add_task(delete_article, payload.article_id)
    else:
        logger.warning(f"Unknown webhook type: {payload.type}")

    return {"status": "accepted"}

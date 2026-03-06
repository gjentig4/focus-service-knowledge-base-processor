import logging

from src.pipeline.zendesk_client import fetch_article
from src.pipeline.html_to_markdown import convert_html_to_markdown
from src.pipeline.image_processor import process_images
from src.pipeline.enrichment import enrich_document
from src.pipeline.document_builder import build_document
from src.clients.focus_service import send_document, delete_document
from src.store.image_dedup import ImageDedupStore

logger = logging.getLogger(__name__)


async def process_article(article_id: int) -> None:
    try:
        logger.info(f"Processing article {article_id}")

        # 1. Fetch from Zendesk
        article = await fetch_article(article_id)
        logger.info(f"Fetched: {article.title}")

        # 2. Convert HTML to markdown
        markdown = convert_html_to_markdown(article.body)

        # 3. Process images (dedup + alt text)
        dedup_store = ImageDedupStore()
        markdown = await process_images(markdown, dedup_store)

        # 4. Enrich via LLM
        enrichment = await enrich_document(markdown, article.title)

        # 5. Build final document
        document = build_document(article, markdown, enrichment)

        # 6. Send to focus-service
        await send_document(document)

        logger.info(f"Successfully processed article {article_id}: {article.title}")
    except Exception as e:
        logger.error(f"Failed to process article {article_id}: {e}", exc_info=True)
        raise


async def delete_article(article_id: int) -> None:
    try:
        logger.info(f"Deleting article {article_id}")
        await delete_document(article_id)
        logger.info(f"Successfully deleted article {article_id}")
    except Exception as e:
        logger.error(f"Failed to delete article {article_id}: {e}", exc_info=True)
        raise

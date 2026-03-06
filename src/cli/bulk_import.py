import asyncio
import logging
import sys

from src.pipeline.zendesk_client import fetch_all_articles
from src.pipeline.html_to_markdown import convert_html_to_markdown
from src.pipeline.image_processor import process_images
from src.pipeline.enrichment import enrich_document
from src.pipeline.document_builder import build_document
from src.clients.focus_service import send_document
from src.store.image_dedup import ImageDedupStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def bulk_import():
    logger.info("Starting bulk import from Zendesk...")

    articles = await fetch_all_articles()
    logger.info(f"Found {len(articles)} articles to process")

    dedup_store = ImageDedupStore()
    success = 0
    failed = 0

    for i, article in enumerate(articles, 1):
        try:
            logger.info(f"[{i}/{len(articles)}] Processing: {article.title}")

            markdown = convert_html_to_markdown(article.body)
            markdown = await process_images(markdown, dedup_store)
            enrichment = await enrich_document(markdown, article.title)
            document = build_document(article, markdown, enrichment)
            await send_document(document)

            success += 1
            logger.info(f"[{i}/{len(articles)}] Done: {article.title}")
        except Exception as e:
            failed += 1
            logger.error(f"[{i}/{len(articles)}] Failed: {article.title} - {e}")

    logger.info(f"Bulk import complete: {success} succeeded, {failed} failed out of {len(articles)}")


def main():
    asyncio.run(bulk_import())


if __name__ == "__main__":
    main()

import logging

import httpx

from src.config import settings
from src.models.article import ZendeskArticle

logger = logging.getLogger(__name__)

BASE_URL = f"https://{settings.zendesk_subdomain}.zendesk.com"


def _auth() -> tuple[str, str]:
    return (f"{settings.zendesk_api_email}/token", settings.zendesk_api_token)


async def fetch_article(article_id: int) -> ZendeskArticle:
    url = f"{BASE_URL}/api/v2/help_center/en-150/articles/{article_id}.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, auth=_auth())
        response.raise_for_status()
        data = response.json()["article"]
        return ZendeskArticle.model_validate(data)


async def fetch_all_articles() -> list[ZendeskArticle]:
    articles: list[ZendeskArticle] = []
    url = f"{BASE_URL}/api/v2/help_center/en-150/articles.json?per_page=100"

    async with httpx.AsyncClient() as client:
        while url:
            response = await client.get(url, auth=_auth())
            response.raise_for_status()
            data = response.json()
            for article_data in data["articles"]:
                articles.append(ZendeskArticle.model_validate(article_data))
            url = data.get("next_page")
            logger.info(f"Fetched {len(articles)} articles so far...")

    logger.info(f"Total articles fetched: {len(articles)}")
    return articles

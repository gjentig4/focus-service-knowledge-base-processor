import io
import logging
import re

import httpx
from PIL import Image
import imagehash

from src.store.image_dedup import ImageDedupStore
from src.clients.openrouter import generate_alt_text

logger = logging.getLogger(__name__)


def extract_image_urls(markdown: str) -> list[str]:
    return re.findall(r"!\[.*?\]\((https?://[^\)]+)\)", markdown)


async def download_image(url: str) -> Image.Image | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30, follow_redirects=True)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
    except Exception as e:
        logger.warning(f"Failed to download image {url}: {e}")
        return None


def compute_phash(image: Image.Image) -> str:
    return str(imagehash.phash(image))


async def process_images(markdown: str, dedup_store: ImageDedupStore) -> str:
    image_urls = extract_image_urls(markdown)
    if not image_urls:
        return markdown

    for url in image_urls:
        image = await download_image(url)
        if not image:
            continue

        phash = compute_phash(image)

        # Check for duplicate
        existing = dedup_store.find_by_hash(phash)
        if existing and existing["alt_text"]:
            alt_text = existing["alt_text"]
            logger.debug(f"Reusing alt text for duplicate image: {url}")
        else:
            alt_text = await generate_alt_text(url)
            dedup_store.store(phash, url, alt_text)

        # Replace in markdown - update alt text
        markdown = markdown.replace(
            f"![]({url})",
            f"![{alt_text}]({url})",
        )

    return markdown

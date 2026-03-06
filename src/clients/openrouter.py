import logging

from openai import AsyncOpenAI

from src.config import settings

logger = logging.getLogger(__name__)

MODEL = "google/gemini-2.0-flash-001"


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )


async def generate_alt_text(image_url: str) -> str:
    client = _get_client()
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this image in one concise sentence for use as alt text. Focus on what the image shows in the context of a software help article.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                }
            ],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Alt text generation failed for {image_url}: {e}")
        return "Image"


async def generate_enrichment(prompt: str) -> str:
    client = _get_client()
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()

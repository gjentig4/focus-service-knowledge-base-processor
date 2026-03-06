import json
import logging

from src.clients.openrouter import generate_enrichment

logger = logging.getLogger(__name__)

ENRICHMENT_PROMPT = """Analyze the following Zendesk support article and provide structured metadata.

Article:
{content}

Respond with a JSON object containing:
- "summary": A 1-2 sentence summary of what the article covers
- "keywords": An array of 5-10 relevant keywords
- "doc_type": One of: "how-to", "troubleshooting", "reference", "conceptual", "faq"
- "quality": One of: "high", "medium", "low" - based on completeness and clarity
- "relevance_status": One of: "current", "review-needed", "outdated"
- "question_variations": An array of 3-5 different ways a user might ask about this topic
- "user_intent": A brief description of the typical user intent when seeking this article

Respond ONLY with valid JSON, no markdown code blocks."""


async def enrich_document(content: str, title: str) -> dict:
    prompt = ENRICHMENT_PROMPT.format(content=f"# {title}\n\n{content}")

    try:
        response = await generate_enrichment(prompt)
        metadata = json.loads(response)
        return metadata
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Enrichment failed for '{title}': {e}")
        return {
            "summary": "",
            "keywords": [],
            "doc_type": "reference",
            "quality": "medium",
            "relevance_status": "review-needed",
            "question_variations": [],
            "user_intent": "",
        }

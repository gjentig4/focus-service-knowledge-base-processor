from src.models.article import ZendeskArticle
from src.models.processed_document import ProcessedDocument


def build_document(
    article: ZendeskArticle,
    markdown_content: str,
    enrichment: dict,
) -> ProcessedDocument:
    # Build frontmatter-style content with metadata header
    frontmatter_parts = [
        f"# {article.title}",
    ]

    if enrichment.get("summary"):
        frontmatter_parts.append(f"Summary: {enrichment['summary']}")

    if enrichment.get("keywords"):
        frontmatter_parts.append(f"Keywords: {', '.join(enrichment['keywords'])}")

    frontmatter_parts.append(markdown_content)

    content = "\n\n".join(frontmatter_parts)

    return ProcessedDocument(
        filename=f"zendesk-{article.id}",
        article_id=article.id,
        title=article.title,
        url=article.html_url,
        locale=article.locale,
        content=content,
        metadata={
            "source": "zendesk",
            "article_id": article.id,
            "section_id": article.section_id,
            "label_names": article.label_names,
            "summary": enrichment.get("summary", ""),
            "keywords": enrichment.get("keywords", []),
            "doc_type": enrichment.get("doc_type", "reference"),
            "quality": enrichment.get("quality", "medium"),
            "relevance_status": enrichment.get("relevance_status", "review-needed"),
            "question_variations": enrichment.get("question_variations", []),
            "user_intent": enrichment.get("user_intent", ""),
            "updated_at": article.updated_at,
        },
    )

from pydantic import BaseModel


class ZendeskWebhookPayload(BaseModel):
    type: str  # "article.published" or "article.unpublished"
    article_id: int

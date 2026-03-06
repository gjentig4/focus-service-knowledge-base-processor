from pydantic import BaseModel


class ProcessedDocument(BaseModel):
    filename: str
    article_id: int
    title: str
    url: str
    locale: str
    content: str
    metadata: dict

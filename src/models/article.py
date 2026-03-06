from pydantic import BaseModel


class ZendeskArticle(BaseModel):
    id: int
    title: str
    body: str
    html_url: str
    locale: str
    section_id: int | None = None
    label_names: list[str] = []
    draft: bool = False
    promoted: bool = False
    outdated: bool = False
    created_at: str | None = None
    updated_at: str | None = None

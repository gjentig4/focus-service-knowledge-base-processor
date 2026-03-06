import re

from markdownify import markdownify


def convert_html_to_markdown(html: str) -> str:
    if not html:
        return ""

    markdown = markdownify(html, heading_style="ATX", strip=["script", "style"])

    # Clean up excessive whitespace
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = markdown.strip()

    return markdown

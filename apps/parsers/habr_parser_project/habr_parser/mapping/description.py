"""HTML description -> plain text that fits the contract."""

from __future__ import annotations

from bs4 import BeautifulSoup

_BLOCK_TAGS = ("p", "div", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6")
_ELLIPSIS = "…"


def html_to_text(html: str) -> str:
    """Plain text: one line per block or list item, list items prefixed with a bullet."""
    soup = BeautifulSoup(html, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for item in soup.find_all("li"):
        item.insert(0, "• ")
        item.append("\n")
    for block in soup.find_all(_BLOCK_TAGS):
        block.append("\n")

    lines = (line.strip() for line in soup.get_text().replace("\xa0", " ").splitlines())
    return "\n".join(line for line in lines if line)


def truncate_text(text: str, limit: int) -> str:
    """Cut at a word boundary so that the result, ellipsis included, is <= limit."""
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    boundary = max(cut.rfind(" "), cut.rfind("\n"))
    if boundary > limit // 2:
        cut = cut[:boundary]
    return cut.rstrip() + _ELLIPSIS

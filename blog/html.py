"""Utility helpers for sanitising rich text content."""

from __future__ import annotations

import bleach

ALLOWED_TAGS: list[str] = [
    "a",
    "abbr",
    "blockquote",
    "br",
    "code",
    "em",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "ul",
]

ALLOWED_ATTRIBUTES: dict[str, list[str] | dict[str, list[str]]] = {
    "a": ["href", "title", "target", "rel"],
    "abbr": ["title"],
}

ALLOWED_PROTOCOLS: list[str] = ["http", "https", "mailto"]


def sanitize_post_html(value: str) -> str:
    """Return HTML that is safe to render in the browser."""

    return bleach.clean(
        value or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


def extract_text(value: str) -> str:
    """Return plain text from HTML content for summaries and word counts."""

    return bleach.clean(value or "", tags=[], strip=True)

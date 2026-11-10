from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from tools._shared import err, fold_text


def _normalized_url(value: str) -> str:
    """Normalize harmless URL differences for duplicate detection."""
    parts = urlsplit(value.strip())
    if not parts.scheme or not parts.netloc:
        return value.strip().rstrip("/").lower()
    host = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/")
    # Query parameters and fragments often track clicks rather than identify content.
    return urlunsplit((parts.scheme.lower(), host, path, "", "")).lower()


def _normalized_title(value: str) -> str:
    return re.sub(r"\s+", " ", fold_text(value)).strip()


def deduplicate(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Keep the first item for each URL or title and report removed duplicates."""
    try:
        if items is None:
            items = []
        if not isinstance(items, list):
            raise TypeError("items must be a list of objects")

        unique: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise TypeError(f"items[{index}] must be an object")
            url = item.get("url", "")
            title = item.get("title", "")
            if not isinstance(url, str) or not isinstance(title, str):
                raise TypeError(f"items[{index}].url and title must be strings")

            normalized_url = _normalized_url(url) if url.strip() else ""
            normalized_title = _normalized_title(title) if title.strip() else ""
            duplicate = (normalized_url and normalized_url in seen_urls) or (
                normalized_title and normalized_title in seen_titles
            )
            if duplicate:
                continue
            unique.append(item)
            if normalized_url:
                seen_urls.add(normalized_url)
            if normalized_title:
                seen_titles.add(normalized_title)

        return {
            "tool": "deduplicate",
            "items": unique,
            "item_count": len(unique),
            "removed_count": len(items) - len(unique),
        }
    except Exception as exc:
        return err("deduplicate", exc)

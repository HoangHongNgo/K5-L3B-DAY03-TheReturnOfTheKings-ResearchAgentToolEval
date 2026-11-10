from __future__ import annotations

import os
import re
from typing import Any

import requests

from tools._shared import TIMEOUT, err, fold_text, terms


def _search_query(reference_text: str, max_terms: int = 8) -> str:
    """Build a compact, deterministic query from the reference post."""
    meaningful = terms(reference_text)
    ordered: list[str] = []
    for token in re.findall(r"[a-z0-9]+", fold_text(reference_text)):
        if token in meaningful and token not in ordered:
            ordered.append(token)
        if len(ordered) >= max_terms:
            break
    return " ".join(ordered)


def _tweet_item(raw: dict[str, Any], reference_terms: set[str]) -> dict[str, Any] | None:
    handle = raw.get("screen_name") or (raw.get("author") or {}).get("screen_name") or ""
    tweet_id = raw.get("tweet_id") or raw.get("id") or ""
    text = (raw.get("text") or "").strip()
    if not tweet_id or not text:
        return None

    candidate_terms = terms(text)
    union = reference_terms | candidate_terms
    score = len(reference_terms & candidate_terms) / len(union) if union else 0.0
    if score <= 0:
        return None

    return {
        "title": text.split("\n")[0][:120],
        "summary": text,
        "url": f"https://x.com/{handle}/status/{tweet_id}" if handle and tweet_id else "",
        "source": f"@{handle}" if handle else "x.com",
        "date": raw.get("created_at"),
        "metrics": {
            "favorites": raw.get("favorites"),
            "retweets": raw.get("retweets"),
            "views": raw.get("views"),
        },
        "similarity_score": round(score, 4),
    }


def find_similar_posts(
    reference_text: str = "",
    search_type: str = "Top",
    limit: int = 5,
) -> dict[str, Any]:
    """Search X and rank candidate posts by Jaccard term similarity."""
    try:
        if not isinstance(reference_text, str) or not reference_text.strip():
            raise ValueError("reference_text must be a non-empty string")
        if search_type not in {"Top", "Latest"}:
            raise ValueError("search_type must be 'Top' or 'Latest'")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
            raise ValueError("limit must be an integer from 1 to 20")

        reference_text = reference_text.strip()
        reference_terms = terms(reference_text)
        query = _search_query(reference_text)
        if not query or not reference_terms:
            raise ValueError("reference_text must contain searchable words")

        key = os.getenv("RAPIDAPI_KEY")
        host = os.getenv("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")
        if not key:
            raise RuntimeError("Missing RAPIDAPI_KEY env var")

        response = requests.get(
            f"https://{host}/search.php",
            params={"query": query, "search_type": search_type},
            headers={"x-rapidapi-key": key, "x-rapidapi-host": host},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        raw_items = data.get("timeline") or data.get("tweets") or []
        normalized_reference = " ".join(fold_text(reference_text).split())
        items = []
        for raw in raw_items:
            candidate_text = (raw.get("text") or "").strip()
            if " ".join(fold_text(candidate_text).split()) == normalized_reference:
                continue
            item = _tweet_item(raw, reference_terms)
            if item is not None:
                items.append(item)

        items.sort(key=lambda item: item["similarity_score"], reverse=True)
        return {
            "tool": "similar_posts",
            "reference_text": reference_text,
            "query": query,
            "search_type": search_type,
            "items": items[:limit],
        }
    except Exception as exc:
        return err("similar_posts", exc)

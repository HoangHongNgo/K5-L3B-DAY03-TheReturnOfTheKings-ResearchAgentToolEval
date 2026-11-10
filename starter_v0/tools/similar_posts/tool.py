from __future__ import annotations

import os
import re
from collections import Counter
from typing import Any

import requests

from tools._shared import TIMEOUT, err, fold_text, terms


MIN_SIMILARITY = 0.15
QUERY_STOPWORDS = {
    "find", "he", "https", "it", "just", "like", "new", "our", "post", "posts", "rt",
    "she", "similar", "that", "their", "these", "they", "thing", "things", "this", "those",
    "today", "use", "used", "using", "we", "with", "you", "your",
}


def _term_sequence(text: str) -> list[str]:
    """Return meaningful terms in source order for phrase comparison."""
    meaningful = terms(text)
    return [
        token
        for token in re.findall(r"[a-z0-9]+", fold_text(text))
        if token in meaningful
    ]


def _bigrams(sequence: list[str]) -> set[tuple[str, str]]:
    return set(zip(sequence, sequence[1:]))


def _similarity(reference_text: str, candidate_text: str) -> dict[str, float]:
    """Blend topic coverage, overall overlap, and matching word pairs."""
    reference_sequence = _term_sequence(reference_text)
    candidate_sequence = _term_sequence(candidate_text)
    reference_terms = set(reference_sequence)
    candidate_terms = set(candidate_sequence)
    shared_terms = reference_terms & candidate_terms
    union = reference_terms | candidate_terms

    coverage = len(shared_terms) / len(reference_terms) if reference_terms else 0.0
    jaccard = len(shared_terms) / len(union) if union else 0.0
    reference_bigrams = _bigrams(reference_sequence)
    phrase_overlap = (
        len(reference_bigrams & _bigrams(candidate_sequence)) / len(reference_bigrams)
        if reference_bigrams else 0.0
    )
    score = 0.45 * coverage + 0.35 * jaccard + 0.20 * phrase_overlap
    return {
        "coverage": round(coverage, 4),
        "jaccard": round(jaccard, 4),
        "phrase_overlap": round(phrase_overlap, 4),
        "score": round(score, 4),
    }


def _search_query(reference_text: str, max_terms: int = 8) -> str:
    """Build a compact, deterministic query from the reference post."""
    meaningful = terms(reference_text)
    ordered: list[str] = []
    for token in re.findall(r"[a-z0-9]+", fold_text(reference_text)):
        if token in meaningful and token not in QUERY_STOPWORDS and token not in ordered:
            ordered.append(token)
        if len(ordered) >= max_terms:
            break
    return " ".join(ordered)


def _profile_query(posts: list[str], max_terms: int = 8) -> str:
    """Favor terms that recur across a user's recent posts."""
    counts: Counter[str] = Counter()
    first_seen: dict[str, int] = {}
    position = 0
    for post in posts:
        seen_in_post: set[str] = set()
        for token in _term_sequence(post):
            if token in QUERY_STOPWORDS or token in seen_in_post:
                continue
            seen_in_post.add(token)
            counts[token] += 1
            if token not in first_seen:
                first_seen[token] = position
                position += 1
    ranked = sorted(counts, key=lambda token: (-counts[token], first_seen[token]))
    return " ".join(ranked[:max_terms])


def _twitter_get(path: str, params: dict[str, Any], key: str, host: str) -> dict[str, Any]:
    response = requests.get(
        f"https://{host}{path}",
        params=params,
        headers={"x-rapidapi-key": key, "x-rapidapi-host": host},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _tweet_item(raw: dict[str, Any], reference_text: str) -> dict[str, Any] | None:
    handle = raw.get("screen_name") or (raw.get("author") or {}).get("screen_name") or ""
    tweet_id = raw.get("tweet_id") or raw.get("id") or ""
    text = (raw.get("text") or "").strip()
    if not tweet_id or not text:
        return None

    similarity = _similarity(reference_text, text)
    if similarity["score"] < MIN_SIMILARITY:
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
        "similarity_score": similarity["score"],
        "similarity_components": {
            "coverage": similarity["coverage"],
            "jaccard": similarity["jaccard"],
            "phrase_overlap": similarity["phrase_overlap"],
        },
    }


def find_similar_posts(
    reference_text: str = "",
    reference_screenname: str = "",
    search_type: str = "Top",
    limit: int = 5,
    timeline_limit: int = 10,
) -> dict[str, Any]:
    """Search X and rank posts against reference text or a user's recent posts."""
    try:
        if not isinstance(reference_text, str) or not isinstance(reference_screenname, str):
            raise ValueError("reference_text and reference_screenname must be strings")
        reference_text = reference_text.strip()
        reference_screenname = reference_screenname.strip().lstrip("@")
        if bool(reference_text) == bool(reference_screenname):
            raise ValueError("provide exactly one of reference_text or reference_screenname")
        if reference_screenname and not re.fullmatch(r"[A-Za-z0-9_]{1,15}", reference_screenname):
            raise ValueError("reference_screenname must be a valid X handle without spaces")
        if search_type not in {"Top", "Latest"}:
            raise ValueError("search_type must be 'Top' or 'Latest'")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
            raise ValueError("limit must be an integer from 1 to 20")
        if isinstance(timeline_limit, bool) or not isinstance(timeline_limit, int) or not 1 <= timeline_limit <= 20:
            raise ValueError("timeline_limit must be an integer from 1 to 20")

        key = os.getenv("RAPIDAPI_KEY")
        host = os.getenv("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")
        if not key:
            raise RuntimeError("Missing RAPIDAPI_KEY env var")

        reference_mode = "text"
        reference_basis = reference_text
        reference_post_count = 0
        excluded_texts = {" ".join(fold_text(reference_text).split())} if reference_text else set()
        if reference_screenname:
            reference_mode = "user"
            timeline_data = _twitter_get(
                "/timeline.php", {"screenname": reference_screenname}, key, host,
            )
            timeline_items = timeline_data.get("timeline") or timeline_data.get("tweets") or []
            reference_posts = [
                (item.get("text") or "").strip()
                for item in timeline_items
                if (item.get("text") or "").strip()
            ][:timeline_limit]
            if not reference_posts:
                raise ValueError(f"no usable recent posts found for @{reference_screenname}")
            query = _profile_query(reference_posts)
            reference_basis = query
            reference_post_count = len(reference_posts)
            excluded_texts = {" ".join(fold_text(text).split()) for text in reference_posts}
        else:
            query = _search_query(reference_text)

        if not query or not terms(reference_basis):
            raise ValueError("reference must contain searchable words")

        data = _twitter_get(
            "/search.php", {"query": query, "search_type": search_type}, key, host,
        )

        raw_items = data.get("timeline") or data.get("tweets") or []
        items = []
        for raw in raw_items:
            handle = raw.get("screen_name") or (raw.get("author") or {}).get("screen_name") or ""
            if reference_screenname and handle.lower() == reference_screenname.lower():
                continue
            candidate_text = (raw.get("text") or "").strip()
            if " ".join(fold_text(candidate_text).split()) in excluded_texts:
                continue
            item = _tweet_item(raw, reference_basis)
            if item is not None:
                items.append(item)

        items.sort(key=lambda item: item["similarity_score"], reverse=True)
        return {
            "tool": "similar_posts",
            "reference_mode": reference_mode,
            "reference_text": reference_text if reference_mode == "text" else "",
            "reference_screenname": reference_screenname,
            "reference_post_count": reference_post_count,
            "query": query,
            "search_type": search_type,
            "minimum_similarity": MIN_SIMILARITY,
            "items": items[:limit],
        }
    except Exception as exc:
        return err("similar_posts", exc)

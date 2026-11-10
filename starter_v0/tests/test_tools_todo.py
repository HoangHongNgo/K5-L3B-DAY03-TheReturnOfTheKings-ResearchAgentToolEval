"""TODO CP3 (student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest
import requests

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO CP3 (student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    pytest.skip(TODO)


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    pytest.skip(TODO)


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    pytest.skip(TODO)


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    pytest.skip(TODO)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    pytest.skip(TODO)


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    pytest.skip(TODO)


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    pytest.skip(TODO)


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    pytest.skip(TODO)


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    pytest.skip(TODO)


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    pytest.skip(TODO)


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    pytest.skip(TODO)


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    pytest.skip(TODO)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    pytest.skip(TODO)


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

def test_similar_posts_ranks_candidates_and_sends_derived_query(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"timeline": [
        {
            "tweet_id": "1", "screen_name": "alice",
            "text": "AI agents use tools reliably with concise prompts",
        },
        {
            "tweet_id": "2", "screen_name": "bob",
            "text": "AI agents improve research models",
        },
        {
            "tweet_id": "3", "screen_name": "copy",
            "text": "AI agents use tools reliably",
        },
        {"screen_name": "missing_id", "text": "AI agents use tools"},
    ]}))

    result = TOOL_FUNCTIONS["similar_posts"](
        reference_text="AI agents use tools reliably", search_type="Top", limit=2,
    )

    assert calls[0]["url"] == "https://twitter-api45.p.rapidapi.com/search.php"
    assert calls[0]["params"] == {
        "query": "ai agents tools reliably", "search_type": "Top",
    }
    assert calls[0]["headers"]["x-rapidapi-key"] == "test-key"
    assert [item["source"] for item in result["items"]] == ["@alice", "@bob"]
    assert result["items"][0]["similarity_score"] > result["items"][1]["similarity_score"]
    assert result["items"][0]["similarity_components"]["coverage"] == 1.0
    assert result["minimum_similarity"] == 0.15


def test_similar_posts_filters_candidates_below_minimum_similarity(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    fake_http(FakeResponse({"timeline": [
        {"tweet_id": "1", "screen_name": "weak", "text": "AI recipes for home cooking"},
        {
            "tweet_id": "2", "screen_name": "strong",
            "text": "Language models call reliable tools with short prompts in production",
        },
    ]}))

    result = TOOL_FUNCTIONS["similar_posts"](
        reference_text="AI language models call tools reliably with concise prompts",
    )

    assert [item["source"] for item in result["items"]] == ["@strong"]


def test_similar_posts_builds_profile_from_user_with_two_requests(monkeypatch) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    responses = iter([
        FakeResponse({"timeline": [
            {"tweet_id": "r1", "screen_name": "source_user", "text": "AI agents call tools reliably"},
            {"tweet_id": "r2", "screen_name": "source_user", "text": "Reliable AI evaluation for agents"},
        ]}),
        FakeResponse({"timeline": [
            {"tweet_id": "self", "screen_name": "source_user", "text": "AI agents call tools"},
            {"tweet_id": "match", "screen_name": "other_user", "text": "Reliable AI agents need tool evaluation"},
            {"tweet_id": "weak", "screen_name": "cook", "text": "Pasta recipes for dinner"},
        ]}),
    ])
    calls = []

    def fake_get(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return next(responses)

    monkeypatch.setattr(requests, "get", fake_get)

    result = TOOL_FUNCTIONS["similar_posts"](
        reference_screenname="@source_user", timeline_limit=5, limit=3,
    )

    assert [call["url"] for call in calls] == [
        "https://twitter-api45.p.rapidapi.com/timeline.php",
        "https://twitter-api45.p.rapidapi.com/search.php",
    ]
    assert calls[0]["params"] == {"screenname": "source_user"}
    assert result["reference_mode"] == "user"
    assert result["reference_screenname"] == "source_user"
    assert result["reference_post_count"] == 2
    assert [item["source"] for item in result["items"]] == ["@other_user"]


def test_similar_posts_rejects_empty_reference_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse({"timeline": []}))

    result = TOOL_FUNCTIONS["similar_posts"](reference_text="   ")

    assert result["error"] == "ValueError"
    assert "reference_text" in result["message"]
    assert calls == []


def test_similar_posts_missing_key_returns_error_dict() -> None:
    result = TOOL_FUNCTIONS["similar_posts"](reference_text="AI agents use tools")

    assert result["error"] == "RuntimeError"
    assert "RAPIDAPI_KEY" in result["message"]

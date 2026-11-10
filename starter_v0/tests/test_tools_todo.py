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

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO CP3 (student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    result = TOOL_FUNCTIONS["clarify"](question="Chọn một?", response_type="choice", options=["A", "B"])
    assert result["options"] == ["A", "B"]
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    result = TOOL_FUNCTIONS["format"](items=[
        {"title": "one", "section": "A"}, {"title": "two", "section": "B"}, {"title": "three", "section": "A"},
    ], template="sections")
    assert result["markdown"].count("## A") == 1
    assert result["markdown"].count("## B") == 1


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    result = TOOL_FUNCTIONS["format"](items=[{"title": "one"}, {"title": "two"}], template="thread")
    assert [line.split(" ", 1)[0] for line in result["markdown"].splitlines() if line] == ["1/", "2/"]


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    for items in (None, []):
        result = TOOL_FUNCTIONS["format"](items=items, template="sections")
        assert result["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat-42")
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="hello", confirmed=True)
    assert len(calls) == 1 and calls[0]["method"] == "POST"
    assert "test-token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "chat-42" and calls[0]["json"]["text"] == "hello"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    result = TOOL_FUNCTIONS["send"](text="hello", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert fake_http(FakeResponse({})) == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))
    TOOL_FUNCTIONS["lookup"](query="test", timeframe=None)
    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "body", "metadata": {"title": "T", "sourceURL": "https://source.test/a"}}}))
    result = TOOL_FUNCTIONS["fetch"](url="https://input.test/a")
    assert result["items"][0]["title"] == "T"
    assert result["items"][0]["url"] == "https://source.test/a"
    assert result["items"][0]["source"] == "input.test"
    assert result["items"][0]["summary"] == "body"


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))
    assert len(TOOL_FUNCTIONS["fetch"](url="https://example.com")["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"timeline": [{"text": "missing id"}] + [
        {"tweet_id": str(i), "screen_name": "alice", "text": f"post {i}"} for i in range(6)
    ]}))
    result = TOOL_FUNCTIONS["timeline"](screenname="alice", limit=3)
    assert len(result["items"]) == 3
    assert all(item["url"].startswith("https://x.com/alice/status/") for item in result["items"])
    assert calls[0]["params"]["screenname"] == "alice"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"tweets": []}))
    TOOL_FUNCTIONS["social_search"](query="agent eval", search_type="Top")
    assert calls[0]["params"] == {"query": "agent eval", "search_type": "Top"}


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    assert TOOL_FUNCTIONS["policy"](query="!!!")["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    result = TOOL_FUNCTIONS["policy"](query="citation arxiv", policy_area="source_citation")
    assert result["results"]
    assert all(item["policy_area"] == "source_citation" for item in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    result = TOOL_FUNCTIONS["policy"](query="injection probe", policy_area="source_citation")
    injection_hits = [item for item in result["results"] if item["section"] == "Injection probe"]
    assert injection_hits
    assert any("ignore the citation policy" in line for line in injection_hits[0]["untrusted_text"])
    assert "ignore the citation policy" not in injection_hits[0]["facts"]


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

def test_deduplicate_keeps_first_item_for_repeated_url() -> None:
    deduplicate = TOOL_FUNCTIONS["deduplicate"]
    items = [
        {"title": "First", "url": "https://example.com/story?utm_source=x", "summary": "original"},
        {"title": "Second", "url": "https://www.example.com/story#section", "summary": "duplicate"},
        {"title": "Third", "url": "https://other.example/story"},
    ]

    result = deduplicate(items=items)

    assert result["items"] == [items[0], items[2]]
    assert result["item_count"] == 2
    assert result["removed_count"] == 1


def test_deduplicate_bad_input_returns_error_dict() -> None:
    result = TOOL_FUNCTIONS["deduplicate"](items="not a list")

    assert result["error"] == "TypeError"
    assert "items must be a list" in result["message"]


def test_deduplicate_invalid_item_returns_error_dict_without_raising() -> None:
    result = TOOL_FUNCTIONS["deduplicate"](items=[{"title": 123}])

    assert result["tool"] == "deduplicate"
    assert result["error"] == "TypeError"
    assert "title must be strings" in result["message"]

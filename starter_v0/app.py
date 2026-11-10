"""Streamlit chat UI for the same agent loop used by chat.py."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
VERSION = "v3"
PROVIDER = "openrouter"
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4


def new_session() -> dict:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = f"{safe_slug(VERSION)}_{safe_slug(PROVIDER)}_ui_{stamp}"
    version = build_artifact_version(VERSION, PROMPT_PATH, TOOLS_PATH)
    return {
        "transcript_id": transcript_id,
        **artifact_version_dict(version),
        "provider": PROVIDER,
        "model": "openai/gpt-4o-mini",
        "system_prompt": str(PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": HISTORY_WINDOW,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


st.set_page_config(page_title="Research Agent", page_icon="🔎")
st.title("🔎 Research Agent")
st.caption("Tìm và đọc nguồn, hỏi lại khi thiếu thông tin, xin xác nhận trước khi gửi.")

if "transcript" not in st.session_state:
    st.session_state.transcript = new_session()
    st.session_state.history = []

with st.sidebar:
    st.write(f"Provider: {PROVIDER} · Version: {VERSION}")
    st.write("Ví dụ: ‘Chính sách trích dẫn nguồn của công ty là gì?’")
    st.write("Ví dụ: ‘Tóm tắt bài viết này’ rồi cung cấp URL khi agent hỏi.")
    if st.button("Cuộc trò chuyện mới"):
        st.session_state.transcript = new_session()
        st.session_state.history = []
        st.rerun()

for turn in st.session_state.transcript["turns"]:
    with st.chat_message("user"):
        st.write(turn["user"])
    with st.chat_message("assistant"):
        if turn["status"] == "provider_error":
            st.error(turn.get("error", "Provider error"))
        else:
            st.write(turn.get("assistant_text") or "(Không có nội dung trả lời)")
        if turn.get("tool_events"):
            with st.expander("Tool calls và kết quả"):
                st.json(turn["tool_events"])

user_text = st.chat_input("Nhập yêu cầu nghiên cứu…")
if user_text:
    transcript = st.session_state.transcript
    turn = {
        "turn_index": len(transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    with st.spinner("Agent đang xử lý…"):
        try:
            messages = [
                {"role": "system", "content": PROMPT_PATH.read_text(encoding="utf-8")},
                *trim_history(st.session_state.history, HISTORY_WINDOW),
                {"role": "user", "content": user_text},
            ]
            result = run_model_tool_loop(
                provider=make_provider(PROVIDER),
                messages=messages,
                tools=to_openai_tools(load_tool_declarations(TOOLS_PATH)),
                model=None,
                max_tool_rounds=MAX_TOOL_ROUNDS,
            )
            turn.update(result)
            st.session_state.history.extend([
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": result["assistant_text"]},
            ])
        except Exception as exc:
            turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
    turn["ended_at"] = now_iso()
    transcript["turns"].append(turn)
    write_transcript(Path(ROOT) / "transcripts" / f"{transcript['transcript_id']}.transcript.json", transcript)
    st.rerun()

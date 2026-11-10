"""Streamlit demo comparing three configurations of the same research agent."""
from __future__ import annotations

from dataclasses import dataclass
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


PROVIDER = "openrouter"
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4


@dataclass(frozen=True)
class DemoVersion:
    key: str
    label: str
    description: str
    prompt_path: Path
    tools_path: Path


VERSIONS = (
    DemoVersion(
        key="v0",
        label="v0",
        description="Bản gốc: prompt và mô tả tool ban đầu.",
        prompt_path=ARTIFACTS_DIR / "replay_cp2" / "v0" / "system_prompt.md",
        tools_path=ARTIFACTS_DIR / "replay_cp2" / "v0" / "tools.yaml",
    ),
    DemoVersion(
        key="v3",
        label="v3",
        description="Prompt và mô tả tool đã được cải tiến; giữ nguyên 10 tool gốc.",
        prompt_path=ARTIFACTS_DIR / "replay_cp2" / "v3" / "system_prompt.md",
        tools_path=ARTIFACTS_DIR / "replay_cp2" / "v3" / "tools.yaml",
    ),
    DemoVersion(
        key="v3_with_added_tools",
        label="v3 with added tools",
        description="Cấu hình v3 hiện tại, bổ sung deduplicate và similar_posts.",
        prompt_path=ARTIFACTS_DIR / "system_prompt.md",
        tools_path=ARTIFACTS_DIR / "tools.yaml",
    ),
)


def new_session(config: DemoVersion) -> dict:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = f"{safe_slug(config.key)}_{safe_slug(PROVIDER)}_ui_{stamp}"
    version = build_artifact_version(config.key, config.prompt_path, config.tools_path)
    return {
        "transcript_id": transcript_id,
        **artifact_version_dict(version),
        "provider": PROVIDER,
        "model": "openai/gpt-4o-mini",
        "system_prompt": str(config.prompt_path),
        "tools": str(config.tools_path),
        "history_window": HISTORY_WINDOW,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def render_tab(config: DemoVersion) -> None:
    state_key = f"demo_{config.key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = {"transcript": new_session(config), "history": []}
    session = st.session_state[state_key]

    st.caption(config.description)
    declarations = load_tool_declarations(config.tools_path)
    with st.expander(f"Cấu hình: {len(declarations)} tools"):
        st.write(", ".join(item["name"] for item in declarations))
        st.code(session["transcript"]["artifact_version"])

    if st.button("Cuộc trò chuyện mới", key=f"reset_{config.key}"):
        st.session_state[state_key] = {"transcript": new_session(config), "history": []}
        st.rerun()

    for turn in session["transcript"]["turns"]:
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

    user_text = st.chat_input("Nhập yêu cầu nghiên cứu…", key=f"input_{config.key}")
    if not user_text:
        return

    transcript = session["transcript"]
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
                {"role": "system", "content": config.prompt_path.read_text(encoding="utf-8")},
                *trim_history(session["history"], HISTORY_WINDOW),
                {"role": "user", "content": user_text},
            ]
            result = run_model_tool_loop(
                provider=make_provider(PROVIDER),
                messages=messages,
                tools=to_openai_tools(declarations),
                model=None,
                max_tool_rounds=MAX_TOOL_ROUNDS,
            )
            turn.update(result)
            session["history"].extend([
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": result["assistant_text"]},
            ])
        except Exception as exc:
            turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
    turn["ended_at"] = now_iso()
    transcript["turns"].append(turn)
    write_transcript(Path(ROOT) / "transcripts" / f"{transcript['transcript_id']}.transcript.json", transcript)
    st.rerun()


st.set_page_config(page_title="Research Agent", page_icon="🔎")
st.title("🔎 Research Agent")
st.caption("Thử cùng một câu hỏi ở từng phiên bản để so sánh prompt, tool và kết quả.")

with st.sidebar:
    st.write(f"Provider: {PROVIDER}")
    st.write("Ví dụ: ‘Chính sách trích dẫn nguồn của công ty là gì?’")
    st.write("Ví dụ: ‘Tìm các bài đăng tương tự bài này: ...’")

for tab, config in zip(st.tabs([version.label for version in VERSIONS]), VERSIONS):
    with tab:
        render_tab(config)

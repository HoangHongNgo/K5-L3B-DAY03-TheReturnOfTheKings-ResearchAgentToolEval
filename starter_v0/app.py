"""Streamlit demo comparing research agent versions and their evaluations."""
from __future__ import annotations

import json
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
METRICS_PATH = ROOT / "data" / "demo_metrics.json"


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
        key="v1",
        label="v1",
        description="Cải tiến prompt: hỏi lại khi thiếu thông tin và xin xác nhận trước khi gửi.",
        prompt_path=ARTIFACTS_DIR / "replay_cp2" / "v1" / "system_prompt.md",
        tools_path=ARTIFACTS_DIR / "replay_cp2" / "v1" / "tools.yaml",
    ),
    DemoVersion(
        key="v2",
        label="v2",
        description="Cải tiến prompt: quy định rõ response_type khi hỏi lại hoặc xin xác nhận.",
        prompt_path=ARTIFACTS_DIR / "replay_cp2" / "v2" / "system_prompt.md",
        tools_path=ARTIFACTS_DIR / "replay_cp2" / "v2" / "tools.yaml",
    ),
    DemoVersion(
        key="v3",
        label="v3",
        description="Prompt và mô tả tool đã được cải tiến; giữ nguyên 10 tool gốc.",
        prompt_path=ARTIFACTS_DIR / "replay_cp2" / "v3" / "system_prompt.md",
        tools_path=ARTIFACTS_DIR / "replay_cp2" / "v3" / "tools.yaml",
    ),
    DemoVersion(
        key="v4",
        label="v4 with added tools",
        description="Prompt v4 xử lý yêu cầu bỏ nguồn ở hội thoại nhiều lượt; bổ sung deduplicate và similar_posts.",
        prompt_path=ARTIFACTS_DIR / "replay_cp2" / "v4" / "system_prompt.md",
        tools_path=ARTIFACTS_DIR / "replay_cp2" / "v4" / "tools.yaml",
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


def render_metrics_tab() -> None:
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    versions = metrics["versions"]
    first, last = versions[0], versions[-1]

    st.subheader("Thay đổi và kết quả qua các phiên bản")
    st.caption("Số liệu tĩnh từ các run OpenRouter; tab này không gọi model hay tool.")
    col_base, col_gain, col_group = st.columns(3)
    col_base.metric("Case cũ đúng ở v4", f"{last['base_passed']}/{metrics['base_cases']}")
    col_gain.metric("Tăng từ v0 đến v4", f"+{last['base_passed'] - first['base_passed']} case")
    col_group.metric("Case mới đúng ở v4", f"{last['group_passed']}/{metrics['group_cases']}")

    st.markdown("#### Bộ case cũ · 20 case")
    base_rows = [
        "| Phiên bản | Thay đổi | Tools | Case đúng | Routing | Tham số | Nhiều lượt |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for item in versions:
        base_rows.append(
            f"| {item['key']} | {item['change']} | {item['tools']} | "
            f"{item['base_passed']}/{metrics['base_cases']} "
            f"({item['base_passed'] / metrics['base_cases']:.0%}) | "
            f"{item['base_routing']:.0%} | {item['base_arguments']:.0%} | "
            f"{item['base_multiturn']:.0%} |"
        )
    st.markdown("\n".join(base_rows))
    st.caption("Run v4 base đo đủ 20 case, không có lỗi provider và đạt 19/20; lỗi còn lại là response_type ở boundary xác nhận gửi.")

    st.markdown("#### Bộ case mới · 10 case")
    st.write(f"{metrics['group_single_turn_cases']} case một lượt · {metrics['group_multi_turn_cases']} case nhiều lượt")
    group_rows = [
        "| Phiên bản | Tool sẵn có | Case đúng | Routing | Tham số | Nhiều lượt |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in versions:
        group_rows.append(
            f"| {item['key']} | {item['group_tool_coverage']}/{metrics['group_cases']} | "
            f"{item['group_passed']}/{metrics['group_cases']} | {item['group_routing']:.0%} | "
            f"{item['group_arguments']:.0%} | {item['group_multiturn']:.0%} |"
        )
    st.markdown("\n".join(group_rows))
    st.info(metrics["group_result_note"])
    st.caption("4/10 case kiểm tra similar_posts và 4/10 kiểm tra deduplicate ở mức dễ và nhiều lượt; 2 case còn lại kiểm tra no-tool và confirmation boundary.")

    with st.expander("Nguồn số liệu"):
        st.write(f"Case cũ: {metrics['base_dataset']} · Case mới: {metrics['group_dataset']}")
        st.write(f"Provider/model: {metrics['provider']} / {metrics['model']}")
        for item in versions:
            st.code(f"{item['key']}: {item['base_run']}")
            st.code(f"{item['key']} (case mới): {item['group_run']}")
        st.caption("Run JSON gốc được giữ trong workspace; chỉ số tổng hợp được đưa lên website.")


st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")
st.title("🔎 Research Agent")
st.caption("Thử cùng một câu hỏi ở từng phiên bản để so sánh prompt, tool và kết quả.")

with st.sidebar:
    st.write(f"Provider: {PROVIDER}")
    st.write("Ví dụ: ‘Chính sách trích dẫn nguồn của công ty là gì?’")
    st.write("Ví dụ: ‘Tìm các bài đăng tương tự bài này: ...’")

tabs = st.tabs([version.label for version in VERSIONS] + ["Thống kê phiên bản"])
for tab, config in zip(tabs, VERSIONS):
    with tab:
        render_tab(config)

with tabs[-1]:
    render_metrics_tab()

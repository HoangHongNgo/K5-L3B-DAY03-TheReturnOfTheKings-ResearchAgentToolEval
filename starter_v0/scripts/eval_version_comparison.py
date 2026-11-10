"""Score group-case routing for each saved version without executing tools."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers import make_provider  # noqa: E402
from run_eval import case_messages, evaluate_phase_b, load_cases, summarize  # noqa: E402
from tools import load_tool_declarations, to_openai_tools  # noqa: E402
from versioning import artifact_version_dict, build_artifact_version  # noqa: E402


def main() -> None:
    cases = load_cases(ROOT / "data/eval_group.json", "B")
    provider = make_provider("openrouter")
    for version in ("v0", "v1", "v2", "v3", "v4"):
        snapshot = ROOT / "artifacts/replay_cp2" / version
        prompt_path = snapshot / "system_prompt.md"
        tools_path = snapshot / "tools.yaml"
        prompt = prompt_path.read_text(encoding="utf-8")
        tools = to_openai_tools(load_tool_declarations(tools_path))
        results = []
        for case in cases:
            print(f"{version}: {case['id']}", flush=True)
            try:
                response = provider.complete(
                    [{"role": "system", "content": prompt}, *case_messages(case)],
                    tools,
                    model=None,
                    temperature=0.0,
                    tool_choice=None if case["expect"].get("no_tool") else "required",
                )
                calls = [{"name": call.name, "args": call.args} for call in response.tool_calls]
                result = evaluate_phase_b(case, calls, response.text)
            except Exception as exc:
                result = {
                    "passed": False, "failure_type": "provider_error",
                    "observed_mismatch": "provider_error",
                    "failures": [f"{type(exc).__name__}: {exc}"],
                    "actual_tool_calls": [], "routing_correct": False, "args_correct": False,
                }
            results.append({"id": case["id"], "phase": "B", "is_multiturn": "turns" in case, "result": result})
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        artifact = build_artifact_version(version, prompt_path, tools_path)
        payload = {
            "run_id": f"{version}_B_group_openrouter_routing_{stamp}",
            "version": version, **artifact_version_dict(artifact),
            "suite": "group", "provider": "openrouter", "model": provider.default_model,
            "evaluation_mode": "routing_only_no_tool_execution",
            "dataset_id": "day03_v2_research_group", "generated_at": datetime.now().isoformat(timespec="seconds"),
            "summary": summarize(results), "results": results,
        }
        path = ROOT / "runs" / f"{payload['run_id']}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{version}: {payload['summary']['passed_cases']}/{payload['summary']['measured_cases']} -> {path}", flush=True)


if __name__ == "__main__":
    main()

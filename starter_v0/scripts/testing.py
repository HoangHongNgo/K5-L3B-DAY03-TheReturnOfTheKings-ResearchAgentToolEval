from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from tools import TOOL_FUNCTIONS

load_lab_env(ROOT)

# Avoid Unicode display errors in Windows PowerShell.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

result = TOOL_FUNCTIONS["similar_posts"](
    reference_screenname="b1rdal",
    timeline_limit=5,
    search_type="Top",
    limit=3,
)

print(json.dumps(result, ensure_ascii=False, indent=2))

if "error" in result:
    raise SystemExit(f"Live test failed: {result['message']}")

print(f"\nReturned {len(result['items'])} similar posts")
for index, item in enumerate(result["items"], start=1):
    print(
        f"{index}. score={item['similarity_score']:.4f} "
        f"source={item['source']} url={item['url']}"
    )
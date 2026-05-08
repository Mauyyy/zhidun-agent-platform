from __future__ import annotations

import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.llm_client import generate_plain_reply  # noqa: E402


PROMPT = "请用一句话说明什么是大模型安全网关。"


def main() -> int:
    result = generate_plain_reply(PROMPT)
    if not result["ok"] and result["error"] == "缺少 OPENAI_API_KEY":
        print("未配置 OPENAI_API_KEY，跳过真实大模型调用。")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

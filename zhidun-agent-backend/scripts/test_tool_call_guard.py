"""Isolated tests for virtual tool_call guard.

This script does not call chat/messages, does not write events.json, and does
not execute real tools.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.tool_call_guard import audit_tool_call  # noqa: E402


SCENARIOS: list[dict[str, Any]] = [
    {
        "title": "安全工具：公开文档检索",
        "toolCall": {
            "name": "search_public_docs",
            "arguments": {"query": "校园网报修流程"},
        },
        "expectedDecision": "ALLOWED",
    },
    {
        "title": "自身资料读取",
        "toolCall": {
            "name": "read_user_profile",
            "arguments": {"resource": "self_profile"},
        },
        "expectedDecision": "ALLOWED",
    },
    {
        "title": "高敏系统文件",
        "toolCall": {
            "name": "read_system_file",
            "arguments": {"path": "/admin/db_credentials.txt"},
        },
        "expectedDecision": "BLOCKED",
    },
    {
        "title": "未注册工具",
        "toolCall": {
            "name": "dump_database",
            "arguments": {"table": "users"},
        },
        "expectedDecision": "BLOCKED",
    },
    {
        "title": "参数越界",
        "toolCall": {
            "name": "search_public_docs",
            "arguments": {"resource": "/admin/secret"},
        },
        "expectedDecision": "BLOCKED",
    },
]


def main() -> int:
    print("Function Calling 安全审计隔离验证")
    print("说明：不调用 chat/messages，不写 events.json，不执行真实工具。")

    failed: list[dict[str, Any]] = []
    for index, scenario in enumerate(SCENARIOS, start=1):
        result = audit_tool_call(scenario["toolCall"])
        expected = scenario["expectedDecision"]
        actual = result["decision"]
        passed = actual == expected

        print(f"\n[{index}] {scenario['title']}")
        print(f"decision: {actual}")
        print(f"reason: {result['reason']}")
        print("checks:")
        print(json.dumps(result["checks"], ensure_ascii=False, indent=2))

        if not passed:
            failed.append(
                {
                    "title": scenario["title"],
                    "expected": expected,
                    "actual": actual,
                }
            )

    print("\n汇总")
    print(f"total: {len(SCENARIOS)}")
    print(f"passed: {len(SCENARIOS) - len(failed)}")
    print(f"failed: {len(failed)}")

    if failed:
        print("失败场景：")
        print(json.dumps(failed, ensure_ascii=False, indent=2))
        return 1

    print("所有隔离审计场景通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

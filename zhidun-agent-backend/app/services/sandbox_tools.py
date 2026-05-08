"""Sandbox-only virtual tool execution for isolated validation.

This module never accesses real files, databases, or enterprise resources.
"""

from __future__ import annotations

from typing import Any


def execute_sandbox_tool(tool_name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    """Execute only safe virtual tools and return simulated results."""
    safe_arguments = arguments or {}

    if tool_name == "search_public_docs":
        query = safe_arguments.get("query", "")
        return {
            "ok": True,
            "toolName": tool_name,
            "result": f"公开知识库模拟结果：已检索到与“{query}”相关的公开流程说明。",
            "error": None,
        }

    if tool_name == "read_user_profile":
        resource = safe_arguments.get("resource", "self_profile")
        if resource != "self_profile":
            return {
                "ok": False,
                "toolName": tool_name,
                "result": "",
                "error": "read_user_profile 仅允许读取 self_profile 模拟资源。",
            }
        return {
            "ok": True,
            "toolName": tool_name,
            "result": "用户资料模拟结果：demo_user，角色为演示用户。",
            "error": None,
        }

    if tool_name == "read_system_file":
        return {
            "ok": False,
            "toolName": tool_name,
            "result": "",
            "error": "read_system_file 为高风险工具，隔离沙箱中拒绝执行。",
        }

    return {
        "ok": False,
        "toolName": tool_name,
        "result": "",
        "error": "工具未注册或不允许在隔离沙箱中执行。",
    }

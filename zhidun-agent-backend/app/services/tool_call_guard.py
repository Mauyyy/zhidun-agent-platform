"""Execution-before-audit guard for isolated model tool calls."""

from __future__ import annotations

import json
from typing import Any

from app.services.rbac_engine import check_rbac
from app.services.tool_registry import get_tool_definition


HIGH_SENSITIVE_MARKERS = ("/admin", "db_credentials", "secret", "token", "key")


def audit_tool_call(tool_call: dict[str, Any], role: str = "demo_user") -> dict[str, Any]:
    """Audit a virtual tool call without executing it."""
    tool_name, arguments = _normalize_tool_call(tool_call)
    definition = get_tool_definition(tool_name)
    registered = definition is not None
    resource = _extract_resource(tool_name, arguments)
    resource_level = _detect_resource_level(resource)

    checks: list[dict[str, Any]] = [
        {
            "name": "工具注册",
            "passed": registered,
            "expected": "工具需在 registry 中声明",
            "actual": tool_name or "UNKNOWN",
        }
    ]

    boundary_passed, boundary_actual = _check_argument_boundary(tool_name, resource, registered)
    checks.append(
        {
            "name": "参数边界",
            "passed": boundary_passed,
            "expected": "工具参数必须停留在允许资源域内",
            "actual": boundary_actual,
        }
    )

    sensitivity_passed = resource_level != "L4"
    checks.append(
        {
            "name": "资源敏感级别",
            "passed": sensitivity_passed,
            "expected": "普通用户不得访问 L4 资源",
            "actual": resource_level,
        }
    )

    if registered:
        rbac_result = check_rbac(
            {
                "name": tool_name,
                "resource": resource,
                "arguments": arguments,
            },
            role=role,
        )
        rbac_passed = bool(rbac_result.get("allowed"))
        rbac_actual = rbac_result.get("decision") or ("ALLOW" if rbac_passed else "DENY")
    else:
        rbac_result = {
            "allowed": False,
            "decision": "DENY",
            "reason": "未注册工具不进入授权执行。",
        }
        rbac_passed = False
        rbac_actual = "DENY"

    checks.append(
        {
            "name": "RBAC 校验",
            "passed": rbac_passed,
            "expected": "role/tool/resource 必须满足策略",
            "actual": rbac_actual,
        }
    )

    allowed = registered and boundary_passed and sensitivity_passed and rbac_passed
    decision = "ALLOWED" if allowed else "BLOCKED"

    return {
        "allowed": allowed,
        "decision": decision,
        "toolName": tool_name or "UNKNOWN",
        "resource": resource,
        "resourceLevel": resource_level,
        "role": role,
        "reason": _build_reason(
            allowed=allowed,
            registered=registered,
            boundary_passed=boundary_passed,
            resource_level=resource_level,
            rbac_result=rbac_result,
        ),
        "checks": checks,
    }


def _normalize_tool_call(tool_call: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    tool_name = tool_call.get("name")
    arguments = tool_call.get("arguments", {})

    function_payload = tool_call.get("function")
    if isinstance(function_payload, dict):
        tool_name = function_payload.get("name", tool_name)
        arguments = function_payload.get("arguments", arguments)

    if isinstance(arguments, str):
        try:
            parsed_arguments = json.loads(arguments)
            arguments = parsed_arguments if isinstance(parsed_arguments, dict) else {}
        except json.JSONDecodeError:
            arguments = {}

    return str(tool_name or ""), arguments if isinstance(arguments, dict) else {}


def _extract_resource(tool_name: str, arguments: dict[str, Any]) -> str:
    if tool_name == "search_public_docs":
        return str(arguments.get("resource") or "public_docs")
    if tool_name == "read_user_profile":
        return str(arguments.get("resource") or "self_profile")
    if tool_name == "read_system_file":
        return str(arguments.get("path") or arguments.get("file_path") or arguments.get("resource") or "")
    return str(arguments.get("resource") or arguments.get("path") or arguments.get("table") or "unknown")


def _detect_resource_level(resource: str) -> str:
    normalized = resource.lower()
    if any(marker in normalized for marker in HIGH_SENSITIVE_MARKERS):
        return "L4"
    if normalized == "self_profile":
        return "L2"
    if normalized == "public_docs":
        return "L1"
    return "L2"


def _check_argument_boundary(tool_name: str, resource: str, registered: bool) -> tuple[bool, str]:
    if not registered:
        return False, "未注册工具"
    if tool_name == "search_public_docs":
        return resource == "public_docs", resource
    if tool_name == "read_user_profile":
        return resource == "self_profile", resource
    if tool_name == "read_system_file":
        return False, "read_system_file 默认拒绝"
    return False, resource


def _build_reason(
    *,
    allowed: bool,
    registered: bool,
    boundary_passed: bool,
    resource_level: str,
    rbac_result: dict[str, Any],
) -> str:
    if allowed:
        return "工具调用通过注册、参数边界与 RBAC 校验。"
    if not registered:
        return "工具未在 registry 中声明，已阻断。"
    if resource_level == "L4":
        return "当前角色无权访问 L4 高敏资源，已在执行前阻断。"
    if not boundary_passed:
        return "工具参数越过允许资源边界，已在执行前阻断。"
    return str(rbac_result.get("reason") or "RBAC 校验未通过，已在执行前阻断。")

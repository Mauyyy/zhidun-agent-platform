from typing import Any

from app.core.config import RBAC_FILE
from app.services.data_store import read_json


def check_rbac(function_call: dict[str, Any] | None, role: str = "demo_user") -> dict[str, Any]:
    if not function_call:
        return {
            "allowed": True,
            "role": role,
            "reason": "未产生工具调用，无需 RBAC 拦截",
            "matchedPolicy": None,
            "matched_policy": None,
        }

    policy = read_json(RBAC_FILE, {})
    role_policy = policy.get("roles", {}).get(role, {})
    tool_name = function_call.get("name")
    resource = function_call.get("resource")

    for denied in role_policy.get("denied_tools", []):
        if denied.get("name") == tool_name and _resource_matches(resource, denied.get("resources", [])):
            return {
                "allowed": False,
                "role": role,
                "reason": "工具调用命中 RBAC 拒绝策略，已在执行前阻断。",
                "matchedPolicy": denied,
                "matched_policy": denied,
            }

    for allowed in role_policy.get("allowed_tools", []):
        if allowed.get("name") == tool_name and _resource_matches(resource, allowed.get("resources", [])):
            return {
                "allowed": True,
                "role": role,
                "reason": "工具调用命中 RBAC 白名单",
                "matchedPolicy": allowed,
                "matched_policy": allowed,
            }

    return {
        "allowed": False,
        "role": role,
        "reason": "工具调用未命中 RBAC 白名单，默认拒绝",
        "matchedPolicy": None,
        "matched_policy": None,
    }


def _resource_matches(resource: str | None, candidates: list[str]) -> bool:
    if not resource:
        return False
    lowered = resource.lower()
    return any(candidate.lower() in lowered or lowered in candidate.lower() for candidate in candidates)

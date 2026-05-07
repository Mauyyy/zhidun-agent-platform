from typing import Any

from app.core.config import RBAC_FILE, RULES_FILE, TEST_CASES_FILE
from app.services.data_store import DEFAULT_TEST_CASES, read_json


def list_rules() -> dict[str, Any]:
    rules = read_json(RULES_FILE, [])
    return {
        "items": rules,
        "total": len(rules),
    }


def get_rbac_policy() -> dict[str, Any]:
    policy = read_json(RBAC_FILE, {})
    roles = policy.get("roles", {})
    allowed_policy_count = sum(len(role.get("allowed_tools", [])) for role in roles.values())
    denied_policy_count = sum(len(role.get("denied_tools", [])) for role in roles.values())

    return {
        **policy,
        "summary": {
            "roleCount": len(roles),
            "allowedPolicyCount": allowed_policy_count,
            "deniedPolicyCount": denied_policy_count,
        },
    }


def list_test_cases() -> dict[str, Any]:
    test_cases = read_json(TEST_CASES_FILE, DEFAULT_TEST_CASES)
    return {
        "items": test_cases,
        "total": len(test_cases),
    }

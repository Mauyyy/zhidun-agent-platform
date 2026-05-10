from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import EVENTS_FILE, RBAC_FILE, RULES_FILE, TEST_CASES_FILE
from app.services.data_store import DEFAULT_TEST_CASES, read_json


def list_rules() -> dict[str, Any]:
    rules = read_json(RULES_FILE, [])
    hit_counts = _build_rule_hit_counts(days=7)
    enriched_rules = []
    for rule in rules:
        rule_id = rule.get("id", "")
        hits7d = hit_counts.get(rule_id, 0)
        enriched_rules.append(
            {
                **rule,
                "hits7d": hits7d,
                "hits_7d": hits7d,
            }
        )
    return {
        "items": enriched_rules,
        "total": len(rules),
    }


def _build_rule_hit_counts(days: int) -> dict[str, int]:
    events = read_json(EVENTS_FILE, [])
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    counts: dict[str, int] = {}

    for event in events:
        timestamp = _parse_event_timestamp(event.get("timestamp"))
        if timestamp is None or timestamp < cutoff:
            continue
        for hit in event.get("ruleHits") or event.get("rule_hits") or []:
            rule_id = hit.get("ruleId") or hit.get("rule_id")
            if not rule_id:
                continue
            counts[rule_id] = counts.get(rule_id, 0) + 1

    return counts


def _parse_event_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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

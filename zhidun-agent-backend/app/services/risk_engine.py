import re
from typing import Any

from app.core.config import HIGH_RISK_THRESHOLD, MEDIUM_RISK_THRESHOLD


SENSITIVE_RESOURCES = [
    "/admin",
    "db_credentials",
    "secret",
    "token",
    "key",
    "password",
]


def calculate_risk(user_input: str, rule_hits: list[dict[str, Any]]) -> dict[str, Any]:
    rule_score = min(sum(int(hit.get("score", 0)) for hit in rule_hits), 70)
    context_score = _context_risk_score(user_input)
    resource_score = _resource_sensitivity_score(user_input)
    total = min(rule_score + context_score + resource_score, 100)

    if total >= HIGH_RISK_THRESHOLD:
        level = "high"
    elif total >= MEDIUM_RISK_THRESHOLD:
        level = "medium"
    else:
        level = "low"

    risk_type = rule_hits[0]["riskType"] if rule_hits else "normal"

    return {
        "riskScore": total,
        "risk_score_total": total,
        "riskLevel": level,
        "risk_level": level,
        "riskType": risk_type,
        "risk_type": risk_type,
        "components": {
            "ruleScore": rule_score,
            "rule_score": rule_score,
            "contextScore": context_score,
            "context_score": context_score,
            "resourceSensitivityScore": resource_score,
            "resource_sensitivity_score": resource_score,
        },
    }


def _context_risk_score(user_input: str) -> int:
    risky_intents = ["读取", "导出", "泄露", "告诉我", "show me", "dump", "exfiltrate"]
    return 10 if any(term.lower() in user_input.lower() for term in risky_intents) else 0


def _resource_sensitivity_score(user_input: str) -> int:
    hit_count = 0
    for resource in SENSITIVE_RESOURCES:
        if re.search(re.escape(resource), user_input, flags=re.IGNORECASE):
            hit_count += 1
    return min(hit_count * 8, 20)


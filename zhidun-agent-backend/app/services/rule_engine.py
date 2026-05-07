import re
from typing import Any

from app.core.config import RULES_FILE
from app.services.data_store import read_json


def detect_rule_hits(user_input: str) -> list[dict[str, Any]]:
    rules = read_json(RULES_FILE, [])
    hits: list[dict[str, Any]] = []

    for rule in rules:
        matched_patterns = [
            pattern
            for pattern in rule.get("patterns", [])
            if re.search(re.escape(pattern), user_input, flags=re.IGNORECASE)
        ]
        if matched_patterns:
            hits.append(
                {
                    "ruleId": rule.get("id"),
                    "rule_id": rule.get("id"),
                    "name": rule.get("name"),
                    "riskType": rule.get("risk_type"),
                    "risk_type": rule.get("risk_type"),
                    "severity": rule.get("severity"),
                    "score": rule.get("score", 0),
                    "matchedPatterns": matched_patterns,
                    "matched_patterns": matched_patterns,
                }
            )

    return hits


import re
from typing import Any


REDACTION_PATTERNS = [
    ("phone", re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("api_key", re.compile(r"\b(?:sk|ak|api)[-_][A-Za-z0-9_-]{8,}\b", re.IGNORECASE)),
    ("system_prompt", re.compile(r"system prompt\s*:\s*[^.\n\u3002]+", re.IGNORECASE)),
]


def desensitize_output(raw_output: str) -> dict[str, Any]:
    redacted = raw_output
    redactions: list[dict[str, str]] = []

    for redaction_type, pattern in REDACTION_PATTERNS:
        matches = pattern.findall(redacted)
        if matches:
            redactions.extend({"type": redaction_type, "value": str(match)} for match in matches)
            redacted = pattern.sub(f"[REDACTED_{redaction_type.upper()}]", redacted)

    return {
        "before": raw_output,
        "after": redacted,
        "redactions": redactions,
        "changed": raw_output != redacted,
    }

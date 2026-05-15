from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import EVENTS_FILE, RBAC_FILE
from app.services.data_store import read_json


def get_dashboard_overview() -> dict[str, Any]:
    events = read_json(EVENTS_FILE, [])
    total_events = len(events)
    high_risk_events = sum(1 for event in events if _risk_level(event) == "high")
    tool_audit_count = sum(1 for event in events if event.get("functionCall") or event.get("function_call"))
    risk_type_distribution = _build_risk_type_distribution(events)
    leak_block_count = sum(
        1
        for event in events
        if event.get("decision") == "BLOCKED" and _risk_type(event) == "sensitive_data_exfiltration"
    )

    llm_mode_distribution = _build_llm_mode_distribution(events)
    tool_call_stats = _build_tool_call_stats(events)

    return {
        "stats": {
            "totalEvents": total_events,
            "highRiskEvents": high_risk_events,
            "toolAuditCount": tool_audit_count,
            "leakBlockCount": leak_block_count,
            "weekChangePercent": _week_change_percent(events),
            "llmModeDistribution": llm_mode_distribution,
            "toolCallStats": tool_call_stats,
        },
        "trend": _build_trend(events),
        "riskTypeDistribution": risk_type_distribution,
        "risk_type_distribution": risk_type_distribution,
    }


def get_risk_matrix_summary() -> dict[str, int]:
    events = read_json(EVENTS_FILE, [])
    rbac = read_json(RBAC_FILE, {})
    roles = rbac.get("roles", {})
    denied_policy_count = sum(len(role.get("denied_tools", [])) for role in roles.values())
    sensitive_event_types = {
        event.get("riskType") or event.get("risk_type")
        for event in events
        if event.get("decision") == "BLOCKED"
    }

    return {
        "monitoredNodes": max(4, len(roles) + denied_policy_count + 2),
        "highRiskZones": max(1 if events else 0, len([item for item in sensitive_event_types if item])),
    }


def _build_trend(events: list[dict[str, Any]]) -> dict[str, list[Any]]:
    today = datetime.now(timezone.utc).date()
    dates = [(today - timedelta(days=offset)).isoformat() for offset in range(6, -1, -1)]
    counters = {
        "promptInjection": Counter(),
        "ruleOverride": Counter(),
        "privilegeEscalation": Counter(),
        "sensitiveExfiltration": Counter(),
    }

    for event in events:
        day = _event_date(event)
        if not day or day not in dates:
            continue
        
        risk_types = _get_risk_types_from_event(event)
        if risk_types:
            for risk_type in risk_types:
                if risk_type == "prompt_injection":
                    counters["promptInjection"][day] += 1
                elif risk_type == "rule_override":
                    counters["ruleOverride"][day] += 1
                elif risk_type == "privilege_escalation":
                    counters["privilegeEscalation"][day] += 1
                elif risk_type == "sensitive_data_exfiltration":
                    counters["sensitiveExfiltration"][day] += 1
        else:
            risk_type = _risk_type(event)
            if risk_type == "prompt_injection":
                counters["promptInjection"][day] += 1
            elif risk_type == "rule_override":
                counters["ruleOverride"][day] += 1
            elif risk_type == "privilege_escalation":
                counters["privilegeEscalation"][day] += 1
            elif risk_type == "sensitive_data_exfiltration":
                counters["sensitiveExfiltration"][day] += 1

    return {
        "dates": dates,
        "promptInjection": [counters["promptInjection"][day] for day in dates],
        "ruleOverride": [counters["ruleOverride"][day] for day in dates],
        "privilegeEscalation": [counters["privilegeEscalation"][day] for day in dates],
        "sensitiveExfiltration": [counters["sensitiveExfiltration"][day] for day in dates],
    }


def _build_risk_type_distribution(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = {
        "prompt_injection": "提示注入",
        "rule_override": "规则覆盖",
        "privilege_escalation": "工具越权",
        "sensitive_data_exfiltration": "敏感泄露",
        "normal": "正常请求",
        "unknown": "其他",
    }
    counters: Counter[str] = Counter()

    for event in events:
        risk_types = _get_risk_types_from_event(event)
        if risk_types:
            for risk_type in risk_types:
                counters[risk_type] += 1
        else:
            risk_type = _risk_type(event) or "unknown"
            counters[risk_type] += 1

    ordered_types = [
        "prompt_injection",
        "rule_override",
        "privilege_escalation",
        "sensitive_data_exfiltration",
        "normal",
    ]
    distribution = [
        {
            "type": risk_type,
            "label": labels[risk_type],
            "count": counters[risk_type],
        }
        for risk_type in ordered_types
    ]

    other_count = sum(
        count for risk_type, count in counters.items() if risk_type not in set(ordered_types)
    )
    if other_count:
        distribution.append({"type": "unknown", "label": labels["unknown"], "count": other_count})

    return distribution


def _build_llm_mode_distribution(events: list[dict[str, Any]]) -> dict[str, int]:
    modes = ["mvp_rule_based", "real_llm_text", "real_model_tool_call", "fallback"]
    counters: Counter[str] = Counter()

    for event in events:
        llm_mode = str(event.get("llmMode") or event.get("llm_mode") or "").lower()
        if llm_mode in modes:
            counters[llm_mode] += 1
        else:
            counters["mvp_rule_based"] += 1

    return {mode: counters[mode] for mode in modes}


def _build_tool_call_stats(events: list[dict[str, Any]]) -> dict[str, int]:
    compliant_count = 0
    blocked_count = 0
    param_violation_count = 0
    total_count = 0

    for event in events:
        function_call = event.get("functionCall") or event.get("function_call")
        if not function_call:
            continue
        
        total_count += 1
        rbac_result = event.get("rbacResult") or event.get("rbac_result") or {}
        allowed = rbac_result.get("allowed", False)
        decision = event.get("decision", "").upper()
        
        if allowed or decision == "ALLOWED":
            compliant_count += 1
        elif decision == "BLOCKED":
            if rbac_result.get("allowed") is False:
                blocked_count += 1
            else:
                param_violation_count += 1
        else:
            param_violation_count += 1

    return {
        "compliantCount": compliant_count,
        "blockedCount": blocked_count,
        "paramViolationCount": param_violation_count,
        "totalCount": total_count,
    }


def _get_risk_types_from_event(event: dict[str, Any]) -> set[str]:
    risk_types: set[str] = set()
    rule_hits = event.get("ruleHits") or event.get("rule_hits") or []
    
    for hit in rule_hits:
        risk_type = str(hit.get("riskType") or hit.get("risk_type") or "").lower()
        if risk_type:
            risk_types.add(risk_type)
    
    return risk_types


def _week_change_percent(events: list[dict[str, Any]]) -> float:
    now = datetime.now(timezone.utc)
    current_start = now - timedelta(days=7)
    previous_start = now - timedelta(days=14)
    current_count = 0
    previous_count = 0

    for event in events:
        event_time = _event_datetime(event)
        if not event_time:
            continue
        if event_time >= current_start:
            current_count += 1
        elif previous_start <= event_time < current_start:
            previous_count += 1

    if previous_count == 0:
        return 0.0
    return round(((current_count - previous_count) / previous_count) * 100, 2)


def _event_datetime(event: dict[str, Any]) -> datetime | None:
    timestamp = event.get("timestamp")
    if not isinstance(timestamp, str):
        return None
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _event_date(event: dict[str, Any]) -> str | None:
    event_time = _event_datetime(event)
    return event_time.date().isoformat() if event_time else None


def _risk_level(event: dict[str, Any]) -> str:
    return str(event.get("riskLevel") or event.get("risk_level") or "").lower()


def _risk_type(event: dict[str, Any]) -> str:
    return str(event.get("riskType") or event.get("risk_type") or "").lower()
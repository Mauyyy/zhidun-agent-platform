from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.config import EVENTS_FILE, HIGH_RISK_THRESHOLD
from app.services.data_store import read_json, write_json


def should_create_event(risk_score: int, decision: str) -> bool:
    return risk_score >= HIGH_RISK_THRESHOLD or decision == "BLOCKED"


def create_audit_event(
    *,
    session_id: str | None,
    user_input: str,
    rule_hits: list[dict[str, Any]],
    risk: dict[str, Any],
    function_call: dict[str, Any] | None,
    rbac_result: dict[str, Any],
    output_diff: dict[str, Any],
    action: str,
    decision: str,
) -> dict[str, Any]:
    event_id = f"evt_{uuid4().hex[:12]}"
    timestamp = datetime.now(timezone.utc).isoformat()
    conclusion = _build_conclusion(risk, decision, rbac_result)

    event = {
        "eventId": event_id,
        "event_id": event_id,
        "sessionId": session_id,
        "session_id": session_id,
        "timestamp": timestamp,
        "riskLevel": risk["riskLevel"],
        "risk_level": risk["risk_level"],
        "riskType": risk["riskType"],
        "risk_type": risk["risk_type"],
        "action": action,
        "decision": decision,
        "userInput": user_input,
        "user_input": user_input,
        "riskScore": risk["riskScore"],
        "risk_score_total": risk["risk_score_total"],
        "riskComponents": risk["components"],
        "risk_components": risk["components"],
        "ruleHits": rule_hits,
        "rule_hits": rule_hits,
        "functionCall": function_call,
        "function_call": function_call,
        "rbacResult": rbac_result,
        "rbac_result": rbac_result,
        "outputDiff": output_diff,
        "output_diff": output_diff,
        "auditConclusion": conclusion,
        "audit_conclusion": conclusion,
    }

    events = read_json(EVENTS_FILE, [])
    events.append(event)
    write_json(EVENTS_FILE, events)
    return event


def list_events() -> list[dict[str, Any]]:
    events = read_json(EVENTS_FILE, [])
    return sorted(events, key=lambda item: item.get("timestamp", ""), reverse=True)


def get_event(event_id: str) -> dict[str, Any] | None:
    return next(
        (
            event
            for event in read_json(EVENTS_FILE, [])
            if event.get("eventId") == event_id or event.get("event_id") == event_id
        ),
        None,
    )


def create_event_report(event_id: str) -> dict[str, Any] | None:
    events = read_json(EVENTS_FILE, [])
    for event in events:
        if event.get("eventId") == event_id or event.get("event_id") == event_id:
            report = {
                "eventId": event.get("eventId"),
                "event_id": event.get("event_id"),
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "title": "智盾Agent 安全审计报告",
                "summary": event.get("auditConclusion"),
                "decision": event.get("decision"),
                "riskLevel": event.get("riskLevel"),
                "risk_level": event.get("risk_level"),
                "riskScore": event.get("riskScore"),
                "risk_score_total": event.get("risk_score_total"),
                "recommendation": _build_recommendation(event),
            }
            event["report"] = report
            write_json(EVENTS_FILE, events)
            return report
    return None


def _build_conclusion(risk: dict[str, Any], decision: str, rbac_result: dict[str, Any]) -> str:
    if decision == "BLOCKED":
        return f"请求风险等级为 {risk['riskLevel']}，{rbac_result.get('reason')}最终结论：阻断。"
    if risk["riskScore"] >= HIGH_RISK_THRESHOLD:
        return "请求达到高风险阈值，但未产生越权工具执行，已完成输出脱敏和审计记录。"
    return "请求已通过最小安全闭环检测。"


def _build_recommendation(event: dict[str, Any]) -> str:
    if event.get("decision") == "BLOCKED":
        return "建议保留当前 RBAC 默认拒绝策略，并补充更细粒度的敏感资源分类。"
    return "建议持续观察同类输入，必要时提高相关规则权重。"

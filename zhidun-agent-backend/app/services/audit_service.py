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
    generated_at = datetime.now(timezone.utc).isoformat()

    for event in events:
        if event.get("eventId") == event_id or event.get("event_id") == event_id:
            report = {
                "eventId": event.get("eventId"),
                "event_id": event.get("event_id"),
                "generatedAt": generated_at,
                "generated_at": generated_at,
                "title": "智盾Agent 安全审计报告",
                "summary": {
                    "decision": event.get("decision"),
                    "riskLevel": event.get("riskLevel"),
                    "risk_level": event.get("risk_level"),
                    "riskScore": event.get("riskScore"),
                    "risk_score_total": event.get("risk_score_total"),
                    "conclusion": event.get("auditConclusion"),
                },
                "decision": event.get("decision"),
                "riskLevel": event.get("riskLevel"),
                "risk_level": event.get("risk_level"),
                "riskScore": event.get("riskScore"),
                "risk_score_total": event.get("risk_score_total"),
                "sections": _build_report_sections(event),
                "recommendation": _build_recommendation(event),
            }
            event["report"] = report
            write_json(EVENTS_FILE, events)
            return report
    return None


def _build_report_sections(event: dict[str, Any]) -> list[dict[str, Any]]:
    risk_components = event.get("riskComponents") or event.get("risk_components") or {}
    output_diff = event.get("outputDiff") or event.get("output_diff") or {}
    rbac_result = event.get("rbacResult") or event.get("rbac_result") or {}
    function_call = event.get("functionCall") or event.get("function_call")
    rule_hits = event.get("ruleHits") or event.get("rule_hits") or []

    return [
        {
            "key": "input_detection",
            "title": "输入检测",
            "items": [
                {"label": "原始输入", "value": event.get("userInput") or event.get("user_input")},
                {"label": "规则命中数量", "value": len(rule_hits)},
                {"label": "规则命中详情", "value": rule_hits},
            ],
        },
        {
            "key": "risk_scoring",
            "title": "风险评分",
            "items": [
                {"label": "综合风险分", "value": event.get("riskScore")},
                {"label": "风险等级", "value": event.get("riskLevel")},
                {"label": "风险类型", "value": event.get("riskType")},
                {"label": "评分分解", "value": risk_components},
            ],
        },
        {
            "key": "function_call_audit",
            "title": "Function Calling 执行前审计",
            "items": [
                {"label": "工具调用请求", "value": function_call},
                {
                    "label": "审计状态",
                    "value": "已在工具执行前完成审计" if function_call else "未产生工具调用",
                },
            ],
        },
        {
            "key": "rbac",
            "title": "RBAC 越权判断",
            "items": [
                {"label": "是否放行", "value": rbac_result.get("allowed")},
                {"label": "角色", "value": rbac_result.get("role")},
                {"label": "校验原因", "value": rbac_result.get("reason")},
                {"label": "匹配策略", "value": rbac_result.get("matchedPolicy")},
            ],
        },
        {
            "key": "output_protection",
            "title": "输出防护",
            "items": [
                {"label": "脱敏前", "value": output_diff.get("before")},
                {"label": "脱敏后", "value": output_diff.get("after")},
                {"label": "是否发生脱敏", "value": output_diff.get("changed")},
                {"label": "脱敏记录", "value": output_diff.get("redactions", [])},
            ],
        },
        {
            "key": "audit_conclusion",
            "title": "审计结论",
            "items": [
                {"label": "最终裁决", "value": event.get("decision")},
                {"label": "审计结论", "value": event.get("auditConclusion")},
            ],
        },
        {
            "key": "recommendation",
            "title": "处置建议",
            "items": [
                {"label": "建议", "value": _build_recommendation(event)},
            ],
        },
    ]


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

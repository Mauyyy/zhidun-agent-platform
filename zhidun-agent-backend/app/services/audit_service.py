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


def list_tool_invocations(page: int = 1, page_size: int = 12) -> dict[str, Any]:
    invocations = [
        invocation
        for event in list_events()
        if (invocation := _event_to_tool_invocation(event)) is not None
    ]
    safe_page = max(page, 1)
    safe_page_size = max(page_size, 1)
    start = (safe_page - 1) * safe_page_size
    end = start + safe_page_size

    return {
        "items": invocations[start:end],
        "total": len(invocations),
        "page": safe_page,
        "pageSize": safe_page_size,
    }


def get_tool_invocation(invocation_id: str) -> dict[str, Any] | None:
    for event in list_events():
        invocation = _event_to_tool_invocation(event)
        if not invocation:
            continue
        if invocation.get("id") == invocation_id:
            return invocation
    return None


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


def _event_to_tool_invocation(event: dict[str, Any]) -> dict[str, Any] | None:
    function_call = event.get("functionCall") or event.get("function_call")
    if not function_call:
        return None

    rbac_result = event.get("rbacResult") or event.get("rbac_result") or {}
    output_diff = event.get("outputDiff") or event.get("output_diff") or {}
    event_id = event.get("eventId") or event.get("event_id") or "unknown"
    tool_name = function_call.get("name") or "unknown_tool"
    arguments = function_call.get("arguments") or {}
    resource = function_call.get("resource") or arguments.get("path") or arguments.get("file_path")
    allowed = bool(rbac_result.get("allowed", False))
    decision = event.get("decision") or ("ALLOWED" if allowed else "BLOCKED")

    return {
        "id": f"inv_{event_id}",
        "eventId": event_id,
        "event_id": event_id,
        "timestamp": event.get("timestamp"),
        "time": event.get("timestamp"),
        "agent": "智盾Agent",
        "toolName": tool_name,
        "tool_name": tool_name,
        "arguments": arguments,
        "argsBrief": _build_args_brief(arguments, resource),
        "args_brief": _build_args_brief(arguments, resource),
        "callerRole": rbac_result.get("role") or rbac_result.get("matched_role") or "demo_user",
        "caller_role": rbac_result.get("role") or rbac_result.get("matched_role") or "demo_user",
        "requiredLevel": _required_level(resource, event),
        "required_level": _required_level(resource, event),
        "passed": allowed,
        "rbacBreach": not allowed,
        "rbac_breach": not allowed,
        "decision": decision,
        "riskScore": event.get("riskScore") or event.get("risk_score_total") or 0,
        "risk_score": event.get("riskScore") or event.get("risk_score_total") or 0,
        "riskLevel": event.get("riskLevel") or event.get("risk_level") or "low",
        "risk_level": event.get("riskLevel") or event.get("risk_level") or "low",
        "rbacResult": rbac_result,
        "rbac_result": rbac_result,
        "status": "allowed" if allowed else "blocked",
        "outputDiff": output_diff,
        "output_diff": output_diff,
        "auditConclusion": event.get("auditConclusion") or event.get("audit_conclusion"),
        "audit_conclusion": event.get("auditConclusion") or event.get("audit_conclusion"),
        "contextChain": [
            {
                "turn": 1,
                "speaker": "user",
                "text": event.get("userInput") or event.get("user_input") or "",
            },
            {
                "turn": 2,
                "speaker": "agent",
                "text": "工具调用已放行" if allowed else "工具调用已在执行前阻断",
            },
        ],
        "context_chain": [
            {
                "turn": 1,
                "speaker": "user",
                "text": event.get("userInput") or event.get("user_input") or "",
            },
            {
                "turn": 2,
                "speaker": "agent",
                "text": "工具调用已放行" if allowed else "工具调用已在执行前阻断",
            },
        ],
    }


def _build_args_brief(arguments: dict[str, Any], resource: Any) -> str:
    if resource:
        return f"path={resource}"
    if not arguments:
        return "无参数"
    return ", ".join(f"{key}={value}" for key, value in list(arguments.items())[:3])


def _required_level(resource: Any, event: dict[str, Any]) -> str:
    text = f"{resource or ''} {event.get('riskType') or event.get('risk_type') or ''}".lower()
    if any(keyword in text for keyword in ["/admin", "db_credentials", "secret"]):
        return "L4"
    if any(keyword in text for keyword in ["token", "key", "password"]):
        return "L3"
    return "L2"


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

from fastapi import APIRouter

from app.core.response import fail, success
from app.schemas.chat import ChatMessageRequest
from app.services.audit_service import create_audit_event, should_create_event
from app.services.desensitizer import desensitize_output
from app.services.function_calling import build_simulated_output, simulate_function_call
from app.services.rbac_engine import check_rbac
from app.services.risk_engine import calculate_risk
from app.services.rule_engine import detect_rule_hits

router = APIRouter()


@router.post("/chat/messages")
def create_chat_message(payload: ChatMessageRequest) -> dict:
    user_input = payload.normalized_content()
    if not user_input:
        return fail("content or message is required", code=400, data=None)

    rule_hits = detect_rule_hits(user_input)
    risk = calculate_risk(user_input, rule_hits)
    function_call = simulate_function_call(user_input)
    rbac_result = check_rbac(function_call)
    blocked = function_call is not None and not rbac_result["allowed"]
    raw_output = build_simulated_output(blocked=blocked, function_call=function_call)
    output_diff = desensitize_output(raw_output)

    decision = "BLOCKED" if blocked else "ALLOWED"
    action = "function_call_blocked" if blocked else "chat_guardrail_checked"
    event = None
    if should_create_event(risk["riskScore"], decision):
        event = create_audit_event(
            session_id=payload.session_id,
            user_input=user_input,
            rule_hits=rule_hits,
            risk=risk,
            function_call=function_call,
            rbac_result=rbac_result,
            output_diff=output_diff,
            action=action,
            decision=decision,
        )

    conclusion = event["auditConclusion"] if event else "请求已通过最小安全闭环检测。"
    return success(
        {
            "sessionId": payload.session_id,
            "session_id": payload.session_id,
            "reply": output_diff["after"],
            "blocked": blocked,
            "decision": decision,
            "riskLevel": risk["riskLevel"],
            "risk_level": risk["risk_level"],
            "riskScore": risk["riskScore"],
            "risk_score_total": risk["risk_score_total"],
            "riskType": risk["riskType"],
            "risk_type": risk["risk_type"],
            "ruleHits": rule_hits,
            "rule_hits": rule_hits,
            "functionCall": function_call,
            "function_call": function_call,
            "rbacResult": rbac_result,
            "rbac_result": rbac_result,
            "outputDiff": output_diff,
            "output_diff": output_diff,
            "eventId": event["eventId"] if event else None,
            "event_id": event["event_id"] if event else None,
            "auditConclusion": conclusion,
            "audit_conclusion": conclusion,
        }
    )

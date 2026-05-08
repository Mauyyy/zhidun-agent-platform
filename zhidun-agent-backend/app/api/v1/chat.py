from fastapi import APIRouter

from app.core.config import HIGH_RISK_THRESHOLD, has_openai_api_key, use_real_llm, use_real_tool_call
from app.core.response import fail, success
from app.schemas.chat import ChatMessageRequest
from app.services.audit_service import create_audit_event, should_create_event
from app.services.desensitizer import desensitize_output
from app.services.function_calling import build_simulated_output, simulate_function_call
from app.services.llm_client import generate_plain_reply
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
    llm_mode, llm_trace, real_output = _try_generate_real_text_reply(
        user_input=user_input,
        blocked=blocked,
        risk=risk,
    )
    if real_output is not None:
        raw_output = real_output
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
            "llmMode": llm_mode,
            "llm_mode": llm_mode,
            "llmTrace": llm_trace,
            "llm_trace": llm_trace,
            "eventId": event["eventId"] if event else None,
            "event_id": event["event_id"] if event else None,
            "auditConclusion": conclusion,
            "audit_conclusion": conclusion,
        }
    )


def _try_generate_real_text_reply(
    *,
    user_input: str,
    blocked: bool,
    risk: dict,
) -> tuple[str, dict, str | None]:
    real_llm_enabled = use_real_llm()
    real_tool_call_enabled = use_real_tool_call()
    trace = {
        "enabled": real_llm_enabled,
        "realToolCallEnabled": real_tool_call_enabled,
        "real_tool_call_enabled": real_tool_call_enabled,
        "provider": None,
        "model": None,
        "used": False,
        "reason": "USE_REAL_LLM=false，使用当前规则 MVP。",
    }

    if not real_llm_enabled:
        return "mvp_rule_based", trace, None

    if blocked or risk["riskScore"] >= HIGH_RISK_THRESHOLD or risk["riskLevel"] != "low":
        trace["reason"] = "请求存在较高风险或已触发阻断，未调用真实大模型。"
        return "mvp_rule_based", trace, None

    if not has_openai_api_key():
        trace["reason"] = "缺少 OPENAI_API_KEY，回退当前规则 MVP。"
        return "fallback", trace, None

    try:
        result = generate_plain_reply(user_input)
    except Exception as exc:
        trace["reason"] = f"真实大模型调用异常：{exc.__class__.__name__}，回退当前规则 MVP。"
        return "fallback", trace, None
    trace.update(
        {
            "provider": result.get("provider"),
            "model": result.get("model"),
        }
    )

    if not result.get("ok"):
        trace["reason"] = result.get("error") or "真实大模型调用失败，回退当前规则 MVP。"
        return "fallback", trace, None

    trace["used"] = True
    trace["reason"] = "低风险请求已使用真实大模型普通文本回复；未启用真实 tool_call 主线。"
    return "real_llm_text", trace, result.get("content") or ""

from fastapi import APIRouter

from app.core.config import HIGH_RISK_THRESHOLD, has_openai_api_key, use_real_llm, use_real_tool_call
from app.core.response import fail, success
from app.schemas.chat import ChatMessageRequest
from app.services.audit_service import create_audit_event, should_create_event
from app.services.desensitizer import desensitize_output
from app.services.function_calling import build_simulated_output, simulate_function_call
from app.services import llm_client
from app.services.rbac_engine import check_rbac
from app.services.risk_engine import calculate_risk
from app.services.rule_engine import detect_rule_hits
from app.services.sandbox_tools import execute_sandbox_tool
from app.services.tool_call_guard import audit_tool_call
from app.services.tool_registry import get_tool_schema_list

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
    blocked = _should_block_request(risk, function_call, rbac_result)
    raw_output = build_simulated_output(blocked=blocked, function_call=function_call)
    function_call_source = "simulated" if function_call else "none"
    guard_result = None
    sandbox_execution = None
    llm_result = _try_generate_real_reply(
        user_input=user_input,
        blocked=blocked,
        risk=risk,
    )
    llm_mode = llm_result["llm_mode"]
    llm_trace = llm_result["llm_trace"]
    if llm_result.get("raw_output") is not None:
        raw_output = llm_result["raw_output"]
    if llm_result.get("function_call") is not None:
        function_call = llm_result["function_call"]
        function_call_source = "real_model_tool_call"
    if llm_result.get("rbac_result") is not None:
        rbac_result = llm_result["rbac_result"]
    if llm_result.get("blocked") is not None:
        blocked = llm_result["blocked"]
    guard_result = llm_result.get("guard_result")
    sandbox_execution = llm_result.get("sandbox_execution")
    output_diff = desensitize_output(raw_output)

    decision = "BLOCKED" if blocked else "ALLOWED"
    action = _build_action(blocked, function_call_source, llm_mode)
    event = None
    if (
        should_create_event(risk["riskScore"], decision)
        or function_call is not None
        or llm_mode in {"real_llm_text", "real_model_tool_call"}
    ):
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
            function_call_source=function_call_source,
            llm_mode=llm_mode,
            llm_trace=llm_trace,
            guard_result=guard_result,
            sandbox_execution=sandbox_execution,
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
            "functionCallSource": function_call_source,
            "function_call_source": function_call_source,
            "rbacResult": rbac_result,
            "rbac_result": rbac_result,
            "outputDiff": output_diff,
            "output_diff": output_diff,
            "llmMode": llm_mode,
            "llm_mode": llm_mode,
            "llmTrace": llm_trace,
            "llm_trace": llm_trace,
            "guardResult": guard_result,
            "guard_result": guard_result,
            "sandboxExecution": sandbox_execution,
            "sandbox_execution": sandbox_execution,
            "eventId": event["eventId"] if event else None,
            "event_id": event["event_id"] if event else None,
            "auditConclusion": conclusion,
            "audit_conclusion": conclusion,
        }
    )


def _try_generate_real_reply(
    *,
    user_input: str,
    blocked: bool,
    risk: dict,
) -> dict:
    real_llm_enabled = use_real_llm()
    real_tool_call_enabled = use_real_tool_call()
    trace = {
        "enabled": real_llm_enabled,
        "realToolCallEnabled": real_tool_call_enabled,
        "real_tool_call_enabled": real_tool_call_enabled,
        "provider": None,
        "model": None,
        "rawType": None,
        "raw_type": None,
        "toolCalls": [],
        "tool_calls": [],
        "used": False,
        "reason": "USE_REAL_LLM=false，使用当前规则 MVP。",
    }

    if not real_llm_enabled:
        return _llm_branch_result("mvp_rule_based", trace)

    if blocked or risk["riskScore"] >= HIGH_RISK_THRESHOLD or risk["riskLevel"] != "low":
        trace["reason"] = "请求存在较高风险或已触发阻断，未调用真实大模型。"
        return _llm_branch_result("mvp_rule_based", trace)

    if not has_openai_api_key():
        trace["reason"] = "缺少 OPENAI_API_KEY，回退当前规则 MVP。"
        return _llm_branch_result("fallback", trace)

    if real_tool_call_enabled:
        return _try_generate_real_tool_call_reply(user_input, trace)
    return _try_generate_real_text_reply(user_input, trace)


def _try_generate_real_text_reply(user_input: str, trace: dict) -> dict:
    try:
        result = llm_client.generate_plain_reply(user_input)
    except Exception as exc:
        trace["reason"] = f"真实大模型调用异常：{exc.__class__.__name__}，回退当前规则 MVP。"
        return _llm_branch_result("fallback", trace)
    trace.update(
        {
            "provider": result.get("provider"),
            "model": result.get("model"),
            "rawType": "text" if result.get("ok") else "error",
            "raw_type": "text" if result.get("ok") else "error",
        }
    )

    if not result.get("ok"):
        trace["reason"] = result.get("error") or "真实大模型调用失败，回退当前规则 MVP。"
        return _llm_branch_result("fallback", trace)

    trace["used"] = True
    trace["reason"] = "低风险请求已使用真实大模型普通文本回复；未启用真实 tool_call 主线。"
    return _llm_branch_result("real_llm_text", trace, raw_output=result.get("content") or "")


def _try_generate_real_tool_call_reply(user_input: str, trace: dict) -> dict:
    try:
        result = llm_client.generate_tool_call_response(user_input, get_tool_schema_list())
    except Exception as exc:
        trace["reason"] = f"真实 tool_call 调用异常：{exc.__class__.__name__}，回退当前规则 MVP。"
        return _llm_branch_result("fallback", trace)

    tool_calls = result.get("toolCalls") or []
    raw_type = result.get("rawType") or ("tool_call" if tool_calls else "text")
    trace.update(
        {
            "provider": result.get("provider"),
            "model": result.get("model"),
            "rawType": raw_type,
            "raw_type": raw_type,
            "toolCalls": tool_calls,
            "tool_calls": tool_calls,
        }
    )

    if not result.get("ok"):
        trace["reason"] = result.get("error") or "真实 tool_call 调用失败，回退当前规则 MVP。"
        return _llm_branch_result("fallback", trace)

    trace["used"] = True
    if not tool_calls:
        trace["reason"] = "真实模型未返回 tool_call，按普通文本回复处理。"
        return _llm_branch_result("real_llm_text", trace, raw_output=result.get("content") or "")

    for tool_call in tool_calls:
        normalized_call = _normalize_real_tool_call(tool_call)
        guard_result = audit_tool_call(normalized_call)
        rbac_result = _guard_to_rbac_result(guard_result)
        if not guard_result.get("allowed"):
            trace["reason"] = "真实模型 tool_call 未通过执行前审计，已阻断。"
            raw_output = f"请求已被阻断：{guard_result.get('reason')}"
            return _llm_branch_result(
                "real_model_tool_call",
                trace,
                raw_output=raw_output,
                blocked=True,
                function_call=normalized_call,
                rbac_result=rbac_result,
                guard_result=guard_result,
                sandbox_execution=_empty_sandbox_execution(normalized_call, executed=False),
            )

        sandbox_result = execute_sandbox_tool(
            normalized_call["name"],
            normalized_call.get("arguments") or {},
        )
        sandbox_execution = _build_sandbox_execution(normalized_call, sandbox_result, executed=True)
        if not sandbox_result.get("ok"):
            trace["reason"] = "沙箱虚拟工具执行失败，已降级阻断。"
            raw_output = f"请求已被阻断：{sandbox_result.get('error') or '虚拟工具执行失败'}"
            return _llm_branch_result(
                "real_model_tool_call",
                trace,
                raw_output=raw_output,
                blocked=True,
                function_call=normalized_call,
                rbac_result={
                    **rbac_result,
                    "allowed": False,
                    "reason": sandbox_result.get("error") or "虚拟工具执行失败，已阻断。",
                },
                guard_result=guard_result,
                sandbox_execution=sandbox_execution,
            )

        trace["reason"] = "真实模型 tool_call 已通过 guard 审计，并仅执行沙箱虚拟工具。"
        raw_output = f"已完成安全工具调用：{sandbox_execution['resultSummary']}"
        return _llm_branch_result(
            "real_model_tool_call",
            trace,
            raw_output=raw_output,
            blocked=False,
            function_call=normalized_call,
            rbac_result=rbac_result,
            guard_result=guard_result,
            sandbox_execution=sandbox_execution,
        )

    trace["reason"] = "模型返回 tool_call 为空，回退当前规则 MVP。"
    return _llm_branch_result("fallback", trace)


def _should_block_request(
    risk: dict,
    function_call: dict | None,
    rbac_result: dict,
) -> bool:
    if risk["riskScore"] >= HIGH_RISK_THRESHOLD or risk["riskLevel"] == "high":
        return True
    return function_call is not None and not rbac_result["allowed"]


def _llm_branch_result(
    llm_mode: str,
    llm_trace: dict,
    *,
    raw_output: str | None = None,
    blocked: bool | None = None,
    function_call: dict | None = None,
    rbac_result: dict | None = None,
    guard_result: dict | None = None,
    sandbox_execution: dict | None = None,
) -> dict:
    return {
        "llm_mode": llm_mode,
        "llm_trace": llm_trace,
        "raw_output": raw_output,
        "blocked": blocked,
        "function_call": function_call,
        "rbac_result": rbac_result,
        "guard_result": guard_result,
        "sandbox_execution": sandbox_execution,
    }


def _normalize_real_tool_call(tool_call: dict) -> dict:
    name = tool_call.get("name") or "UNKNOWN"
    arguments = tool_call.get("arguments") or {}
    resource = (
        arguments.get("resource")
        or arguments.get("path")
        or arguments.get("file_path")
        or ("public_docs" if name == "search_public_docs" else None)
        or ("self_profile" if name == "read_user_profile" else None)
    )
    return {
        "id": tool_call.get("id") or "",
        "name": name,
        "arguments": arguments,
        "resource": resource,
    }


def _guard_to_rbac_result(guard_result: dict) -> dict:
    return {
        "allowed": bool(guard_result.get("allowed")),
        "role": guard_result.get("role") or "demo_user",
        "reason": guard_result.get("reason"),
        "matchedPolicy": None,
        "matched_policy": None,
        "decision": "ALLOW" if guard_result.get("allowed") else "DENY",
        "checks": guard_result.get("checks", []),
    }


def _empty_sandbox_execution(function_call: dict, *, executed: bool) -> dict:
    return {
        "executed": executed,
        "toolName": function_call.get("name"),
        "tool_name": function_call.get("name"),
        "ok": False,
        "resultSummary": "",
        "result_summary": "",
        "error": None,
    }


def _build_sandbox_execution(function_call: dict, sandbox_result: dict, *, executed: bool) -> dict:
    result = sandbox_result.get("result") or ""
    return {
        "executed": executed,
        "toolName": function_call.get("name"),
        "tool_name": function_call.get("name"),
        "ok": bool(sandbox_result.get("ok")),
        "resultSummary": result[:160],
        "result_summary": result[:160],
        "error": sandbox_result.get("error"),
    }


def _build_action(blocked: bool, function_call_source: str, llm_mode: str) -> str:
    if llm_mode == "real_model_tool_call":
        return "real_tool_call_blocked" if blocked else "real_tool_call_allowed"
    if blocked:
        return "function_call_blocked"
    if function_call_source == "simulated":
        return "function_call_allowed"
    if function_call_source == "real_model_tool_call":
        return "real_tool_call_checked"
    return "chat_guardrail_checked"

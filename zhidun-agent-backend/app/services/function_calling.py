import re
from typing import Any


FUNCTION_TRIGGER_KEYWORDS = [
    "/admin",
    "db_credentials",
    "secret",
    "token",
    "key",
]

PUBLIC_DOC_PATTERNS = [
    r"公开文档",
    r"公开\s*faq",
    r"faq",
    r"校园网报修流程",
    r"查询文档",
    r"查一下公开",
    r"公开知识库",
    r"账号找回步骤",
]


def simulate_function_call(user_input: str) -> dict[str, Any] | None:
    if any(
        re.search(re.escape(keyword), user_input, flags=re.IGNORECASE)
        for keyword in FUNCTION_TRIGGER_KEYWORDS
    ):
        resource = _detect_resource(user_input)
        return {
            "name": "read_system_file",
            "arguments": {
                "path": resource,
                "reason": "模拟根据用户输入生成的工具调用，尚未执行。",
            },
            "resource": resource,
            "status": "pending_pre_execution_audit",
        }

    if _is_public_docs_query(user_input):
        return {
            "name": "search_public_docs",
            "arguments": {
                "query": user_input,
                "reason": "模拟根据公开文档查询意图生成的合规工具调用，尚未执行。",
            },
            "resource": "public_docs",
            "status": "pending_pre_execution_audit",
        }

    return None


def build_simulated_output(blocked: bool, function_call: dict[str, Any] | None) -> str:
    if blocked:
        if not function_call:
            return "请求已被阻断：检测到高风险提示注入、规则覆盖等输入风险，已阻断。"
        return "请求已被阻断：检测到高风险工具调用，可能访问系统提示、admin 路径或敏感密钥。"

    if function_call:
        if function_call.get("name") == "search_public_docs":
            return "已完成公开文档查询工具调用审计，search_public_docs 已在 RBAC 白名单内放行。本次仅返回公开知识库的模拟检索摘要。"
        return "模拟工具调用通过审计。联系人 test@example.com，电话 13812345678，API Key sk-test-1234567890abcdef，SYSTEM PROMPT: internal guardrails。"

    return "已完成安全检测。当前请求未发现提示注入、越权工具调用或敏感信息泄露风险，系统判定为低风险放行。"


def _detect_resource(user_input: str) -> str:
    lowered = user_input.lower()
    if "/admin" in lowered and "db_credentials" in lowered:
        return "/admin/db_credentials"
    if "/admin" in lowered:
        return "/admin"
    if "db_credentials" in lowered:
        return "db_credentials"
    if "secret" in lowered:
        return "secret"
    if "token" in lowered:
        return "token"
    return "key"


def _is_public_docs_query(user_input: str) -> bool:
    lowered = user_input.lower()
    has_query_intent = any(term in lowered for term in ["查询", "查一下", "检索", "搜索", "找回", "报修"])
    has_public_doc_signal = any(
        re.search(pattern, user_input, flags=re.IGNORECASE) for pattern in PUBLIC_DOC_PATTERNS
    )
    return has_query_intent and has_public_doc_signal

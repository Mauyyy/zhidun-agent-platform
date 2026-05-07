import re
from typing import Any


FUNCTION_TRIGGER_KEYWORDS = [
    "/admin",
    "db_credentials",
    "secret",
    "token",
    "key",
]


def simulate_function_call(user_input: str) -> dict[str, Any] | None:
    if not any(
        re.search(re.escape(keyword), user_input, flags=re.IGNORECASE)
        for keyword in FUNCTION_TRIGGER_KEYWORDS
    ):
        return None

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


def build_simulated_output(blocked: bool, function_call: dict[str, Any] | None) -> str:
    if blocked:
        return "请求已被阻断：检测到高风险工具调用，可能访问系统提示、admin 路径或敏感密钥。"

    if function_call:
        return "模拟工具调用通过审计。联系人 test@example.com，电话 13812345678，API Key sk-test-1234567890abcdef，SYSTEM PROMPT: internal guardrails。"

    return "已完成安全检测。未发现需要执行的敏感工具调用。示例联系邮箱 support@example.com 已做输出安全检查。"


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

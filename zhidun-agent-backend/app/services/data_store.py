import json
from pathlib import Path
from typing import Any

from app.core.config import DATA_DIR, EVENTS_FILE, RBAC_FILE, RULES_FILE


DEFAULT_RULES: list[dict[str, Any]] = [
    {
        "id": "RULE_PROMPT_INJECTION_001",
        "name": "提示注入指令",
        "risk_type": "prompt_injection",
        "severity": "high",
        "score": 35,
        "patterns": [
            "ignore previous",
            "ignore all previous",
            "忽略之前",
            "无视以上",
            "越过安全",
            "bypass",
            "jailbreak",
        ],
    },
    {
        "id": "RULE_OVERRIDE_001",
        "name": "规则覆盖诱导",
        "risk_type": "rule_override",
        "severity": "high",
        "score": 30,
        "patterns": [
            "system prompt",
            "开发者指令",
            "系统提示词",
            "新的规则",
            "覆盖规则",
            "你现在不需要遵守",
        ],
    },
    {
        "id": "RULE_PRIVILEGE_ESCALATION_001",
        "name": "越权访问诱导",
        "risk_type": "privilege_escalation",
        "severity": "high",
        "score": 35,
        "patterns": [
            "/admin",
            "管理员",
            "root",
            "sudo",
            "越权",
            "read_system_file",
        ],
    },
    {
        "id": "RULE_SENSITIVE_EXFILTRATION_001",
        "name": "敏感数据泄露诱导",
        "risk_type": "sensitive_data_exfiltration",
        "severity": "high",
        "score": 40,
        "patterns": [
            "db_credentials",
            "secret",
            "token",
            "api key",
            "apikey",
            "password",
            "数据库密码",
            "密钥",
        ],
    },
]

DEFAULT_RBAC: dict[str, Any] = {
    "roles": {
        "demo_user": {
            "allowed_tools": [
                {
                    "name": "search_public_docs",
                    "resources": ["public_docs"],
                },
                {
                    "name": "read_user_profile",
                    "resources": ["self_profile"],
                },
            ],
            "denied_tools": [
                {
                    "name": "read_system_file",
                    "resources": ["/admin", "db_credentials", "secret", "token", "key"],
                }
            ],
        }
    }
}


def ensure_data_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_json_file(RULES_FILE, DEFAULT_RULES)
    _ensure_json_file(RBAC_FILE, DEFAULT_RBAC)
    _ensure_json_file(EVENTS_FILE, [])


def read_json(path: Path, default: Any) -> Any:
    ensure_data_files()
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        write_json(path, default)
        return default


def write_json(path: Path, payload: Any) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def _ensure_json_file(path: Path, default: Any) -> None:
    if not path.exists():
        write_json(path, default)
        return

    try:
        with path.open("r", encoding="utf-8") as file:
            json.load(file)
    except json.JSONDecodeError:
        write_json(path, default)


import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RULES_FILE = DATA_DIR / "rules.json"
RBAC_FILE = DATA_DIR / "rbac.json"
EVENTS_FILE = DATA_DIR / "events.json"
TEST_CASES_FILE = DATA_DIR / "test_cases.json"

API_PREFIX = "/api/v1"
HIGH_RISK_THRESHOLD = 70
MEDIUM_RISK_THRESHOLD = 40

ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower() or "openai"
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").strip()


def get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def use_real_llm() -> bool:
    return get_bool_env("USE_REAL_LLM", False)


def use_real_tool_call() -> bool:
    return get_bool_env("USE_REAL_TOOL_CALL", False)


def has_openai_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())

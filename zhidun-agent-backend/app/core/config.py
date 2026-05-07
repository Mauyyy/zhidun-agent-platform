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

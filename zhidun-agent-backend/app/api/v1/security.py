from fastapi import APIRouter

from app.core.response import fail, success
from app.schemas.security import EventReportRequest
from app.services.audit_service import create_event_report, get_event, list_events
from app.services.policy_read_service import get_rbac_policy, list_rules, list_test_cases

router = APIRouter()


@router.get("/security/events")
def get_security_events() -> dict:
    return success(
        {
            "items": list_events(),
            "total": len(list_events()),
        }
    )


@router.get("/security/events/{eventId}")
def get_security_event(eventId: str) -> dict:
    event = get_event(eventId)
    if not event:
        return fail("event not found", code=404, data=None)
    return success(event)


@router.get("/security/rules")
def get_security_rules() -> dict:
    return success(list_rules())


@router.get("/security/rbac")
def get_security_rbac() -> dict:
    return success(get_rbac_policy())


@router.get("/security/test-cases")
def get_security_test_cases() -> dict:
    return success(list_test_cases())


@router.post("/security/events/{eventId}/report")
def create_security_event_report(eventId: str, payload: EventReportRequest | None = None) -> dict:
    report = create_event_report(eventId)
    if not report:
        return fail("event not found", code=404, data=None)

    if payload:
        report["operator"] = payload.operator
        report["remark"] = payload.remark

    return success(report)

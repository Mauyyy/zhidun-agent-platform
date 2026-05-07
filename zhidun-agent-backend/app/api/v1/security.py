from fastapi import APIRouter, Query

from app.core.response import fail, success
from app.schemas.security import DesensitizePreviewRequest, EventReportRequest
from app.services.audit_service import (
    create_event_report,
    get_event,
    get_tool_invocation,
    list_events,
    list_tool_invocations,
)
from app.services.desensitizer import desensitize_output
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


@router.get("/security/tool-invocations")
def get_security_tool_invocations(
    page: int = Query(1, ge=1),
    pageSize: int = Query(12, ge=1, le=100),
) -> dict:
    return success(list_tool_invocations(page=page, page_size=pageSize))


@router.get("/security/tool-invocations/{invocationId}")
def get_security_tool_invocation(invocationId: str) -> dict:
    invocation = get_tool_invocation(invocationId)
    if not invocation:
        return fail("tool invocation not found", code=404, data=None)
    return success(invocation)


@router.post("/security/desensitize-preview")
def create_desensitize_preview(payload: DesensitizePreviewRequest) -> dict:
    content = payload.normalized_content()
    if not content:
        return fail("content or text is required", code=400, data=None)

    result = desensitize_output(content)
    return success(
        {
            "original": result["before"],
            "masked": result["after"],
            "changed": result["changed"],
            "redactions": result["redactions"],
            "before": result["before"],
            "after": result["after"],
        }
    )


@router.post("/security/events/{eventId}/report")
def create_security_event_report(eventId: str, payload: EventReportRequest | None = None) -> dict:
    report = create_event_report(eventId)
    if not report:
        return fail("event not found", code=404, data=None)

    if payload:
        report["operator"] = payload.operator
        report["remark"] = payload.remark

    return success(report)

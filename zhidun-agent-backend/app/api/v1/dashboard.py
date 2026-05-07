from fastapi import APIRouter

from app.core.response import success
from app.services.dashboard_service import get_dashboard_overview, get_risk_matrix_summary

router = APIRouter()


@router.get("/dashboard/overview")
def dashboard_overview() -> dict:
    return success(get_dashboard_overview())


@router.get("/dashboard/risk-matrix")
def dashboard_risk_matrix() -> dict:
    return success(get_risk_matrix_summary())

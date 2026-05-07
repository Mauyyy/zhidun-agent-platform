from fastapi import APIRouter

from app.core.response import success

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return success(
        {
            "status": "ok",
            "service": "zhidun-agent-backend",
            "version": "0.1.0",
        }
    )


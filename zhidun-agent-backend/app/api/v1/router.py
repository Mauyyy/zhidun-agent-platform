from fastapi import APIRouter

from app.api.v1 import chat, health, security

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(security.router)


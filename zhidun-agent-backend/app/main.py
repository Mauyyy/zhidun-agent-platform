from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import ALLOWED_ORIGINS, API_PREFIX
from app.core.response import UTF8JSONResponse
from app.services.data_store import ensure_data_files


def create_app() -> FastAPI:
    ensure_data_files()

    app = FastAPI(
        title="智盾Agent Backend",
        description="面向大模型应用的提示注入、工具越权与敏感数据泄露一体化防护最小后端原型",
        version="0.1.0",
        default_response_class=UTF8JSONResponse,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=API_PREFIX)
    return app


app = create_app()

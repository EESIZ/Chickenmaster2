"""FastAPI 앱 팩토리"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from web.config import CORS_ORIGINS
from web.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="치킨마스터2", version="2.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    static_dir = Path(__file__).parent / "static"
    v2_dir = static_dir / "v2"

    # v2 SPA (카드 기반 UI) — /v2 경로 유지 (하위 호환)
    if v2_dir.exists():
        app.mount("/v2", StaticFiles(directory=str(v2_dir), html=True), name="static-v2")

    # v2를 루트(/)로 서빙
    if v2_dir.exists():
        app.mount("/", StaticFiles(directory=str(v2_dir), html=True), name="static-root")

    return app

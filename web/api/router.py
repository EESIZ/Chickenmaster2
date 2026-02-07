"""라우터 통합"""

from fastapi import APIRouter
from web.api.game_router import router as game_router
from web.api.game_router_v2 import router as game_router_v2

api_router = APIRouter()
api_router.include_router(game_router)
api_router.include_router(game_router_v2)

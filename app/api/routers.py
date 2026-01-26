# =============================
# app/api/routers.py
# =============================
from fastapi import APIRouter
from .endpoints import users
from .endpoints import indicators
from .endpoints import majors
from .endpoints import user_manage
from .endpoints import permissions
from .endpoints import evaluation_types

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(indicators.router)
api_router.include_router(majors.router)
api_router.include_router(user_manage.router)
api_router.include_router(permissions.router)
api_router.include_router(evaluation_types.router)

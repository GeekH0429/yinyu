"""聚合所有业务路由。"""
from fastapi import APIRouter

from app.api import admin, articles, auth, daily_image, me, treehole, upload

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(articles.router)
api_router.include_router(treehole.router)
api_router.include_router(daily_image.router)
api_router.include_router(upload.router)
api_router.include_router(admin.router)

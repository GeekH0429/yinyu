"""FastAPI 应用入口。"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401  (确保所有模型被注册到 Base.metadata)
from app.api.router import api_router
from app.config import settings
from app.core.exceptions import AppException
from app.redis_client import redis
from app.startup import bootstrap


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await bootstrap()
    yield
    await redis.aclose()


app = FastAPI(
    title=f"{settings.app_name} API",
    version="0.1.0",
    description="治愈系图文 App 后端(图文阅读 / 树洞 / 我的 / 管理后台)",
    lifespan=lifespan,
)

# CORS
_origins = ["*"] if "*" in settings.cors_origins else settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "detail": exc.detail},
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)

# 开发期:后端直接托管 /uploads/ 静态,方便前端预览上传文件。
# 生产环境由 Nginx 直接代理,不经过 Python,这里仅 dev 生效。
if settings.is_dev:
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)
        app.mount(settings.upload_url_prefix, StaticFiles(directory=settings.upload_dir), name="uploads")
    except OSError:
        # 目录无法创建(如默认 /data/uploads 在某些系统),跳过,不影响 API
        pass


@app.get("/health", tags=["运维"])
async def health():
    return {"status": "ok", "env": settings.app_env}


@app.get("/", tags=["运维"])
async def root():
    return {"app": settings.app_name, "docs": "/docs", "health": "/health"}

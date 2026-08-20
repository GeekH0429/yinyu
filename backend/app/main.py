"""FastAPI 应用入口。"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy import text as sa_text
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401  (确保所有模型被注册到 Base.metadata)
from app.api.router import api_router
from app.config import settings
from app.core.exceptions import AppException
from app.database import AsyncSessionLocal, get_db
from app.logging_config import LOG_NAMESPACE, setup_logging
from app.models.article import STATUS_PUBLISHED, STATUS_SCHEDULED, Article
from app.redis_client import redis
from app.services.email import notify_new_article
from app.services.view_counter import archive_daily_views, flush_pending
from app.startup import bootstrap

logger = logging.getLogger(f"{LOG_NAMESPACE}.main")

# 北京时区(归档任务按 CN_TZ 判断"凌晨")
_CN_TZ = timezone(timedelta(hours=8))


async def _view_flusher():
    """后台任务:每 30 秒把 Redis 中累积的浏览增量批量回写到 DB。"""
    while True:
        await asyncio.sleep(30)
        try:
            async with AsyncSessionLocal() as db:
                await flush_pending(redis, db)
        except Exception:  # noqa: BLE001
            logger.exception("view_flusher failed")


async def _daily_archiver():
    """后台任务:每小时检查一次,在北京时区 01:00~02:00 跑归档。

    归档语义见 `archive_daily_views`。模式选 "每小时轮询" 而非 "算精确 sleep 到下次 01:00":
    - 实现简单,无需处理时钟漂移/系统休眠
    - 归档本身幂等(GETDEL + UPSERT 累加),同小时内重复跑也只跑一次(GETDEL 后取不到值)
    - 趋势统计对几分钟误差不敏感

    服务在 01:xx 时段重启会立即补跑,这是好事(确保不漏归档)。
    """
    while True:
        await asyncio.sleep(3600)
        now_cn = datetime.now(_CN_TZ)
        if now_cn.hour != 1:
            continue
        try:
            async with AsyncSessionLocal() as db:
                n = await archive_daily_views(redis, db)
                if n:
                    logger.info("daily_archiver archived %d days", n)
        except Exception:  # noqa: BLE001
            logger.exception("daily_archiver failed")


async def _article_publisher():
    """后台任务:每 30 秒把到期的定时文章(status='scheduled')置为已发布。

    多 worker(生产 --workers 4)安全性:UPDATE ... WHERE status='scheduled'
    是原子认领 —— 行被 A worker 翻转后其它 worker 的 UPDATE 不再命中,
    RETURNING 只出现在一个进程,天然去重,无需 Redis/PG 锁。
    scheduled_at 同步清 NULL,重启后也不会重复匹配。commit 成功后、邮件
    派发前崩溃最多丢一封邮件(best-effort,可接受)。
    """
    while True:
        await asyncio.sleep(30)
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(
                    update(Article)
                    .where(Article.status == STATUS_SCHEDULED, Article.scheduled_at <= func.now())
                    .values(
                        status=STATUS_PUBLISHED,
                        published_at=func.now(),
                        scheduled_at=None,
                    )
                    .returning(Article.id)
                    .execution_options(synchronize_session=False)
                )
                ids = [r[0] for r in res.all()]
                await db.commit()
            for aid in ids:
                asyncio.create_task(notify_new_article(aid))
            if ids:
                logger.info("article_publisher published %d articles", len(ids))
        except Exception:  # noqa: BLE001
            logger.exception("article_publisher failed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    logger.info("app starting", extra={"env": settings.app_env})
    await bootstrap()
    flusher = asyncio.create_task(_view_flusher())
    archiver = asyncio.create_task(_daily_archiver())
    publisher = asyncio.create_task(_article_publisher())
    yield
    flusher.cancel()
    archiver.cancel()
    publisher.cancel()
    await redis.aclose()
    logger.info("app stopped")


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
@app.get("/health/live", tags=["运维"])
async def health_live():
    """存活探活(LB 最浅探活):恒 200,不查 DB/Redis。"""
    return {"status": "ok", "env": settings.app_env}


@app.get("/health/ready", tags=["运维"])
async def health_ready(db: AsyncSession = Depends(get_db)):
    """就绪探活:DB + Redis 实际探测,失败返回 503。

    供宝塔 LB / 监控系统使用;若探活过于频繁(1s 一次)需注意 DB 压力,
    可在前端加短缓存或降低探活频率。
    """
    try:
        await db.execute(sa_text("SELECT 1"))
    except Exception:
        logger.exception("health ready: DB down")
        return JSONResponse(status_code=503, content={"status": "db_down"})
    try:
        if not await redis.ping():
            raise RuntimeError("redis ping returned falsy")
    except Exception:
        logger.exception("health ready: Redis down")
        return JSONResponse(status_code=503, content={"status": "redis_down"})
    return {"status": "ready"}


@app.get("/", tags=["运维"])
async def root():
    return {"app": settings.app_name, "docs": "/docs", "health": "/health"}

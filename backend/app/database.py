"""异步 SQLAlchemy 引擎与会话工厂。"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# 注意:asyncpg + pool_pre_ping 会在连接检出时触发 do_ping → MissingGreenlet,
# 因此不启用 pre_ping;如需可设 pool_recycle。
engine = create_async_engine(
    settings.database_url,
    echo=settings.is_dev,
    future=True,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖:每请求一个会话,结束自动关闭。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

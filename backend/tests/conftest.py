"""pytest 全局配置。

测试不依赖真实 PG / Redis —— services 层测试用 fakeredis,schema 层测试用
SimpleNamespace 模拟 ORM 对象。需要在导入任何 app.* 模块之前设置环境变量,
因为 `app.config` 在首次 import 时会读取并缓存 Settings。
"""
import os

# 在 app.config 首次 import 前注入最小环境变量(否则 pydantic-settings 校验失败)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@127.0.0.1/test")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://test:test@127.0.0.1/test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-not-for-prod")

import pytest
import fakeredis.aioredis


@pytest.fixture
def fake_redis():
    """每个测试用独立的 fakeredis 实例,互不污染。"""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)

"""时光胶囊 schema。

规则:
    - 封存时 unlock_at 必须晚于当前 10 分钟以上(排除手滑选到过去)。
    - 未到期:任何接口都不回传 content(服务端强制,列表/详情一律置 None)。
"""
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 最短封存时长 / 最长年限
_MIN_AHEAD = timedelta(minutes=10)
_MAX_AHEAD = timedelta(days=365 * 20)


def _ensure_aware(dt: datetime) -> datetime:
    """naive 输入视为本地时区转 UTC(正常前端应发带 offset 的 ISO 8601)。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class CapsuleCreate(BaseModel):
    title: str | None = Field(None, max_length=200)
    content: str = Field(..., min_length=1, max_length=20000)
    unlock_at: datetime

    @field_validator("unlock_at")
    @classmethod
    def _validate_unlock_at(cls, v: datetime) -> datetime:
        v = _ensure_aware(v)
        now = datetime.now(timezone.utc)
        if v <= now + _MIN_AHEAD:
            raise ValueError("开启时间至少要在 10 分钟之后")
        if v > now + _MAX_AHEAD:
            raise ValueError("开启时间太远了,最远 20 年")
        return v

    @field_validator("content")
    @classmethod
    def _validate_content(cls, v: str) -> str:
        # 信件是纯文本:去掉标签形态的内容,防富文本混入(展示端按纯文本渲染)
        import re

        return re.sub(r"<[^>]+>", "", v).strip()


class CapsuleBrief(BaseModel):
    """列表条目:不含 content(无论是否到期,列表一律轻量)。"""
    id: int
    title: str | None = None
    unlock_at: datetime
    is_unlocked: bool = False
    created_at: datetime


class CapsuleOut(CapsuleBrief):
    """详情:已到期才带 content;封存中 content 恒为 None。"""
    content: str | None = None
    sealed: bool = False

    model_config = ConfigDict(from_attributes=True)

"""邀请码 schema(后台管理用)。"""
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class InviteCodeCreate(BaseModel):
    count: int = Field(1, ge=1, le=50, description="一次性生成多少个")
    max_uses: int = Field(1, ge=1, le=10000, description="每个码可注册次数")
    remark: str | None = Field(None, max_length=120)
    expires_at: datetime | None = None


class InviteCodeOut(BaseModel):
    id: int
    code: str
    created_by: int | None = None
    remark: str | None = None
    max_uses: int
    used_count: int
    expires_at: datetime | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InviteCodeBatch(BaseModel):
    items: List[InviteCodeOut]

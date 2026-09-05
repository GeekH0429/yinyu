"""摘抄 schema。"""
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExcerptCreate(BaseModel):
    article_id: int | None = None
    article_title: str = Field("", max_length=200)
    content: str = Field(..., min_length=1, max_length=500)

    @field_validator("content")
    @classmethod
    def _plain_text(cls, v: str) -> str:
        """剥掉可能的标签形态内容(摘抄是纯文本句子,卡片按纯文本渲染)。"""
        return re.sub(r"<[^>]+>", "", v).strip()


class ExcerptOut(BaseModel):
    id: int
    article_id: int | None = None
    article_title: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

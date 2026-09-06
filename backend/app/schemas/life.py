"""人生时光轴 schema。"""
import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class LifeMilestoneCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=40)
    color: str = Field("#C4A882", max_length=9)
    start_date: date
    end_date: date
    site: str | None = Field(None, max_length=60)
    images: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("color")
    @classmethod
    def _hex_color(cls, v: str) -> str:
        if not _HEX_COLOR.fullmatch(v):
            raise ValueError("颜色必须是 #RRGGBB 格式")
        return v.upper()

    @field_validator("images")
    @classmethod
    def _urls(cls, v: list[str]) -> list[str]:
        for u in v:
            if len(u) > 500:
                raise ValueError("图片 URL 过长")
        return v

    @model_validator(mode="after")
    def _date_order(self):
        if self.end_date < self.start_date:
            raise ValueError("结束日期不能早于开始日期")
        return self


class LifeMilestoneUpdate(LifeMilestoneCreate):
    """全量更新(时光轴节点无部分编辑场景,App 端提交整表单)。"""


class LifeMilestoneOut(BaseModel):
    id: int
    label: str
    color: str
    start_date: date
    end_date: date
    site: str | None = None
    images: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class LifeSettingsUpdate(BaseModel):
    birthday: date | None = None
    lifespan_years: int | None = Field(None, ge=1, le=120)

    @field_validator("birthday")
    @classmethod
    def _not_future(cls, v: date | None) -> date | None:
        if v is not None and v > date.today():
            raise ValueError("生日不能晚于今天")
        return v


class CapsuleMarkOut(BaseModel):
    """时光轴上的胶囊落点:只有时间与标题,绝不含 content(服务端强制)。"""

    id: int
    title: str | None = None
    unlock_at: datetime


class ArticleMarkOut(BaseModel):
    """时光轴上的写作足迹:发布过的图文。"""

    id: int
    title: str
    published_at: datetime


class LifeOut(BaseModel):
    """时光轴聚合:设置 + 自定义节点 + 胶囊落点 + 写作足迹,一次拉全。"""

    birthday: date | None = None
    lifespan_years: int = 80
    milestones: list[LifeMilestoneOut] = []
    capsules: list[CapsuleMarkOut] = []
    articles: list[ArticleMarkOut] = []

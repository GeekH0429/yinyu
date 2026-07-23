"""每日一图 schema。"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.daily_image import DailyImage


class DailyImageCreate(BaseModel):
    publish_date: date = Field(..., description="排期日期 YYYY-MM-DD")
    image_url: str = Field(..., min_length=1, max_length=500)
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)


class DailyImageUpdate(BaseModel):
    publish_date: date | None = None
    image_url: str | None = Field(None, min_length=1, max_length=500)
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)


class DailyImageOut(BaseModel):
    id: int
    publish_date: date
    image_url: str
    title: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


def to_out(d: DailyImage) -> DailyImageOut:
    return DailyImageOut.model_validate(d)

"""上传文件 schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MediaOut(BaseModel):
    id: int
    filename: str
    url: str
    mime_type: str
    size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

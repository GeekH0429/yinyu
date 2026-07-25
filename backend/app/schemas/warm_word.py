"""暖话 schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WarmWordOut(BaseModel):
    """单条暖话(随机接口返回)。"""
    id: int
    scene: str
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SceneOut(BaseModel):
    """场景统计(scenes 接口返回,只含 count 不含 text,防搬运)。"""
    scene: str
    label: str  # 中文展示名
    count: int  # 该场景下的暖话条数

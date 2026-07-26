"""暖话 schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WarmWordOut(BaseModel):
    """单条暖话(随机接口返回)。"""
    id: int
    scene: str
    text: str
    created_at: datetime
    is_favorited: bool = False  # 当前登录用户是否已收藏(random 接口注入)

    model_config = ConfigDict(from_attributes=True)


class SceneOut(BaseModel):
    """场景统计(scenes 接口返回,只含 count 不含 text,防搬运)。"""
    scene: str
    label: str  # 中文展示名
    count: int  # 该场景下的暖话条数


class FavoriteOut(BaseModel):
    """暖话收藏列表项(扁平化含暖话内容)。"""
    id: int  # favorite 记录 id
    warm_word_id: int
    scene: str
    text: str
    created_at: datetime  # 收藏时间

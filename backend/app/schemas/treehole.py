"""树洞 schema。

注意区分两种视图:
    - TreeHoleOut       作者本人 / 管理员视角(含 code、author)
    - TreeHolePublicOut 暗号读者视角(全量隐匿,不含 author、不含 code)
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.treehole import CODE_LENGTH


class TreeHoleCreate(BaseModel):
    title: str | None = Field(None, max_length=200)
    content_html: str = ""
    # 传则自定义,不传则系统随机生成
    code: str | None = Field(None, pattern=r"^\d{%d}$" % CODE_LENGTH)


class TreeHoleUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    content_html: str | None = None
    is_active: bool | None = None


class CodeUpdate(BaseModel):
    """刷新 / 自定义暗号。"""
    code: str | None = Field(None, pattern=r"^\d{%d}$" % CODE_LENGTH, description="为空则随机刷新")


class TreeHoleOut(BaseModel):
    """作者 / 管理员视角。"""
    id: int
    title: str | None = None
    content_html: str
    code: str
    is_active: bool
    view_count: int
    echo_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TreeHoleUnlockIn(BaseModel):
    code: str = Field(..., pattern=r"^\d{%d}$" % CODE_LENGTH)


class TreeHolePublicOut(BaseModel):
    """暗号读者视角:全量隐匿,无 author、无 code。
    echo_token:解锁成功时签发的回音令牌(30 分钟有效),回音接口凭它调用。"""
    id: int
    title: str | None = None
    content_html: str
    view_count: int
    echo_token: str | None = None
    created_at: datetime


class EchoCreate(BaseModel):
    """留一枚回音:message 必须命中预设白清单(services/treehole_echo.py)。"""
    echo_token: str = Field(..., min_length=8, max_length=64)
    message: str = Field(..., max_length=30)


class EchoOut(BaseModel):
    """作者视角的回音条目:只有预设短句与时间,无任何读者信息。"""
    id: int
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

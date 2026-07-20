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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TreeHoleUnlockIn(BaseModel):
    code: str = Field(..., pattern=r"^\d{%d}$" % CODE_LENGTH)


class TreeHolePublicOut(BaseModel):
    """暗号读者视角:全量隐匿,无 author、无 code。"""
    id: int
    title: str | None = None
    content_html: str
    view_count: int
    created_at: datetime

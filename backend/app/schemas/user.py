"""用户 schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import ROLE_ADMIN, ROLE_USER


class AuthorBrief(BaseModel):
    """文章 / 树洞里嵌套的作者摘要(不泄露敏感信息)。"""
    id: int
    nickname: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None = None
    nickname: str
    avatar_url: str | None = None
    bio: str | None = None
    role: str = ROLE_USER
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN


class UserUpdate(BaseModel):
    nickname: str | None = Field(None, max_length=40)
    email: EmailStr | None = None
    avatar_url: str | None = Field(None, max_length=500)
    bio: str | None = Field(None, max_length=500)


class AdminUserPatch(BaseModel):
    """后台修改用户(启用/禁用、角色)。"""
    is_active: bool | None = None
    role: str | None = Field(None, pattern=r"^(user|admin)$")
    nickname: str | None = Field(None, max_length=40)

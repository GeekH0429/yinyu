"""通用 schema:分页参数与分页响应。"""
from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(1, ge=1, description="页码,从 1 开始")
    page_size: int = Field(20, ge=1, le=100, description="每页条数")


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size if self.page_size else 0


def offset_of(page: int, page_size: int) -> int:
    return (page - 1) * page_size

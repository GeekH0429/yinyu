"""文章 schema 序列化(to_brief / to_out)测试。

用 SimpleNamespace 模拟 ORM 对象,不依赖真实 DB。pydantic 的
`from_attributes=True` 会按属性读取,SimpleNamespace 完美契合。
"""
from datetime import datetime
from types import SimpleNamespace

from app.schemas.article import to_brief, to_out


def _make_article(**overrides):
    defaults = dict(
        id=1,
        title="标题",
        summary=None,
        cover_url=None,
        tags=None,
        status="published",
        view_count=0,
        like_count=0,
        comment_count=0,
        published_at=None,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 2, 12, 0, 0),
        content_html="<p>hello</p>",
        author_id=1,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_author(**overrides):
    defaults = dict(id=1, nickname="Alice", avatar_url=None)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_to_brief_normalizes_none_tags_to_empty_list():
    """tags=None 时(老数据 / 未设标签)应序列化为 []。"""
    a = _make_article(tags=None)
    brief = to_brief(a, _make_author())
    assert brief.tags == []
    # 序列化通过(默认 dict)
    assert brief.model_dump()["tags"] == []


def test_to_brief_maps_core_fields():
    a = _make_article(
        tags=["治愈", "日记"],
        view_count=10,
        like_count=3,
        comment_count=2,
    )
    brief = to_brief(a, _make_author(nickname="Bob"))
    assert brief.tags == ["治愈", "日记"]
    assert brief.view_count == 10
    assert brief.like_count == 3
    assert brief.comment_count == 2
    assert brief.author.nickname == "Bob"


def test_to_out_includes_content_and_updated():
    a = _make_article(content_html="<p>body</p>")
    out = to_out(a, _make_author())
    assert out.content_html == "<p>body</p>"
    assert out.updated_at == a.updated_at

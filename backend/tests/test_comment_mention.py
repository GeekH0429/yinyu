"""评论 @提及摘要的纯逻辑测试。"""
from app.services.comment_mention import _snippet


def test_snippet_short_text_unchanged():
    assert _snippet("hello") == "hello"


def test_snippet_at_boundary_kept():
    """长度恰等于 n 的文本不截断。"""
    text = "a" * 80
    assert _snippet(text) == text


def test_snippet_long_text_truncated():
    long = "b" * 200
    result = _snippet(long)
    assert len(result) == 80
    assert result.endswith("…")
    assert result[:-1] == "b" * 79

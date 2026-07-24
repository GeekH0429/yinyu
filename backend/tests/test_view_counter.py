"""浏览计数测试(Redis 累积 + 日级去重)。"""
from app.services.view_counter import incr_view


async def test_incr_view_counts_first_visit(fake_redis):
    await incr_view(fake_redis, "article", 1, "user:1")
    cnt = await fake_redis.get("view:cnt:article:1")
    assert cnt == "1"


async def test_incr_view_dedup_same_viewer_same_day(fake_redis):
    """同一 viewer 当天对同一对象只计一次。"""
    kind, item_id, viewer = "article", 42, "user:1"
    for _ in range(5):
        await incr_view(fake_redis, kind, item_id, viewer)

    cnt = await fake_redis.get(f"view:cnt:{kind}:{item_id}")
    assert cnt == "1", "同 viewer 当天应去重,只计一次"


async def test_incr_view_different_viewers_independent(fake_redis):
    await incr_view(fake_redis, "article", 7, "user:1")
    await incr_view(fake_redis, "article", 7, "user:2")
    await incr_view(fake_redis, "article", 7, "ip:10.0.0.1")

    cnt = await fake_redis.get("view:cnt:article:7")
    assert cnt == "3", "不同 viewer 各计一次"

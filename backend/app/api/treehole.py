"""树洞路由。

设计要点:
    - 无列表 / 无标签 / 全量隐匿:不提供任何集合接口给读者。
    - 读者唯一入口:POST /treeholes/unlock 输入 6 位暗号解锁单篇(限流防爆破)。
    - 暗号读者看不到作者、看不到 code(返回 TreeHolePublicOut)。
    - 作者可在"我的"里管理自己的树洞(见 me.py)。
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.core.ownership import get_owned
from app.database import get_db
from app.deps import get_current_user
from app.models.treehole import TreeHole
from app.redis_client import get_redis
from app.schemas.treehole import (
    CodeUpdate,
    TreeHoleCreate,
    TreeHoleOut,
    TreeHolePublicOut,
    TreeHoleUnlockIn,
    TreeHoleUpdate,
)
from app.services.treehole_code import allocate_code, assert_unlock_allowed
from app.services.view_counter import incr_view

router = APIRouter(prefix="/treeholes", tags=["树洞"])


@router.post("/unlock", response_model=TreeHolePublicOut)
async def unlock(
    data: TreeHoleUnlockIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """凭 6 位暗号解锁单篇。无论暗号对错都计入限流,且不回显"存在/不存在"差异。"""
    client_ip = (request.client.host if request.client else "unknown") or "unknown"
    await assert_unlock_allowed(redis, client_ip)

    th = await db.scalar(
        select(TreeHole).where(TreeHole.code == data.code, TreeHole.is_active.is_(True))
    )
    if th is None:
        # 统一文案,不暴露存在性
        raise NotFound("暗号无效")

    await incr_view(redis, "treehole", th.id, "ip:" + client_ip)
    th.view_count = (th.view_count or 0) + 1  # 内存校正(显示用),实际落库由后台回写

    return TreeHolePublicOut(
        id=th.id,
        title=th.title,
        content_html=th.content_html,
        view_count=th.view_count,
        created_at=th.created_at,
    )


@router.post("", response_model=TreeHoleOut, status_code=201)
async def create_treehole(
    data: TreeHoleCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    code = await allocate_code(db, preferred=data.code)
    th = TreeHole(
        author_id=user.id,
        title=data.title,
        content_html=data.content_html,
        code=code,
    )
    db.add(th)
    await db.commit()
    await db.refresh(th)
    return th


@router.put("/{treehole_id}", response_model=TreeHoleOut)
async def update_treehole(
    treehole_id: int,
    data: TreeHoleUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    th = await get_owned(db, TreeHole, treehole_id, user, not_found="树洞不存在", forbidden="只能操作自己的树洞")
    payload = data.model_dump(exclude_unset=True)
    for k, v in payload.items():
        setattr(th, k, v)
    await db.commit()
    await db.refresh(th)
    return th


@router.put("/{treehole_id}/code", response_model=TreeHoleOut)
async def change_code(
    treehole_id: int,
    data: CodeUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """刷新随机暗号(data.code=None)或自定义暗号(data.code="123456")。"""
    th = await get_owned(db, TreeHole, treehole_id, user, not_found="树洞不存在", forbidden="只能操作自己的树洞")
    th.code = await allocate_code(db, preferred=data.code, exclude_id=th.id)
    await db.commit()
    await db.refresh(th)
    return th


@router.delete("/{treehole_id}")
async def delete_treehole(
    treehole_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    th = await get_owned(db, TreeHole, treehole_id, user, not_found="树洞不存在", forbidden="只能操作自己的树洞")
    await db.delete(th)
    await db.commit()
    return {"detail": "已删除"}

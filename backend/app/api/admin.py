"""管理后台路由(仅 admin)。邀请码、用户、内容管理。

路由级 dependencies=[require_admin] 已统一守卫,handler 内只需取当前用户,
不再重复 require_admin。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Conflict, NotFound
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models.article import Article
from app.models.invite import InviteCode
from app.models.treehole import TreeHole
from app.models.user import User
from app.schemas.article import ArticleBrief, to_brief
from app.schemas.common import Page, offset_of
from app.schemas.invite import InviteCodeBatch, InviteCodeCreate, InviteCodeOut
from app.schemas.treehole import TreeHoleOut
from app.schemas.user import AdminUserPatch, UserOut
from app.services.invite_code import generate_invite_code

router = APIRouter(prefix="/admin", tags=["管理后台"], dependencies=[Depends(require_admin)])


@router.post("/invite-codes", response_model=InviteCodeBatch, status_code=201)
async def create_invite_codes(
    data: InviteCodeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    seen: set[str] = set()
    created: list[InviteCode] = []
    for _ in range(data.count):
        # 保证库内 + 本批次内唯一(seen 集合避免 O(N²) 重建)
        for _retry in range(30):
            code = generate_invite_code()
            if code in seen:
                continue
            exists = await db.scalar(select(InviteCode.id).where(InviteCode.code == code))
            if exists is None:
                break
        else:
            raise Conflict("邀请码生成失败,请重试")
        seen.add(code)
        created.append(
            InviteCode(
                code=code,
                created_by=user.id,
                max_uses=data.max_uses,
                remark=data.remark,
                expires_at=data.expires_at,
            )
        )
    db.add_all(created)
    await db.commit()
    # 一次批量取回(带 server_default 字段),替代逐条 refresh
    rows = await db.execute(
        select(InviteCode).where(InviteCode.id.in_([c.id for c in created]))
    )
    items = [InviteCodeOut.model_validate(i) for i in rows.scalars()]
    return InviteCodeBatch(items=items)


@router.get("/invite-codes", response_model=Page[InviteCodeOut])
async def list_invite_codes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total = await db.scalar(select(func.count()).select_from(InviteCode))
    rows = await db.execute(
        select(InviteCode)
        .order_by(InviteCode.created_at.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [InviteCodeOut.model_validate(i) for i in rows.scalars().all()]
    return Page[InviteCodeOut](items=items, total=total or 0, page=page, page_size=page_size)


@router.get("/users", response_model=Page[UserOut])
async def list_users(
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    conds = []
    if keyword:
        like = f"%{keyword}%"
        conds.append(User.username.ilike(like) | User.nickname.ilike(like))
    total = await db.scalar(select(func.count()).select_from(User).where(*conds))
    rows = await db.execute(
        select(User)
        .where(*conds)
        .order_by(User.created_at.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [UserOut.model_validate(u) for u in rows.scalars().all()]
    return Page[UserOut](items=items, total=total or 0, page=page, page_size=page_size)


@router.patch("/users/{user_id}", response_model=UserOut)
async def patch_user(
    user_id: int,
    data: AdminUserPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, user_id)
    if target is None:
        raise NotFound("用户不存在")
    if target.id == user.id and data.is_active is False:
        raise BadRequest("不能禁用自己")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(target, k, v)
    await db.commit()
    await db.refresh(target)
    return target


@router.get("/articles", response_model=Page[ArticleBrief])
async def list_all_articles(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    conds = []
    if status:
        conds.append(Article.status == status)
    total = await db.scalar(select(func.count()).select_from(Article).where(*conds))
    rows = await db.execute(
        select(Article, User)
        .join(User, User.id == Article.author_id)
        .where(*conds)
        .order_by(Article.created_at.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [to_brief(a, u) for a, u in rows.all()]
    return Page[ArticleBrief](items=items, total=total or 0, page=page, page_size=page_size)


@router.get("/treeholes", response_model=Page[TreeHoleOut])
async def list_all_treeholes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total = await db.scalar(select(func.count()).select_from(TreeHole))
    rows = await db.execute(
        select(TreeHole)
        .order_by(TreeHole.created_at.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [TreeHoleOut.model_validate(t) for t in rows.scalars().all()]
    return Page[TreeHoleOut](items=items, total=total or 0, page=page, page_size=page_size)


@router.delete("/treeholes/{treehole_id}")
async def force_delete_treehole(
    treehole_id: int,
    db: AsyncSession = Depends(get_db),
):
    th = await db.get(TreeHole, treehole_id)
    if th is None:
        raise NotFound("树洞不存在")
    await db.delete(th)
    await db.commit()
    return {"detail": "已删除"}

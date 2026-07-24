"""管理后台路由(仅 admin)。邀请码、用户、内容管理。

路由级 dependencies=[require_admin] 已统一守卫,handler 内只需取当前用户,
不再重复 require_admin。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Conflict, NotFound
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models.article import Article
from app.models.comment import Comment
from app.models.daily_image import DailyImage
from app.models.invite import InviteCode
from app.models.treehole import TreeHole
from app.models.user import User
from app.schemas.article import ArticleBrief, to_brief
from app.schemas.comment import CommentOut, to_comment_out
from app.schemas.common import Page, offset_of
from app.schemas.daily_image import (
    DailyImageCreate,
    DailyImageOut,
    DailyImageUpdate,
)
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
    keyword: str | None = Query(None, description="标题/摘要关键词"),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    conds = []
    if status:
        conds.append(Article.status == status)
    if keyword:
        like = f"%{keyword}%"
        conds.append(Article.title.ilike(like) | Article.summary.ilike(like))
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


# ---------- 评论管理 ----------


@router.get("/comments", response_model=Page[CommentOut])
async def admin_list_comments(
    article_id: int | None = Query(None, description="按文章 id 过滤"),
    keyword: str | None = Query(None, description="评论内容关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """管理后台:全部评论,支持按文章/关键词过滤。"""
    conds = []
    if article_id:
        conds.append(Comment.article_id == article_id)
    if keyword:
        conds.append(Comment.content.ilike(f"%{keyword}%"))
    total = await db.scalar(
        select(func.count()).select_from(Comment).where(*conds)
    )
    rows = await db.execute(
        select(Comment, User)
        .join(User, User.id == Comment.author_id)
        .where(*conds)
        .order_by(Comment.created_at.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [to_comment_out(c, u) for c, u in rows.all()]
    return Page[CommentOut](items=items, total=total or 0, page=page, page_size=page_size)


@router.delete("/comments/{comment_id}")
async def admin_delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """管理员强删(级联删子回复 / 点赞 / 关联通知)。"""
    c = await db.get(Comment, comment_id)
    if c is None:
        raise NotFound("评论不存在")
    article_id = c.article_id
    # 删前先数直接子评论(yinyu 只支持一层回复,parent_id 有 ON DELETE CASCADE
    # 会自动级联删除子评论,但 Article.comment_count 需要手动减去对应数量)
    child_count = await db.scalar(
        select(func.count()).select_from(Comment).where(Comment.parent_id == comment_id)
    ) or 0
    await db.delete(c)
    delta = 1 + child_count
    await db.execute(
        sa_update(Article)
        .where(Article.id == article_id, Article.comment_count >= delta)
        .values(comment_count=Article.comment_count - delta)
        .execution_options(synchronize_session=False)
    )
    await db.commit()
    return {"ok": True}


# ---------- 每日一图 ----------


@router.get("/daily-images", response_model=Page[DailyImageOut])
async def list_daily_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """管理后台用:含未来排期,按排期日期倒序。"""
    total = await db.scalar(select(func.count()).select_from(DailyImage))
    rows = await db.execute(
        select(DailyImage)
        .order_by(DailyImage.publish_date.desc(), DailyImage.id.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [DailyImageOut.model_validate(d) for d in rows.scalars().all()]
    return Page[DailyImageOut](
        items=items, total=total or 0, page=page, page_size=page_size
    )


@router.post("/daily-images", response_model=DailyImageOut, status_code=201)
async def create_daily_image(
    data: DailyImageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 唯一性预检:给出友好 409,而不是依赖 IntegrityError
    existed = await db.scalar(
        select(DailyImage.id).where(DailyImage.publish_date == data.publish_date)
    )
    if existed is not None:
        raise Conflict(f"{data.publish_date} 已排期,请先删除或修改原有记录")
    di = DailyImage(
        publish_date=data.publish_date,
        image_url=data.image_url,
        title=data.title,
        description=data.description,
    )
    db.add(di)
    await db.commit()
    await db.refresh(di)
    return di


@router.put("/daily-images/{daily_id}", response_model=DailyImageOut)
async def update_daily_image(
    daily_id: int,
    data: DailyImageUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    di = await db.get(DailyImage, daily_id)
    if di is None:
        raise NotFound("每日一图不存在")
    payload = data.model_dump(exclude_unset=True)
    # 改 publish_date 时再做唯一性预检(排除自身)
    if "publish_date" in payload and payload["publish_date"] != di.publish_date:
        dup = await db.scalar(
            select(DailyImage.id).where(
                DailyImage.publish_date == payload["publish_date"],
                DailyImage.id != daily_id,
            )
        )
        if dup is not None:
            raise Conflict(f"{payload['publish_date']} 已排期")
    for k, v in payload.items():
        setattr(di, k, v)
    await db.commit()
    await db.refresh(di)
    return di


@router.delete("/daily-images/{daily_id}")
async def delete_daily_image(
    daily_id: int,
    db: AsyncSession = Depends(get_db),
):
    di = await db.get(DailyImage, daily_id)
    if di is None:
        raise NotFound("每日一图不存在")
    await db.delete(di)
    await db.commit()
    return {"detail": "已删除"}

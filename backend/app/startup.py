"""启动时初始化:超管账号 + 首个引导邀请码(若不存在)。"""
from sqlalchemy import func, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.invite import InviteCode
from app.models.user import ROLE_ADMIN, User
from app.security import hash_password
from app.services.invite_code import generate_invite_code


async def bootstrap() -> None:
    async with AsyncSessionLocal() as db:
        # 超管
        admin = await db.scalar(select(User).where(User.username == settings.superadmin_username))
        if admin is None:
            admin = User(
                username=settings.superadmin_username,
                password_hash=await hash_password(settings.superadmin_password),
                nickname="管理员",
                role=ROLE_ADMIN,
            )
            db.add(admin)
            await db.commit()
            print(f"[bootstrap] 已创建超管: {settings.superadmin_username}")

        # 引导邀请码(库中无任何码时生成一个,方便首批注册)
        cnt = await db.scalar(select(func.count()).select_from(InviteCode))
        if cnt == 0:
            code = generate_invite_code()
            db.add(InviteCode(code=code, max_uses=10, remark="bootstrap"))
            await db.commit()
            print(f"[bootstrap] 已生成引导邀请码: {code}  (max_uses=10)")

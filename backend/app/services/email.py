"""邮件通知服务。

设计要点(参 CLAUDE.md):
  - 全程 async(aiosmtplib),绝不阻塞事件循环。
  - 三层降级:smtp_enabled=False / smtp_host 空 → 整体 no-op;
    收件人 email 为空 → skip;email_notify_enabled=False → skip(调用方校验)。
  - 任何异常只记日志,**永不抛** —— 邮件失败绝不能影响评论接口。
  - 调用方应在 db.commit() 成功后用 asyncio.create_task(...) 派发,避免回滚后误发。

对外两个函数:
  - send_email(to, subject, html_body):通用底层发送。
  - notify_interaction_email(...):按互动类型组装中文文案后发送。
  - notify_new_article(article_id):文章发布后给订阅用户群发通知。
"""
from __future__ import annotations

import html
import logging
from email.message import EmailMessage
from typing import Literal

import aiosmtplib
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.article import Article
from app.models.user import User

logger = logging.getLogger(__name__)

InteractionKind = Literal["comment", "reply", "mention"]


async def send_email(to: str, subject: str, html_body: str) -> None:
    """发送一封 HTML 邮件。失败仅记日志,不抛。"""
    if not settings.smtp_enabled or not settings.smtp_host:
        logger.warning("SMTP 未配置,跳过发送邮件 to=%s subject=%r", to, subject)
        return
    if not to:
        return

    from_addr = settings.smtp_from or settings.smtp_user
    if not from_addr:
        logger.error("SMTP_FROM 与 SMTP_USER 都为空,无法发送邮件")
        return

    sender_display = f"{settings.smtp_sender_name} <{from_addr}>" if settings.smtp_sender_name else from_addr

    msg = EmailMessage()
    msg["From"] = sender_display
    msg["To"] = to
    msg["Subject"] = subject
    # 纯文本兜底(老客户端 / 纯文本预览友好),HTML 为主
    msg.set_content(_strip_tags_fallback(html_body))
    msg.add_alternative(html_body, subtype="html")

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password=settings.smtp_password or None,
            use_tls=settings.smtp_use_tls,          # SSL: True 直接 TLS
            start_tls=not settings.smtp_use_tls,    # STARTTLS: 先明文再升级
            timeout=20,
        )
        logger.info("邮件已发送 to=%s subject=%r", to, subject)
    except Exception as e:  # noqa: BLE001 - 邮件失败不能影响业务
        logger.warning("发送邮件失败 to=%s subject=%r err=%s", to, subject, e)


async def notify_interaction_email(
    *,
    recipient_email: str,
    recipient_nickname: str,
    actor_nickname: str,
    article_title: str,
    content_preview: str,
    kind: InteractionKind,
) -> None:
    """按互动类型组装中文标题/正文后发送。

    kind 取自 Notification.type("comment" / "reply" / "mention")。
    """
    actor = html.escape(actor_nickname or "某位同学")
    nick = html.escape(recipient_nickname or "你")
    title = html.escape(article_title or "一篇文章")
    preview = html.escape(content_preview or "")

    if kind == "comment":
        subject = f"{actor_nickname} 评论了你的文章《{article_title}》"
        headline = f"<b>{actor}</b> 评论了你的文章《{title}》"
    elif kind == "reply":
        subject = f"{actor_nickname} 回复了你的评论"
        headline = f"<b>{actor}</b> 在《{title}》下回复了你的评论"
    elif kind == "mention":
        subject = f"{actor_nickname} 在评论中提到了你"
        headline = f"<b>{actor}</b> 在《{title}》的评论中提到了你"
    else:
        return  # 防御性:未知类型不发

    body = f"""\
<div style="font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;
            max-width:560px;margin:0 auto;padding:24px;color:#3a3a3a;line-height:1.6;">
  <p style="margin:0 0 12px;">嗨,{nick},</p>
  <p style="margin:0 0 16px;font-size:15px;">{headline}</p>
  <blockquote style="margin:0 0 16px;padding:12px 16px;background:#fdfbf7;
                   border-left:3px solid #c4a882;color:#5a5a5a;font-size:14px;
                   border-radius:4px;">
    {preview or '(空评论)'}
  </blockquote>
  <p style="margin:0;font-size:13px;color:#999;">
    —— 来自 yinyu,一个治愈的角落
  </p>
</div>
"""
    await send_email(recipient_email, subject, body)


def _strip_tags_fallback(html_body: str) -> str:
    """粗略去标签,作为纯文本 alternative。

    邮件正文是受控 HTML(我们自己拼),用最小实现就够。
    """
    import re

    text = re.sub(r"<[^>]+>", "", html_body)
    text = html.unescape(text)
    return text.strip()


async def notify_new_article(article_id: int) -> None:
    """文章发布后,给订阅「新文章推送」的用户群发邮件。

    调用时机(均在 db.commit() 成功之后):
      - api/articles.py 立即发布 / scheduled 转发布
      - main.py _article_publisher 定时到期翻转
    只接收纯值 article_id,自开会话查最新数据;收件人 = 开启订阅且
    绑定邮箱的用户(排除作者本人)。任何异常只记日志,永不抛。
    """
    try:
        if not settings.smtp_enabled or not settings.smtp_host:
            return
        async with AsyncSessionLocal() as db:
            row = (
                await db.execute(
                    select(Article.title, Article.summary, Article.author_id, User.nickname)
                    .join(User, User.id == Article.author_id)
                    .where(Article.id == article_id)
                )
            ).first()
            if row is None:
                return
            title, summary, author_id, author_nickname = row
            if not title:
                return
            recipients = (
                (
                    await db.execute(
                        select(User.email).where(
                            User.article_notify_enabled.is_(True),
                            User.email.is_not(None),
                            User.id != author_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
        if not recipients:
            return

        actor = html.escape(author_nickname or "某位同学")
        art_title = html.escape(title)
        art_summary = html.escape((summary or "").strip())
        subject = f"{author_nickname} 发布了新文章《{title}》"
        summary_html = (
            f'<blockquote style="margin:0 0 16px;padding:12px 16px;background:#fdfbf7;'
            f'border-left:3px solid #c4a882;color:#5a5a5a;font-size:14px;'
            f'border-radius:4px;">{art_summary}</blockquote>'
            if art_summary
            else ""
        )
        body = f"""\
<div style="font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;
            max-width:560px;margin:0 auto;padding:24px;color:#3a3a3a;line-height:1.6;">
  <p style="margin:0 0 12px;">嗨,</p>
  <p style="margin:0 0 16px;font-size:15px;"><b>{actor}</b> 发布了新文章《{art_title}》</p>
  {summary_html}
  <p style="margin:0;font-size:13px;color:#999;">
    —— 来自 yinyu,一个治愈的角落
  </p>
</div>
"""
        for to in recipients:
            await send_email(to, subject, body)
        logger.info("new article notify sent article_id=%s recipients=%d", article_id, len(recipients))
    except Exception:  # noqa: BLE001 - 邮件失败不能影响发布流程
        logger.exception("notify_new_article failed article_id=%s", article_id)

"""文件上传路由:存到本地 /data/uploads/,按日期分目录。

部署后由 Nginx 直接代理 `UPLOAD_URL_PREFIX`(默认 /uploads/)到磁盘目录,
后端不参与静态文件下载。
"""
import os
import pathlib
import uuid
from datetime import datetime, timezone

import aiofiles
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import BadRequest
from app.database import get_db
from app.deps import get_current_user
from app.models.media import Media
from app.schemas.media import MediaOut

router = APIRouter(prefix="/upload", tags=["上传"])

_ALLOWED = set(settings.allowed_mimes)
_MAX_BYTES = settings.max_upload_mb * 1024 * 1024
_CHUNK = 1024 * 1024  # 1MB / 块,流式读写,避免整文件入内存 + 阻塞事件循环


@router.post("", response_model=MediaOut, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mime = (file.content_type or "").lower()
    if mime not in _ALLOWED:
        raise BadRequest(f"不支持的文件类型: {mime or '未知'}")

    ext = pathlib.Path(file.filename or "").suffix.lower()[:10]
    name = f"{uuid.uuid4().hex}{ext}"
    date_dir = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    save_dir = os.path.join(settings.upload_dir, date_dir)
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, name)

    # 分块流式落盘(异步),边写边累计大小,超限即终止并清理
    size = 0
    oversize = False
    async with aiofiles.open(save_path, "wb") as f:
        while True:
            chunk = await file.read(_CHUNK)
            if not chunk:
                break
            size += len(chunk)
            if size > _MAX_BYTES:
                oversize = True
                break
            await f.write(chunk)

    if size == 0:
        os.remove(save_path)
        raise BadRequest("文件为空")
    if oversize:
        os.remove(save_path)
        raise BadRequest(f"文件过大,最大 {settings.max_upload_mb}MB")

    rel = os.path.relpath(save_path, settings.upload_dir).replace("\\", "/")
    url = f"{settings.upload_url_prefix.rstrip('/')}/{rel}"

    media = Media(
        uploader_id=user.id,
        filename=name,
        url=url,
        mime_type=mime,
        size_bytes=size,
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media

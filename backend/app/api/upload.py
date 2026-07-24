"""文件上传路由:存到本地 /data/uploads/,按日期分目录。

部署后由 Nginx 直接代理 `UPLOAD_URL_PREFIX`(默认 /uploads/)到磁盘目录,
后端不参与静态文件下载。
"""
import asyncio
import io
import os
import uuid
from datetime import datetime, timezone

import aiofiles
from fastapi import APIRouter, Depends, File, UploadFile
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import BadRequest
from app.core.filetype import MIME_TO_EXT, detect_mime
from app.database import get_db
from app.deps import get_current_user
from app.models.media import Media
from app.schemas.media import MediaOut

router = APIRouter(prefix="/upload", tags=["上传"])

_ALLOWED = set(settings.allowed_mimes)
_MAX_BYTES = settings.max_upload_mb * 1024 * 1024
_CHUNK = 1024 * 1024  # 1MB / 块,流式读写,避免整文件入内存 + 阻塞事件循环


def _save_image(src: io.BytesIO, save_dir: str, mime: str) -> tuple[str, int, str]:
    """图片压缩为 webp(最大边 1280 / 质量 82)落盘;gif 或处理失败则原样保留。

    接收已做完大小检查的 BytesIO,内部按需 seek(0) 二次读取
    (Pillow 失败时 fallback 路径需重新读全量字节)。
    """
    stem = uuid.uuid4().hex
    try:
        if mime == "image/gif":
            raise ValueError("gif 保留原样")
        src.seek(0)
        img = Image.open(src)
        img.load()
        img = img.convert("RGBA")
        if max(img.size) > 1280:
            img.thumbnail((1280, 1280))
        name = f"{stem}.webp"
        img.save(os.path.join(save_dir, name), "WEBP", quality=82, method=4)
        return name, os.path.getsize(os.path.join(save_dir, name)), "image/webp"
    except Exception:
        # gif(避免丢动画)/ 损坏图 / 不支持的图:原样落盘,保留原格式
        src.seek(0)
        data = src.read()
        name = f"{stem}{MIME_TO_EXT.get(mime, '')}"
        with open(os.path.join(save_dir, name), "wb") as f:
            f.write(data)
        return name, len(data), mime


@router.post("", response_model=MediaOut, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 读文件头判定真实类型(不信任 content_type / 扩展名,杜绝 .html 等同源可执行上传)
    head = await file.read(32)
    await file.seek(0)
    mime = detect_mime(head)
    if mime is None or mime not in _ALLOWED:
        raise BadRequest("不支持的文件类型")

    date_dir = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    save_dir = os.path.join(settings.upload_dir, date_dir)
    os.makedirs(save_dir, exist_ok=True)

    if mime.startswith("image/"):
        # 图片:分块流式读到 BytesIO,边读边累计,超限即拒
        # (不在循环外 await file.read() 整文件入内存 —— CLAUDE.md 明令禁止)
        buf = io.BytesIO()
        size = 0
        oversize = False
        while True:
            chunk = await file.read(_CHUNK)
            if not chunk:
                break
            size += len(chunk)
            if size > _MAX_BYTES:
                oversize = True
                break
            buf.write(chunk)
        if size == 0:
            raise BadRequest("文件为空")
        if oversize:
            raise BadRequest(f"文件过大,最大 {settings.max_upload_mb}MB")
        name, size, mime = await asyncio.to_thread(_save_image, buf, save_dir, mime)
    else:
        # 音视频:分块流式落盘,边写边累计大小,超限即终止并清理
        name = f"{uuid.uuid4().hex}{MIME_TO_EXT.get(mime, '')}"
        save_path = os.path.join(save_dir, name)
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

    rel = os.path.relpath(os.path.join(save_dir, name), settings.upload_dir).replace("\\", "/")
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

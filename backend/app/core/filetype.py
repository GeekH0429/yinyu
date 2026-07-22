"""基于文件头签名判定真实 MIME 类型。

不信任客户端提交的 content_type / 扩展名(均可伪造),
只覆盖本服务允许上传的格式(见 config.Settings.allowed_mimes)。
未命中任何签名 → 返回 None,由调用方拒绝(安全默认),从而杜绝
`.html` / `.svg` 等同源可执行内容上传后被 Nginx 当 text/html 执行的存储型 XSS。
"""
from __future__ import annotations

# 检测到的 MIME → 落盘扩展名(由真实类型决定,不接受用户提供的扩展名)
MIME_TO_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-m4a": ".m4a",
    "audio/aac": ".aac",
    "audio/flac": ".flac",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
    "video/mp4": ".mp4",
}


def detect_mime(head: bytes) -> str | None:
    """根据文件头前若干字节判定 MIME;未命中返回 None。"""
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "audio/wav"
    if head.startswith(b"OggS"):
        return "audio/ogg"
    if head.startswith(b"fLaC"):
        return "audio/flac"
    if head.startswith(b"ID3") or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"\xff\xfa"):
        return "audio/mpeg"
    if head[:2] in (b"\xff\xf1", b"\xff\xf9"):
        return "audio/aac"
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return "audio/webm"  # EBML(WebM/MKV);尊重白名单的 audio/webm
    if head[4:8] == b"ftyp":  # ISO BMFF:MP4 家族,品牌区分音/视频
        brand = head[8:12]
        if brand[:3] == b"M4A" or brand in (b"M4B ", b"M4P ", b"M4V "):
            return "audio/x-m4a"
        return "video/mp4"
    return None

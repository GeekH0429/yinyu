"""为存量上传图片补生成 `_s` 缩略档(一次性运维脚本,幂等)。

背景:上传管线(`app/api/upload.py` 的 `_save_image`)为最大边 >800 的图同时生成
`{stem}_s.webp` 缩略档,App 列表封面按文件名约定直接引用(`app/src/config/index.js`
的 `thumbUrl`)。本脚本为历史文件补齐同样的约定:同目录、扩展名前插 `_s`、保持原格式。

用法(backend 目录下,与后端相同的 Python 环境):
    python -m scripts.backfill_thumbs --dir /data/uploads           # 预览(dry-run)
    python -m scripts.backfill_thumbs --dir /data/uploads --apply   # 实际写盘

跳过:gif(动图不缩)、已有缩略档(幂等)、最大边 <=800 的图(App 端直接用原图)。
"""

import argparse
import os

from PIL import Image

THUMB_MAX_SIDE = 800  # 与 app/api/upload.py 的 _THUMB_MAX_SIDE 保持一致
THUMB_QUALITY = 78

# 缩略档保持原格式(文件名约定决定);JPEG 不支持 alpha,需转 RGB
FORMAT_BY_EXT = {".webp": "WEBP", ".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG"}


def make_thumb(path: str, root: str, apply: bool) -> str | None:
    """为单张图生成缩略档,返回一行结果描述;不满足条件的返回 None。"""
    stem, ext = os.path.splitext(path)
    ext = ext.lower()
    fmt = FORMAT_BY_EXT.get(ext)
    if not fmt:
        return None  # 非图片 / gif:跳过
    out = stem + "_s" + ext
    if os.path.exists(out):
        return None  # 幂等:已有缩略档
    rel = os.path.relpath(path, root)
    with Image.open(path) as im:
        im.load()
        w, h = im.size
        if max(w, h) <= THUMB_MAX_SIDE:
            return None  # 原图已够小:App 端直接用原图
        if not apply:
            return f"[dry-run] {rel}"
        scale = THUMB_MAX_SIDE / max(w, h)
        thumb = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    if fmt == "JPEG" and thumb.mode != "RGB":
        thumb = thumb.convert("RGB")
    thumb.save(out, fmt, quality=THUMB_QUALITY, method=4)
    return f"{rel} -> {os.path.relpath(out, root)} ({os.path.getsize(out) // 1024}KB)"


def main() -> None:
    ap = argparse.ArgumentParser(description="为存量上传图片补生成 _s 缩略档")
    ap.add_argument("--dir", default="/data/uploads", help="上传根目录(默认 /data/uploads)")
    ap.add_argument("--apply", action="store_true", help="实际写盘(默认 dry-run 只预览)")
    args = ap.parse_args()

    root = os.path.abspath(args.dir)
    if not os.path.isdir(root):
        raise SystemExit(f"目录不存在: {root}")

    generated, errors = 0, 0
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if os.path.splitext(name)[0].endswith("_s"):
                continue  # 缩略档自身,避免再生成 abc_s_s.webp
            path = os.path.join(dirpath, name)
            try:
                msg = make_thumb(path, root, args.apply)
                if msg:
                    print(msg)
                    generated += 1
            except Exception as e:  # noqa: BLE001 —— 单文件失败(损坏图等)不中断整体
                errors += 1
                print(f"[error] {os.path.relpath(path, root)}: {e}", flush=True)

    mode = "已生成" if args.apply else "将生成(dry-run)"
    print(f"\n完成:{mode} {generated} 张,失败 {errors} 张。")
    if not args.apply and generated:
        print("加 --apply 实际写盘。")


if __name__ == "__main__":
    main()

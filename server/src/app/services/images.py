"""图片存储服务：原图落盘、缩略图生成、元数据读写。

存储布局：
    data/uploads/<album_id>/<image_id>.<ext>            原图
    data/uploads/<album_id>/<image_id>.thumb.webp       缩略图（预览条使用）

原图按上传时的字节原样保存，不做二次编码，避免损失画质；
缩略图统一转成 WebP，体积小且文字边缘比 JPEG 干净。
"""

import contextlib
import io
import uuid
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import get_settings
from app.core.db import get_conn
from app.core.errors import NotFoundError, ValidationError
from app.services.common import now_iso

# Pillow 识别出的格式 -> 落盘扩展名 / MIME
FORMAT_INFO: dict[str, tuple[str, str]] = {
    "PNG": ("png", "image/png"),
    "JPEG": ("jpg", "image/jpeg"),
    "WEBP": ("webp", "image/webp"),
    "GIF": ("gif", "image/gif"),
    "BMP": ("bmp", "image/bmp"),
    "TIFF": ("tiff", "image/tiff"),
}


# ---------------------------------------------------------------- 路径工具


def album_dir(album_id: str) -> Path:
    return get_settings().uploads_dir / album_id


def _original_path(album_id: str, stored_name: str) -> Path:
    return album_dir(album_id) / stored_name


def _thumb_path(album_id: str, thumb_name: str) -> Path:
    return album_dir(album_id) / thumb_name


# ---------------------------------------------------------------- 读写


def _row_to_dict(row) -> dict:
    """补上前端直接可用的 url / thumb_url，省得前端拼接口路径。"""
    settings = get_settings()
    base = settings.api_v1_prefix
    data = dict(row)
    data["url"] = f"{base}/images/{data['id']}/file"
    data["thumb_url"] = f"{base}/images/{data['id']}/thumb"
    return data


def get_image(image_id: str) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"图片不存在：{image_id}")
    return _row_to_dict(row)


def original_path_of(image_id: str) -> Path:
    row = _raw_row(image_id)
    return _original_path(row["album_id"], row["stored_name"])


def thumbnail_path_of(image_id: str) -> Path:
    row = _raw_row(image_id)
    if not row["thumb_name"]:
        raise NotFoundError("该图片没有缩略图")
    return _thumb_path(row["album_id"], row["thumb_name"])


def _raw_row(image_id: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"图片不存在：{image_id}")
    return row


def list_album_images(album_id: str) -> list[dict]:
    """按上传时间升序返回图集内所有图片。"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM images WHERE album_id = ? ORDER BY created_at ASC, rowid ASC",
            (album_id,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


# ---------------------------------------------------------------- 写入


def save_image(album_id: str, filename: str, data: bytes) -> dict:
    """校验并保存一张图片，返回元数据。

    `filename` 仅用于展示（保留用户原始文件名），真实存储名用新生成的 UUID。
    """
    settings = get_settings()

    if not data:
        raise ValidationError("上传内容为空")

    if len(data) > settings.max_image_bytes:
        limit_mb = settings.max_image_bytes / 1024 / 1024
        raise ValidationError(f"图片体积超过上限 {limit_mb:.0f}MB")

    try:
        parsed = Image.open(io.BytesIO(data))
        parsed.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValidationError(f"「{filename}」不是有效的图片文件") from exc

    fmt = (parsed.format or "").upper()
    if fmt not in FORMAT_INFO:
        raise ValidationError(f"「{filename}」的格式不受支持（识别为 {fmt or '未知'}）")
    ext, mime = FORMAT_INFO[fmt]

    # 手机截图常带 EXIF 旋转标记：以「旋转后」的尺寸为准，
    # 与浏览器渲染原图时的显示尺寸一致，批注坐标才不会错位。
    upright = ImageOps.exif_transpose(parsed) or parsed
    width, height = upright.size

    image_id = uuid.uuid4().hex
    stored_name = f"{image_id}.{ext}"
    thumb_name = _make_thumbnail(upright, image_id, album_id)

    target = album_dir(album_id)
    target.mkdir(parents=True, exist_ok=True)
    try:
        (target / stored_name).write_bytes(data)
    except OSError as exc:
        raise ValidationError(f"「{filename}」写入磁盘失败：{exc}") from exc

    created_at = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO images
                (id, album_id, original_name, stored_name, thumb_name,
                 mime, size, width, height, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                image_id,
                album_id,
                filename or stored_name,
                stored_name,
                thumb_name,
                mime,
                len(data),
                width,
                height,
                created_at,
            ),
        )

    return get_image(image_id)


def _make_thumbnail(source: Image.Image, image_id: str, album_id: str) -> str:
    """生成缩略图并返回文件名；失败时不阻断上传（返回空串）。"""
    max_side = get_settings().thumbnail_max_side
    try:
        thumb = source.copy()
        thumb.thumbnail((max_side, max_side), Image.LANCZOS)

        # 统一铺白底：透明 PNG 的截图放在深色主题上不至于糊成一团
        if thumb.mode in ("RGBA", "LA", "P"):
            rgba = thumb.convert("RGBA")
            canvas = Image.new("RGB", rgba.size, (255, 255, 255))
            canvas.paste(rgba, mask=rgba.split()[-1])
            thumb = canvas
        elif thumb.mode != "RGB":
            thumb = thumb.convert("RGB")

        target = album_dir(album_id)
        target.mkdir(parents=True, exist_ok=True)

        name = f"{image_id}.thumb.webp"
        try:
            thumb.save(target / name, "WEBP", quality=88, method=4)
        except (OSError, ValueError):
            # 个别 Pillow 构建不带 WebP 编码器，退回 JPEG 保证功能可用
            name = f"{image_id}.thumb.jpg"
            thumb.save(target / name, "JPEG", quality=88)
        return name
    except Exception:  # noqa: BLE001 - 缩略图属可选优化，失败就降级用原图
        return ""


# ---------------------------------------------------------------- 删除


def delete_image(image_id: str) -> None:
    row = _raw_row(image_id)
    with get_conn() as conn:
        conn.execute("DELETE FROM images WHERE id = ?", (image_id,))

    directory = album_dir(row["album_id"])
    for name in (row["stored_name"], row["thumb_name"]):
        if name:
            # 文件已不在磁盘上时不影响元数据清理
            with contextlib.suppress(OSError):
                (directory / name).unlink(missing_ok=True)


def delete_album_files(album_id: str) -> None:
    """删除图集目录下的所有图片文件（数据库级联由调用方负责）。"""
    import shutil

    shutil.rmtree(album_dir(album_id), ignore_errors=True)

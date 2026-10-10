"""图集服务。"""

import uuid

from app.core.config import get_settings
from app.core.db import get_conn
from app.core.errors import NotFoundError
from app.schemas.album import AlbumCreate, AlbumUpdate
from app.services import images
from app.services.common import now_iso, truncate_to_minute

# 列表页需要封面与图片数量，用两个子查询一次带出来，避免 N+1 请求
_ALBUM_SELECT = """
SELECT
    a.*,
    (SELECT COUNT(*) FROM images i WHERE i.album_id = a.id) AS image_count,
    (SELECT i.id FROM images i
      WHERE i.album_id = a.id
      ORDER BY i.created_at ASC, i.rowid ASC
      LIMIT 1) AS cover_image_id
FROM albums a
"""


def _decorate(album: dict) -> dict:
    """补上封面地址，前端可直接用于 <img src>。"""
    base = get_settings().api_v1_prefix
    cover = album.get("cover_image_id")
    album["cover_url"] = f"{base}/images/{cover}/file" if cover else None
    album["cover_thumb_url"] = f"{base}/images/{cover}/thumb" if cover else None
    return album


def list_albums() -> list[dict]:
    """按交易时间倒序返回全部图集（时间相同再按创建时间倒序）。"""
    with get_conn() as conn:
        rows = conn.execute(
            _ALBUM_SELECT + " ORDER BY a.trade_time DESC, a.created_at DESC"
        ).fetchall()
    return [_decorate(dict(row)) for row in rows]


def get_album(album_id: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(_ALBUM_SELECT + " WHERE a.id = ?", (album_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"图集不存在：{album_id}")
    return _decorate(dict(row))


def create_album(payload: AlbumCreate) -> dict:
    album_id = uuid.uuid4().hex
    stamp = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO albums (id, symbol, trade_time, title, note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                album_id,
                payload.symbol.strip(),
                truncate_to_minute(payload.trade_time).isoformat(),
                payload.title.strip(),
                payload.note.strip(),
                stamp,
                stamp,
            ),
        )
    return get_album(album_id)


def update_album(album_id: str, payload: AlbumUpdate) -> dict:
    existing = get_album(album_id)
    changes = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not changes:
        return existing

    if "trade_time" in changes:
        changes["trade_time"] = truncate_to_minute(changes["trade_time"]).isoformat()
    for text_field in ("symbol", "title", "note"):
        if text_field in changes:
            changes[text_field] = changes[text_field].strip()

    changes["updated_at"] = now_iso()
    assignments = ", ".join(f"{column} = ?" for column in changes)
    with get_conn() as conn:
        conn.execute(
            f"UPDATE albums SET {assignments} WHERE id = ?",  # noqa: S608 - 列名来自固定白名单
            (*changes.values(), album_id),
        )
    return get_album(album_id)


def delete_album(album_id: str) -> None:
    """删除图集：先清磁盘文件，再删数据库记录（images/annotations 级联删除）。"""
    get_album(album_id)
    images.delete_album_files(album_id)
    with get_conn() as conn:
        conn.execute("DELETE FROM albums WHERE id = ?", (album_id,))

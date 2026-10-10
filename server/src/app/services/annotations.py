"""批注服务。

核心约束：**序号（seq）在同一个图集内跨所有图片统一编号**，从 1 开始连续。
新增时取「当前图集最大序号 + 1」；删除后重新压实，保证编号不出现空洞。
"""

import uuid

from app.core.db import get_conn
from app.core.errors import NotFoundError, ValidationError
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate
from app.services.common import now_iso


def list_album_annotations(album_id: str) -> list[dict]:
    """按序号升序返回图集内全部批注。"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM annotations WHERE album_id = ? ORDER BY seq ASC",
            (album_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_annotation(annotation_id: str) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM annotations WHERE id = ?", (annotation_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"批注不存在：{annotation_id}")
    return dict(row)


def create_annotation(album_id: str, payload: AnnotationCreate) -> dict:
    # 图片必须存在，且确实属于这个图集
    with get_conn() as conn:
        owner = conn.execute(
            "SELECT album_id FROM images WHERE id = ?", (payload.image_id,)
        ).fetchone()
        if owner is None:
            raise NotFoundError(f"图片不存在：{payload.image_id}")
        if owner["album_id"] != album_id:
            raise ValidationError("该图片不属于当前图集")

        next_seq = conn.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 AS seq FROM annotations WHERE album_id = ?",
            (album_id,),
        ).fetchone()["seq"]

        annotation_id = uuid.uuid4().hex
        conn.execute(
            """
            INSERT INTO annotations
                (id, album_id, image_id, kind, seq, x, y, w, h, text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                annotation_id,
                album_id,
                payload.image_id,
                payload.kind,
                next_seq,
                payload.x,
                payload.y,
                # 点批注不保留跨度；矩形保留带符号的 w/h，使 (x, y) 恒为拖拽起点
                payload.w if payload.kind == "rect" else 0.0,
                payload.h if payload.kind == "rect" else 0.0,
                payload.text.strip(),
                now_iso(),
            ),
        )

    return get_annotation(annotation_id)


def update_annotation(annotation_id: str, payload: AnnotationUpdate) -> dict:
    existing = get_annotation(annotation_id)
    changes = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not changes:
        return existing

    if "text" in changes:
        changes["text"] = changes["text"].strip()
    # 点批注没有矩形，避免写入无意义的宽高
    if existing["kind"] == "point":
        changes.pop("w", None)
        changes.pop("h", None)

    assignments = ", ".join(f"{column} = ?" for column in changes)
    with get_conn() as conn:
        conn.execute(
            f"UPDATE annotations SET {assignments} WHERE id = ?",  # noqa: S608 - 列名来自固定白名单
            (*changes.values(), annotation_id),
        )
    return get_annotation(annotation_id)


def delete_annotation(annotation_id: str) -> None:
    existing = get_annotation(annotation_id)
    with get_conn() as conn:
        conn.execute("DELETE FROM annotations WHERE id = ?", (annotation_id,))
        _compact_sequence(conn, existing["album_id"])


def delete_image_annotations(image_id: str) -> None:
    """删除某张图片的全部批注，并把该图集的序号重新压实。

    由删除图片的接口调用，保证「统一序号」不会出现断号。
    """
    with get_conn() as conn:
        row = conn.execute("SELECT album_id FROM images WHERE id = ?", (image_id,)).fetchone()
        if row is None:
            return
        conn.execute("DELETE FROM annotations WHERE image_id = ?", (image_id,))
        _compact_sequence(conn, row["album_id"])


def _compact_sequence(conn, album_id: str) -> None:
    """把图集内的批注序号按原顺序重新编号为 1..N。"""
    rows = conn.execute(
        "SELECT id FROM annotations WHERE album_id = ? ORDER BY seq ASC, created_at ASC",
        (album_id,),
    ).fetchall()
    for index, row in enumerate(rows, start=1):
        conn.execute("UPDATE annotations SET seq = ? WHERE id = ?", (index, row["id"]))

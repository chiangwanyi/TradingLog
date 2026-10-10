"""轻量键值偏好存储。

只保存纯 UI 偏好（目前是批注调色板的「最近使用颜色」）。
用 preferences 表存 `key -> JSON 字符串`，不为几个偏好单独建结构化表。

设计要点：**读时容错**。偏好数据即使被写坏也不该让界面崩掉，
所以解析失败的策略是「当作空列表」，而不是抛异常。
"""

import json
import re

from app.core.db import get_conn
from app.services.common import now_iso

RECENT_COLORS_KEY = "annotation_recent_colors"
# 调色板一行放得下的数量，超出后挤掉最久未使用的
MAX_RECENT_COLORS = 12

_HEX_RE = re.compile(r"^#[0-9a-f]{6}$")


def get_recent_colors() -> list[str]:
    return _parse_colors(_read(RECENT_COLORS_KEY))


def remember_color(color: str) -> list[str]:
    """把颜色排到最近使用列表的最前（去重 + 截断），返回更新后的列表。

    颜色非法时不做任何写入，直接返回现有列表 —— 接口层已经用 pattern 拦过一道，
    这里再挡一次是为了防止绕过接口直接调服务。
    """
    normalized = (color or "").strip().lower()
    if not _HEX_RE.match(normalized):
        return get_recent_colors()

    recent = [normalized]
    recent.extend(item for item in get_recent_colors() if item != normalized)

    recent = recent[:MAX_RECENT_COLORS]
    _write(RECENT_COLORS_KEY, json.dumps(recent))
    return recent


# ---------------------------------------------------------------- 内部工具


def _parse_colors(raw: str | None) -> list[str]:
    """容错解析存下来的 JSON 数组；非法内容一律视为空。"""
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []

    if not isinstance(data, list):
        return []

    result: list[str] = []
    for item in data:
        color = str(item).strip().lower()
        if _HEX_RE.match(color) and color not in result:
            result.append(color)
    return result[:MAX_RECENT_COLORS]


def _read(key: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM preferences WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def _write(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO preferences (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, value, now_iso()),
        )

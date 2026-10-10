"""`init_db()` 的轻量列迁移测试。

表结构以 `db.SCHEMA` 为唯一事实来源，但 `CREATE TABLE IF NOT EXISTS`
不会给已存在的表补列，所以 `_migrate()` 必须能把旧库升级上来 ——
这是「改动数据库结构」里最容易悄悄出错的一环，单独测。
"""

import sqlite3

import pytest

from app.core.config import get_settings
from app.core.db import get_conn, init_db

# 加 color 列之前的结构
LEGACY_ANNOTATIONS = """
CREATE TABLE annotations (
    id         TEXT PRIMARY KEY,
    album_id   TEXT NOT NULL,
    image_id   TEXT NOT NULL,
    kind       TEXT NOT NULL,
    seq        INTEGER NOT NULL,
    x          REAL NOT NULL,
    y          REAL NOT NULL,
    w          REAL NOT NULL DEFAULT 0,
    h          REAL NOT NULL DEFAULT 0,
    text       TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
"""


@pytest.fixture
def legacy_data_dir(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """准备一个「旧版本数据库」并把应用指向它，退出时恢复原数据目录。"""
    data_dir = tmp_path / "legacy-data"
    data_dir.mkdir()

    raw = sqlite3.connect(data_dir / "tradinglog.db")
    raw.executescript(LEGACY_ANNOTATIONS)
    raw.execute(
        "INSERT INTO annotations VALUES "
        "('a1', 'al', 'im', 'point', 1, 0.1, 0.2, 0, 0, '旧数据', '2026-01-01T09:00:00')"
    )
    raw.commit()
    raw.close()

    with monkeypatch.context() as patch:
        patch.setenv("DATA_DIR", str(data_dir))
        get_settings.cache_clear()
        yield data_dir

    # 退出 monkeypatch 后 env 已还原，清缓存让后续测试重新按原目录建配置
    get_settings.cache_clear()


def test_init_db_adds_color_column_and_keeps_existing_rows(legacy_data_dir) -> None:
    init_db()

    with get_conn() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(annotations)")}
        row = conn.execute("SELECT * FROM annotations WHERE id = 'a1'").fetchone()

    assert "color" in columns
    # 老数据完好，新列取默认空串（前端会回落到默认强调色）
    assert row["text"] == "旧数据"
    assert row["color"] == ""


def test_init_db_is_idempotent(legacy_data_dir) -> None:
    # 连续跑三次不应因「列已存在」而报错
    init_db()
    init_db()
    init_db()

    with get_conn() as conn:
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(annotations)")]
    # 也不能把 color 列加重复
    assert columns.count("color") == 1

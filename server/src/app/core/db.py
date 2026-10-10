"""SQLite 存储层。

只做两件事：管理连接、建立表结构。业务读写逻辑放在 `app.services` 下。

为什么用标准库 `sqlite3` 而不用 ORM：
本项目的元数据只有三张表、查询也很简单，标准库足以胜任，且不引入额外依赖。
图片本身以文件形式落盘（见 `app.services.images`），数据库只存元数据。
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.core.config import get_settings

# 表结构：albums（图集）-> images（图片）-> annotations（批注）
# 时间统一以 ISO 8601 字符串存储，字典序即时间序，可直接用于 ORDER BY。
# 批注坐标 (x, y, w, h) 全部是相对图片的归一化值（0~1），
# 这样缩放 / 换分辨率显示时批注位置不会漂移。
SCHEMA = """
CREATE TABLE IF NOT EXISTS albums (
    id          TEXT PRIMARY KEY,
    symbol      TEXT NOT NULL,
    trade_time  TEXT NOT NULL,
    title       TEXT NOT NULL DEFAULT '',
    note        TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS images (
    id            TEXT PRIMARY KEY,
    album_id      TEXT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    original_name TEXT NOT NULL DEFAULT '',
    stored_name   TEXT NOT NULL,
    thumb_name    TEXT NOT NULL DEFAULT '',
    mime          TEXT NOT NULL,
    size          INTEGER NOT NULL,
    width         INTEGER NOT NULL DEFAULT 0,
    height        INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_images_album ON images(album_id, created_at);

CREATE TABLE IF NOT EXISTS annotations (
    id         TEXT PRIMARY KEY,
    album_id   TEXT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    image_id   TEXT NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    kind       TEXT NOT NULL CHECK (kind IN ('point', 'rect')),
    seq        INTEGER NOT NULL,
    x          REAL NOT NULL,
    y          REAL NOT NULL,
    w          REAL NOT NULL DEFAULT 0,
    h          REAL NOT NULL DEFAULT 0,
    text       TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_annotations_album ON annotations(album_id, seq);
CREATE INDEX IF NOT EXISTS idx_annotations_image ON annotations(image_id, seq);
"""


def init_db() -> None:
    """建表（幂等），并确保数据目录存在。应用启动时调用一次。"""
    settings = get_settings()
    settings.ensure_dirs()
    with get_conn() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """按请求获取一个连接，退出时自动提交 / 回滚并关闭。

    同步的 FastAPI 接口跑在线程池里，每次调用独立开连接是最省心也最安全的做法；
    开启 WAL 后并发读写不会互相阻塞。
    """
    settings = get_settings()
    settings.ensure_dirs()

    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

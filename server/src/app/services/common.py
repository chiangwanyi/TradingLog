"""服务层共用的小工具。"""

from datetime import datetime


def now_iso() -> str:
    """当前时间（本地时区、微秒精度）的 ISO 字符串。

    用字符串而非 datetime 落库，是因为 ISO 8601 的字典序与时间序一致，
    ORDER BY 可以直接生效，也不需要额外的序列化适配。
    """
    return datetime.now().isoformat(timespec="microseconds")


def truncate_to_minute(value: datetime) -> datetime:
    """把时间截断到分钟 —— 交易时间只要求精确到分。"""
    return value.replace(second=0, microsecond=0)


def row_to_dict(row) -> dict:
    """sqlite3.Row -> dict。"""
    return dict(row)

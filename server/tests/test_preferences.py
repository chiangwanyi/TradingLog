"""批注「最近使用颜色」偏好的接口测试。"""

import pytest
from fastapi.testclient import TestClient

API = "/api/v1"
ENDPOINT = f"{API}/preferences/annotation-colors"


@pytest.fixture(autouse=True)
def clean_preferences(client: TestClient) -> None:
    """偏好是全局状态，而 client 夹具是整个会话共用一个库。

    因此每个用例前先清空 preferences 表，否则「最近使用」会跨用例累积。
    依赖 client 形参是为了确保会话级夹具（含临时数据目录）已经初始化。
    """
    from app.core.db import get_conn

    with get_conn() as conn:
        conn.execute("DELETE FROM preferences")


def test_recent_colors_starts_empty(client: TestClient) -> None:
    assert client.get(ENDPOINT).json() == {"recent": []}


def test_remember_color_puts_latest_first(client: TestClient) -> None:
    assert client.post(ENDPOINT, json={"color": "#ef4444"}).json()["recent"] == ["#ef4444"]
    assert client.post(ENDPOINT, json={"color": "#3b82f6"}).json()["recent"] == [
        "#3b82f6",
        "#ef4444",
    ]

    # 重新用回旧颜色时它应当被提到最前，而不是产生重复项
    assert client.post(ENDPOINT, json={"color": "#ef4444"}).json()["recent"] == [
        "#ef4444",
        "#3b82f6",
    ]
    assert client.get(ENDPOINT).json()["recent"] == ["#ef4444", "#3b82f6"]


def test_remember_color_normalizes_case(client: TestClient) -> None:
    client.post(ENDPOINT, json={"color": "#A855F7"})
    # 统一小写存储，大小写不同的同一个颜色不会算作两条
    assert client.post(ENDPOINT, json={"color": "#a855f7"}).json()["recent"] == ["#a855f7"]


def test_recent_colors_is_capped_and_drops_oldest(client: TestClient) -> None:
    colors = [f"#{index:02x}{index:02x}{index:02x}" for index in range(1, 16)]

    latest: list[str] = []
    for color in colors:
        latest = client.post(ENDPOINT, json={"color": color}).json()["recent"]

    assert len(latest) == 12
    # 最近 12 个，倒序排列；最早用的 3 个被挤掉
    assert latest == list(reversed(colors[-12:]))
    assert colors[0] not in latest


def test_remember_color_rejects_invalid_value(client: TestClient) -> None:
    assert client.post(ENDPOINT, json={"color": "red"}).status_code == 422
    assert client.post(ENDPOINT, json={"color": "#fff"}).status_code == 422
    # 非法请求不应污染已存的数据
    assert client.get(ENDPOINT).json() == {"recent": []}

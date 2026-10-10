"""交易截图相册的接口测试：图集 / 图片 / 批注 全链路。"""

import io

from fastapi.testclient import TestClient
from PIL import Image

API = "/api/v1"


def make_image(
    size: tuple[int, int] = (160, 100), color: tuple[int, int, int] = (200, 30, 30)
) -> bytes:
    """生成一张真实可解析的 PNG，用于上传测试。"""
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "PNG")
    return buffer.getvalue()


def create_album(client: TestClient, **overrides) -> dict:
    payload = {
        "symbol": "000001 平安银行",
        "trade_time": "2026-10-09T09:31:45",
        "title": "早盘",
        "note": "",
    }
    payload.update(overrides)
    response = client.post(f"{API}/albums", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def upload(client: TestClient, album_id: str, names: list[str]) -> dict:
    files = [("files", (name, make_image(), "image/png")) for name in names]
    response = client.post(f"{API}/albums/{album_id}/images", files=files)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_album_truncates_trade_time_to_minute(client: TestClient) -> None:
    album = create_album(client)

    assert album["image_count"] == 0
    assert album["cover_image_id"] is None
    assert album["symbol"] == "000001 平安银行"
    # 交易时间精确到分钟：秒与微秒被截掉
    assert album["trade_time"] == "2026-10-09T09:31:00"


def test_list_albums_is_sorted_by_trade_time_desc(client: TestClient) -> None:
    create_album(client, symbol="早", trade_time="2026-10-01T09:30:00")
    create_album(client, symbol="晚", trade_time="2026-10-03T14:00:00")

    albums = client.get(f"{API}/albums").json()
    symbols = [item["symbol"] for item in albums]

    assert symbols.index("晚") < symbols.index("早")


def test_update_and_delete_album(client: TestClient) -> None:
    album = create_album(client)

    patched = client.patch(f"{API}/albums/{album['id']}", json={"symbol": "600519 贵州茅台"})
    assert patched.status_code == 200
    assert patched.json()["symbol"] == "600519 贵州茅台"

    assert client.delete(f"{API}/albums/{album['id']}").status_code == 204
    assert client.get(f"{API}/albums/{album['id']}").status_code == 404


def test_upload_images_and_serve_them(client: TestClient) -> None:
    album = create_album(client)
    result = upload(client, album["id"], ["a.png", "b.png"])

    assert result["failed"] == []
    assert len(result["saved"]) == 2

    first = result["saved"][0]
    assert first["width"] == 160
    assert first["height"] == 100
    assert first["original_name"] == "a.png"

    original = client.get(first["url"])
    assert original.status_code == 200
    assert original.headers["content-type"] == "image/png"

    thumbnail = client.get(first["thumb_url"])
    assert thumbnail.status_code == 200
    assert thumbnail.headers["content-type"] in {"image/webp", "image/jpeg"}
    assert len(thumbnail.content) > 0

    # 列表页的封面与计数应当同步更新
    listed = next(item for item in client.get(f"{API}/albums").json() if item["id"] == album["id"])
    assert listed["image_count"] == 2
    assert listed["cover_image_id"] == result["saved"][0]["id"]


def test_upload_response_matches_album_detail_image_shape(client: TestClient) -> None:
    """回归：上传接口返回的图片结构必须与图集详情里的完全一致。

    前端会把上传返回的图片直接 push 进图集的图片列表，之后在这张图上画批注时
    会执行 `image.annotations.push(...)`。早期上传接口返回的是不含 annotations
    的 ImageRead，导致新上传的图片一画批注就抛
    `Cannot read properties of undefined (reading 'push')`（刷新后才正常）。
    """
    album = create_album(client)
    saved = upload(client, album["id"], ["1.png"])["saved"][0]

    # 新图片必然还没有批注，但字段本身必须存在
    assert saved["annotations"] == []

    detail_image = client.get(f"{API}/albums/{album['id']}").json()["images"][0]
    assert set(saved) == set(detail_image)

    # 紧接着画批注应当成功，并且出现在详情里
    created = client.post(
        f"{API}/albums/{album['id']}/annotations",
        json={"image_id": saved["id"], "kind": "point", "x": 0.3, "y": 0.4},
    )
    assert created.status_code == 201

    refreshed = client.get(f"{API}/albums/{album['id']}").json()["images"][0]["annotations"]
    assert [item["id"] for item in refreshed] == [created.json()["id"]]


def test_upload_rejects_non_image_without_breaking_batch(client: TestClient) -> None:
    album = create_album(client)
    files = [
        ("files", ("good.png", make_image(), "image/png")),
        ("files", ("bad.png", b"this is not an image", "image/png")),
    ]

    response = client.post(f"{API}/albums/{album['id']}/images", files=files)
    assert response.status_code == 201
    body = response.json()

    assert len(body["saved"]) == 1
    assert len(body["failed"]) == 1
    assert body["failed"][0]["name"] == "bad.png"


def test_images_are_sorted_by_upload_time(client: TestClient) -> None:
    album = create_album(client)
    upload(client, album["id"], ["1.png"])
    upload(client, album["id"], ["2.png"])

    detail = client.get(f"{API}/albums/{album['id']}").json()
    names = [image["original_name"] for image in detail["images"]]

    assert names == ["1.png", "2.png"]


def test_annotation_seq_is_shared_across_images(client: TestClient) -> None:
    album = create_album(client)
    images = upload(client, album["id"], ["1.png", "2.png"])["saved"]
    album_id = album["id"]

    point = client.post(
        f"{API}/albums/{album_id}/annotations",
        json={"image_id": images[0]["id"], "kind": "point", "x": 0.25, "y": 0.4, "text": "放量"},
    )
    assert point.status_code == 201
    assert point.json()["seq"] == 1

    rect = client.post(
        f"{API}/albums/{album_id}/annotations",
        json={
            "image_id": images[1]["id"],
            "kind": "rect",
            "x": 0.1,
            "y": 0.1,
            "w": 0.5,
            "h": 0.3,
            "text": "",
        },
    )
    assert rect.status_code == 201
    # 跨图片但序号连续，这是「同一图集共用一套序号」的核心约束
    assert rect.json()["seq"] == 2

    # 点批注不应带上矩形尺寸
    assert point.json()["w"] == 0
    assert point.json()["h"] == 0


def test_rect_annotation_keeps_drag_origin_and_signed_span(client: TestClient) -> None:
    """向左上拖拽时 w/h 为负，(x, y) 必须始终是拖拽起点（序号落点）。"""
    album = create_album(client)
    image = upload(client, album["id"], ["1.png"])["saved"][0]

    response = client.post(
        f"{API}/albums/{album['id']}/annotations",
        json={
            "image_id": image["id"],
            "kind": "rect",
            "x": 0.8,
            "y": 0.7,
            "w": -0.4,
            "h": -0.3,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert (body["x"], body["y"]) == (0.8, 0.7)
    assert (body["w"], body["h"]) == (-0.4, -0.3)


def test_annotation_requires_image_in_same_album(client: TestClient) -> None:
    album_a = create_album(client, symbol="A")
    album_b = create_album(client, symbol="B")
    other_image = upload(client, album_b["id"], ["b.png"])["saved"][0]

    response = client.post(
        f"{API}/albums/{album_a['id']}/annotations",
        json={"image_id": other_image["id"], "kind": "point", "x": 0.1, "y": 0.1},
    )

    assert response.status_code == 400


def test_update_and_delete_annotation_recompacts_sequence(client: TestClient) -> None:
    album = create_album(client)
    image = upload(client, album["id"], ["1.png"])["saved"][0]
    album_id = album["id"]

    created = [
        client.post(
            f"{API}/albums/{album_id}/annotations",
            json={"image_id": image["id"], "kind": "point", "x": 0.1 * i, "y": 0.1, "text": ""},
        ).json()
        for i in range(1, 4)
    ]
    assert [item["seq"] for item in created] == [1, 2, 3]

    updated = client.patch(f"{API}/annotations/{created[0]['id']}", json={"text": "这里是买点"})
    assert updated.status_code == 200
    assert updated.json()["text"] == "这里是买点"

    assert client.delete(f"{API}/annotations/{created[0]['id']}").status_code == 204

    remaining = client.get(f"{API}/albums/{album_id}").json()["images"][0]["annotations"]
    # 删掉 1 号后，剩下的应重排为 1、2，不留空洞
    assert [item["seq"] for item in remaining] == [1, 2]


def test_deleting_image_removes_its_annotations(client: TestClient) -> None:
    album = create_album(client)
    images = upload(client, album["id"], ["1.png", "2.png"])["saved"]
    album_id = album["id"]

    client.post(
        f"{API}/albums/{album_id}/annotations",
        json={"image_id": images[0]["id"], "kind": "point", "x": 0.5, "y": 0.5},
    )
    client.post(
        f"{API}/albums/{album_id}/annotations",
        json={"image_id": images[1]["id"], "kind": "point", "x": 0.5, "y": 0.5},
    )

    assert client.delete(f"{API}/images/{images[0]['id']}").status_code == 204

    detail = client.get(f"{API}/albums/{album_id}").json()
    assert len(detail["images"]) == 1
    remaining = detail["images"][0]["annotations"]
    assert len(remaining) == 1
    # 原 2 号被压实成 1 号
    assert remaining[0]["seq"] == 1
    assert client.get(f"{API}/images/{images[0]['id']}/file").status_code == 404

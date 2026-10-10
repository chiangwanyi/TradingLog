"""图集接口：列表、新建、详情、修改、删除，以及图片上传。"""

from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.core.config import get_settings
from app.core.errors import ValidationError
from app.schemas.album import AlbumCreate, AlbumDetail, AlbumRead, AlbumUpdate
from app.schemas.image import ImageUploadResult, UploadFailure
from app.services import albums as album_service
from app.services import annotations as annotation_service
from app.services import images as image_service

router = APIRouter(prefix="/albums", tags=["albums"])


@router.get("", response_model=list[AlbumRead], summary="图集列表（按交易时间倒序）")
def list_albums() -> list[dict]:
    return album_service.list_albums()


@router.post(
    "",
    response_model=AlbumRead,
    status_code=status.HTTP_201_CREATED,
    summary="新建图集",
)
def create_album(payload: AlbumCreate) -> dict:
    return album_service.create_album(payload)


@router.get("/{album_id}", response_model=AlbumDetail, summary="图集详情（含图片与批注）")
def get_album(album_id: str) -> dict:
    album = album_service.get_album(album_id)
    images = image_service.list_album_images(album_id)

    # 一次取出图集内全部批注，按图片归组，避免逐图查询
    grouped: dict[str, list[dict]] = defaultdict(list)
    for annotation in annotation_service.list_album_annotations(album_id):
        grouped[annotation["image_id"]].append(annotation)

    for image in images:
        image["annotations"] = grouped.get(image["id"], [])

    album["images"] = images
    return album


@router.patch("/{album_id}", response_model=AlbumRead, summary="修改图集信息")
def update_album(album_id: str, payload: AlbumUpdate) -> dict:
    return album_service.update_album(album_id, payload)


@router.delete(
    "/{album_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除图集（连同图片与批注）",
)
def delete_album(album_id: str) -> None:
    album_service.delete_album(album_id)


@router.post(
    "/{album_id}/images",
    response_model=ImageUploadResult,
    status_code=status.HTTP_201_CREATED,
    summary="上传图片（支持多张，单张失败不影响其它）",
)
def upload_images(album_id: str, files: Annotated[list[UploadFile], File()]) -> dict:
    """批量上传截图。

    返回结构里区分 saved / failed：一批里混进了非图片文件时，
    只有那一个文件被跳过，其余仍然入库，前端可以把失败原因提示给用户。
    """
    album_service.get_album(album_id)

    # 只读到「上限 + 1」字节，超限的由服务层拒绝，避免把超大文件整读进内存
    read_limit = get_settings().max_image_bytes + 1

    saved: list[dict] = []
    failed: list[UploadFailure] = []

    for upload in files:
        name = upload.filename or "screenshot"
        try:
            payload = upload.file.read(read_limit)
        except OSError as exc:
            failed.append(UploadFailure(name=name, reason=f"读取失败：{exc}"))
            continue
        try:
            saved.append(image_service.save_image(album_id, name, payload))
        except ValidationError as exc:
            failed.append(UploadFailure(name=name, reason=exc.message))
        finally:
            upload.file.close()

    return {"saved": saved, "failed": failed}

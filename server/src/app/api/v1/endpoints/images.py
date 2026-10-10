"""图片接口：原图 / 缩略图读取与删除。"""

from pathlib import Path

from fastapi import APIRouter, status
from fastapi.responses import FileResponse

from app.core.errors import NotFoundError
from app.services import annotations as annotation_service
from app.services import images as image_service

router = APIRouter(prefix="/images", tags=["images"])

# 图片以 UUID 命名、内容永不变化，可以放心长缓存
_IMMUTABLE = {"Cache-Control": "public, max-age=31536000, immutable"}


def _serve(path: Path, media_type: str) -> FileResponse:
    if not path.is_file():
        raise NotFoundError("图片文件已丢失")
    return FileResponse(path, media_type=media_type, headers=_IMMUTABLE)


@router.get("/{image_id}/file", summary="读取原图")
def read_original(image_id: str) -> FileResponse:
    image = image_service.get_image(image_id)
    return _serve(image_service.original_path_of(image_id), image["mime"])


@router.get("/{image_id}/thumb", summary="读取缩略图（缺缩略图时回退原图）")
def read_thumbnail(image_id: str) -> FileResponse:
    image = image_service.get_image(image_id)
    try:
        path = image_service.thumbnail_path_of(image_id)
    except NotFoundError:
        # 生成缩略图失败时降级返回原图，功能不中断
        return _serve(image_service.original_path_of(image_id), image["mime"])
    media_type = "image/webp" if path.suffix == ".webp" else "image/jpeg"
    return _serve(path, media_type)


@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除图片（连同其批注，并重排图集序号）",
)
def delete_image(image_id: str) -> None:
    # 先清批注并压实序号，再删图片本身（图片删除会级联带走剩余批注）
    annotation_service.delete_image_annotations(image_id)
    image_service.delete_image(image_id)

"""批注接口：新增、修改文字、删除。

序号在服务层统一分配，接口不暴露 seq 的写入能力。
"""

from fastapi import APIRouter, status

from app.schemas.annotation import AnnotationCreate, AnnotationRead, AnnotationUpdate
from app.services import annotations as annotation_service

router = APIRouter(tags=["annotations"])


@router.post(
    "/albums/{album_id}/annotations",
    response_model=AnnotationRead,
    status_code=status.HTTP_201_CREATED,
    summary="在图集内新增批注（自动分配统一序号）",
)
def create_annotation(album_id: str, payload: AnnotationCreate) -> dict:
    return annotation_service.create_annotation(album_id, payload)


@router.patch(
    "/annotations/{annotation_id}",
    response_model=AnnotationRead,
    summary="修改批注（文字说明或几何位置）",
)
def update_annotation(annotation_id: str, payload: AnnotationUpdate) -> dict:
    return annotation_service.update_annotation(annotation_id, payload)


@router.delete(
    "/annotations/{annotation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除批注（删除后重排序号）",
)
def delete_annotation(annotation_id: str) -> None:
    annotation_service.delete_annotation(annotation_id)

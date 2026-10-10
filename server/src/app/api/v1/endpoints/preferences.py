"""UI 偏好接口：批注调色板的「最近使用颜色」。"""

from fastapi import APIRouter

from app.schemas.preference import ColorUsage, RecentAnnotationColors
from app.services import preferences as preference_service

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get(
    "/annotation-colors",
    response_model=RecentAnnotationColors,
    summary="批注调色板的最近使用颜色（最近优先）",
)
def get_recent_annotation_colors() -> dict:
    return {"recent": preference_service.get_recent_colors()}


@router.post(
    "/annotation-colors",
    response_model=RecentAnnotationColors,
    summary="记录一次颜色使用（排到最前，去重并截断）",
)
def remember_annotation_color(payload: ColorUsage) -> dict:
    return {"recent": preference_service.remember_color(payload.color)}

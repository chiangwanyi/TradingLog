"""请求 / 响应数据模型（Pydantic）。"""

from app.schemas.album import AlbumCreate, AlbumRead, AlbumUpdate
from app.schemas.annotation import AnnotationCreate, AnnotationRead, AnnotationUpdate
from app.schemas.image import ImageRead

__all__ = [
    "AlbumCreate",
    "AlbumRead",
    "AlbumUpdate",
    "AnnotationCreate",
    "AnnotationRead",
    "AnnotationUpdate",
    "ImageRead",
]

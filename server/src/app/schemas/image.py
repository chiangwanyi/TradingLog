"""图片响应模型。"""

from datetime import datetime

from pydantic import BaseModel

from app.schemas.annotation import AnnotationRead


class ImageRead(BaseModel):
    """图片元数据。

    `url` / `thumb_url` 由后端拼好，前端直接拿去做 <img src>，
    避免前端硬编码接口路径。
    """

    id: str
    album_id: str
    original_name: str = ""
    mime: str
    size: int
    width: int = 0
    height: int = 0
    created_at: datetime
    url: str
    thumb_url: str


class ImageDetail(ImageRead):
    """图集详情里返回的图片，带上自己的批注。"""

    annotations: list[AnnotationRead] = []


class UploadFailure(BaseModel):
    """单个文件上传失败的原因（批量上传时不影响其它文件）。"""

    name: str
    reason: str


class ImageUploadResult(BaseModel):
    saved: list[ImageRead] = []
    failed: list[UploadFailure] = []

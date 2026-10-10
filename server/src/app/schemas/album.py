"""图集相关的请求 / 响应模型。"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.image import ImageDetail


class AlbumCreate(BaseModel):
    """新建图集：交易时间 + 标的为必填。"""

    symbol: str = Field(..., min_length=1, max_length=64, description="标的，如 000001 平安银行")
    trade_time: datetime = Field(..., description="交易时间，精确到分钟")
    title: str = Field("", max_length=128, description="可选标题")
    note: str = Field("", max_length=2000, description="可选备注")


class AlbumUpdate(BaseModel):
    """更新图集：只传需要改的字段。"""

    symbol: str | None = Field(None, min_length=1, max_length=64)
    trade_time: datetime | None = None
    title: str | None = Field(None, max_length=128)
    note: str | None = Field(None, max_length=2000)


class AlbumRead(BaseModel):
    """图集列表项。"""

    id: str
    symbol: str
    trade_time: datetime
    title: str = ""
    note: str = ""
    created_at: datetime
    updated_at: datetime
    # 附加统计：列表页展示封面与图片数量，避免逐图集再发一次请求
    image_count: int = 0
    cover_image_id: str | None = None
    # 封面地址由后端拼好，前端不硬编码接口路径
    cover_url: str | None = None
    cover_thumb_url: str | None = None


class AlbumDetail(AlbumRead):
    """图集详情：一次返回全部图片及其批注，前端只需一次请求。"""

    images: list[ImageDetail] = []

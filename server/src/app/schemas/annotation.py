"""批注相关的请求 / 响应模型。

坐标系约定：所有几何量都是**相对图片的归一化值**（0~1），原点在左上角。
  - 点批注：只用 (x, y)
  - 矩形批注：(x, y) 就是**拖拽起点**，也就是序号图标所在的位置；
    (w, h) 是相对起点、**带符号**的宽高 —— 向左上拖时 w/h 为负。
    这样序号始终落在「单击起点」，与需求一致，而矩形范围用
    `min(x, x+w)` 起、`|w| × |h|` 大小即可还原。
无论图片以多大尺寸显示，批注都能精确落回原位。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AnnotationCreate(BaseModel):
    image_id: str = Field(..., description="所在图片")
    kind: Literal["point", "rect"] = Field(..., description="批注类型")
    x: float = Field(..., ge=0, le=1, description="相对图片左边缘的位置")
    y: float = Field(..., ge=0, le=1, description="相对图片上边缘的位置")
    w: float = Field(0, ge=-1, le=1, description="矩形相对起点的横向跨度（带符号），点批注为 0")
    h: float = Field(0, ge=-1, le=1, description="矩形相对起点的纵向跨度（带符号），点批注为 0")
    text: str = Field("", max_length=2000, description="文字说明")


class AnnotationUpdate(BaseModel):
    """更新批注：主要用于改文字说明；也允许微调几何。"""

    text: str | None = Field(None, max_length=2000)
    x: float | None = Field(None, ge=0, le=1)
    y: float | None = Field(None, ge=0, le=1)
    w: float | None = Field(None, ge=-1, le=1)
    h: float | None = Field(None, ge=-1, le=1)


class AnnotationRead(BaseModel):
    id: str
    album_id: str
    image_id: str
    kind: Literal["point", "rect"]
    # seq 在同一图集内跨图片统一编号，从 1 开始连续
    seq: int
    x: float
    y: float
    w: float
    h: float
    text: str = ""
    created_at: datetime

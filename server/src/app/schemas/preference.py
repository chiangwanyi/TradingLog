"""UI 偏好相关的请求 / 响应模型。

偏好与业务数据分开：它们是「界面怎么显示」而不是「记录了什么」，
所以统一挂在 /preferences 下，用一张 key/value 表保存。
"""

from pydantic import BaseModel, Field

from app.schemas.annotation import HEX_COLOR


class RecentAnnotationColors(BaseModel):
    """批注调色板的「最近使用颜色」，最近用过的排在最前。"""

    recent: list[str] = []


class ColorUsage(BaseModel):
    """记录一次颜色使用。"""

    color: str = Field(..., pattern=f"^{HEX_COLOR}$", description="本次使用的颜色 #rrggbb")

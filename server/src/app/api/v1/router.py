"""v1 路由汇总。

新增业务模块时：在 `endpoints/` 下建文件，然后在这里注册一行即可。
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter()
api_router.include_router(health.router)

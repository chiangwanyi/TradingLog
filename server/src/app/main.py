"""FastAPI 应用入口：创建实例、挂载中间件与路由。

对外暴露的 `app` 供 ASGI 服务器引用（`app.main:app`）。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.db import init_db
from app.core.errors import NotFoundError, ValidationError


@asynccontextmanager
async def lifespan(_: FastAPI):
    """启动时建好数据目录与表结构；SQLite 建表是幂等的。"""
    init_db()
    yield


def create_app() -> FastAPI:
    """应用工厂：便于测试按需构造独立实例，也方便未来按环境覆写。"""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 领域异常 -> HTTP 响应，服务层因此不需要依赖 FastAPI
    @application.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @application.exception_handler(ValidationError)
    async def _invalid(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    application.include_router(api_router, prefix=settings.api_v1_prefix)

    return application


app = create_app()

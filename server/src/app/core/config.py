"""应用配置。

所有配置项均可用环境变量覆盖，也可写在项目根目录的 `.env` 里（见 `.env.example`）。
读取优先级：环境变量 > .env 文件 > 下方默认值。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """运行期配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- 基础信息 ----
    app_name: str = "TradingLog API"
    app_version: str = "0.1.0"
    debug: bool = False

    # ---- 服务监听 ----
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False

    # ---- 路由 ----
    api_v1_prefix: str = "/api/v1"

    # ---- 跨域：允许访问的前端来源 ----
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    """返回配置单例；测试中可用 `get_settings.cache_clear()` 重置。"""
    return Settings()

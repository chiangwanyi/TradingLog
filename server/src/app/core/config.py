"""应用配置。

所有配置项均可用环境变量覆盖，也可写在项目根目录的 `.env` 里（见 `.env.example`）。
读取优先级：环境变量 > .env 文件 > 下方默认值。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（server/）：本文件位于 server/src/app/core/config.py
SERVER_ROOT = Path(__file__).resolve().parents[3]


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

    # ---- 数据存储 ----
    # 运行期数据（SQLite 库 + 截图原图/缩略图）统一放在这里，已加入 .gitignore
    data_dir: Path = SERVER_ROOT / "data"
    # 单张图片的体积上限
    max_image_bytes: int = 20 * 1024 * 1024
    # 缩略图最长边（预览缩略图条使用）
    thumbnail_max_side: int = 480

    @property
    def db_path(self) -> Path:
        """SQLite 数据库文件路径。"""
        return self.data_dir / "tradinglog.db"

    @property
    def uploads_dir(self) -> Path:
        """截图原图与缩略图的存放根目录。"""
        return self.data_dir / "uploads"

    def ensure_dirs(self) -> None:
        """确保运行期需要的目录都存在。"""
        self.uploads_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """返回配置单例；测试中可用 `get_settings.cache_clear()` 重置。"""
    return Settings()

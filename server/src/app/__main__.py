"""命令行入口。

用法（均需在 server/ 目录下执行）：
    uv run tradinglog-server
    uv run python -m app
"""

import uvicorn

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )


if __name__ == "__main__":
    main()

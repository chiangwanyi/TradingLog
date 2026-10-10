"""pytest 共享夹具。

把运行期数据（SQLite 库 + 截图文件）指向临时目录，
这样跑测试不会污染 `server/data/` 里的真实数据。
"""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client(tmp_path_factory: pytest.TempPathFactory) -> TestClient:
    """全局测试客户端，使用独立的临时数据目录。"""
    from app.core.config import get_settings

    os.environ["DATA_DIR"] = str(tmp_path_factory.mktemp("tradinglog-data"))
    get_settings.cache_clear()

    # 必须在设置好 DATA_DIR 之后再构造应用，lifespan 会按新路径建库
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client

    get_settings.cache_clear()

"""pytest 共享夹具。"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """全局测试客户端。"""
    return TestClient(app)

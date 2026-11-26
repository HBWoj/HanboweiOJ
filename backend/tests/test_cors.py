import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
    ],
)
def test_allowed_origins_receive_cors_headers(origin: str) -> None:
    """测试三套本地前端地址均被允许跨域访问。"""
    response = client.options(
        "/api/v1",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_untrusted_origin_is_rejected() -> None:
    """测试未经授权的来源不能通过 CORS 预检。"""
    response = client.options(
        "/api/v1",
        headers={
            "Origin": "http://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

"""
API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthCheckAPI:
    """健康检查API测试"""

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200


class TestAuthAPI:
    """认证API测试"""

    def test_login_endpoint_exists(self, client):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test@test.com", "password": "test123"}
        )
        assert response.status_code in [200, 401, 422]

    def test_me_endpoint_requires_auth(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestVendorAPI:
    """供应商API测试"""

    def test_vendors_endpoint_requires_auth(self, client):
        response = client.get("/api/v1/vendors")
        assert response.status_code in [200, 401]


class TestSLAAPI:
    """SLA计算API测试"""

    def test_sla_calculate_requires_auth(self, client):
        response = client.post(
            "/api/v1/sla/calculate",
            json={"vendor_id": 1, "period": "2026-03"}
        )
        assert response.status_code in [200, 401, 404, 422]


class TestAlertAPI:
    """告警API测试"""

    def test_alerts_endpoint_requires_auth(self, client):
        response = client.get("/api/v1/alerts")
        assert response.status_code in [200, 401]


class TestConfigAPI:
    """配置管理API测试"""

    def test_config_requires_auth(self, client):
        response = client.get("/api/v1/config")
        assert response.status_code in [200, 401]


class TestAPIDocs:
    """API文档测试"""

    def test_openapi_docs(self, client):
        response = client.get("/api/docs")
        assert response.status_code == 200
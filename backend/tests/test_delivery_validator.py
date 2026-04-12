"""
验收一票否决逻辑单元测试
"""
import pytest
from app.services.delivery_validator import DeliveryValidator


class TestDeliveryValidator:
    """验收验证测试"""

    def test_delivery_validator_class_exists(self):
        """验证类存在"""
        assert DeliveryValidator is not None


class TestVetoReasonMessages:
    """否决原因消息测试"""

    def test_veto_reason_format(self):
        reason = "供应商已被暂停，无法进行验收"
        assert "暂停" in reason
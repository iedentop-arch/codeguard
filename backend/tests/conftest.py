"""
Pytest Configuration and Fixtures
"""
import pytest
from datetime import datetime, date
from decimal import Decimal

from app.models.models import (
    Vendor, VendorMember, User, MonthlyScore,
    SLAGrade, VendorStatus, VendorType
)


@pytest.fixture
def sample_vendor():
    """示例供应商数据"""
    return Vendor(
        id=1,
        name="测试供应商A",
        vendor_type=VendorType.A,
        status=VendorStatus.ACTIVE,
        contact_name="张三",
        contact_email="zhangsan@test.com",
        contract_start=date(2026, 1, 1),
        contract_end=date(2026, 12, 31),
        github_org="test-org-a",
        current_grade=SLAGrade.A,
        current_score=Decimal("85.5"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=False,
    )


@pytest.fixture
def sample_user():
    """示例用户数据"""
    return User(
        id=1,
        email="admin@test.com",
        hashed_password="hashed_password_here",
        name="管理员",
        role="admin",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=False,
    )
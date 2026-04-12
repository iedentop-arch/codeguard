"""
乙方相关 Schema
"""
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel


class VendorType(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class VendorStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    WARNING = "warning"
    SUSPENDED = "suspended"
    EXITED = "exited"


class SLAGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


# ============ Vendor Schemas ============

class VendorBase(BaseModel):
    """乙方基础信息"""
    name: str
    vendor_type: VendorType
    contact_name: str | None = None
    contact_email: str | None = None
    github_org: str | None = None
    contract_start: date | None = None
    contract_end: date | None = None


class VendorCreate(VendorBase):
    """创建乙方"""
    pass


class VendorUpdate(BaseModel):
    """更新乙方"""
    name: str | None = None
    vendor_type: VendorType | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    github_org: str | None = None
    contract_start: date | None = None
    contract_end: date | None = None
    status: VendorStatus | None = None


class VendorResponse(VendorBase):
    """乙方响应"""
    id: int
    status: VendorStatus
    member_count: int = 0
    current_grade: SLAGrade | None = None
    current_score: float | None = None
    onboarding_status: str = "not_started"
    created_at: datetime

    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    """乙方列表响应"""
    items: list[VendorResponse]
    total: int


# ============ Vendor Member Schemas ============

class MemberBase(BaseModel):
    """成员基础信息"""
    name: str
    email: str
    role: str
    github_username: str | None = None


class MemberCreate(MemberBase):
    """创建成员"""
    pass


class MemberUpdate(BaseModel):
    """更新成员"""
    name: str | None = None
    role: str | None = None
    github_username: str | None = None
    status: str | None = None


class MemberResponse(MemberBase):
    """成员响应"""
    id: int
    vendor_id: int
    status: str
    exam_score: int | None = None
    certification_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

"""
乙方相关 Schema
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum


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
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    github_org: Optional[str] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None


class VendorCreate(VendorBase):
    """创建乙方"""
    pass


class VendorUpdate(BaseModel):
    """更新乙方"""
    name: Optional[str] = None
    vendor_type: Optional[VendorType] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    github_org: Optional[str] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    status: Optional[VendorStatus] = None


class VendorResponse(VendorBase):
    """乙方响应"""
    id: int
    status: VendorStatus
    member_count: int = 0
    current_grade: Optional[SLAGrade] = None
    current_score: Optional[float] = None
    onboarding_status: str = "not_started"
    created_at: datetime

    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    """乙方列表响应"""
    items: List[VendorResponse]
    total: int


# ============ Vendor Member Schemas ============

class MemberBase(BaseModel):
    """成员基础信息"""
    name: str
    email: str
    role: str
    github_username: Optional[str] = None


class MemberCreate(MemberBase):
    """创建成员"""
    pass


class MemberUpdate(BaseModel):
    """更新成员"""
    name: Optional[str] = None
    role: Optional[str] = None
    github_username: Optional[str] = None
    status: Optional[str] = None


class MemberResponse(MemberBase):
    """成员响应"""
    id: int
    vendor_id: int
    status: str
    exam_score: Optional[int] = None
    certification_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
"""
代码审查相关 Schema
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel
from enum import Enum


class PRStatus(str, Enum):
    OPEN = "open"
    CI_CHECKING = "ci_checking"
    CI_PASSED = "ci_passed"
    CI_FAILED = "ci_failed"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"
    CLOSED = "closed"


class GateStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    RUNNING = "running"


# ============ Quality Gate Schemas ============

class QualityGateBase(BaseModel):
    """质量门禁基础"""
    layer: int
    layer_name: str
    status: GateStatus
    details: Optional[Dict[str, GateStatus]] = None
    violations_count: int = 0
    warnings_count: int = 0


class QualityGateResponse(QualityGateBase):
    """质量门禁响应"""
    id: int
    pr_id: int
    checked_at: datetime

    class Config:
        from_attributes = True


# ============ PR Schemas ============

class PRBase(BaseModel):
    """PR基础信息"""
    github_pr_number: int
    title: str
    branch: Optional[str] = None


class PRCreate(PRBase):
    """创建PR"""
    vendor_id: int
    author_id: Optional[int] = None
    github_pr_url: Optional[str] = None


class PRUpdate(BaseModel):
    """更新PR"""
    status: Optional[PRStatus] = None
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None
    files_changed: Optional[int] = None
    has_ai_code: Optional[bool] = None
    ai_code_marked: Optional[bool] = None


class PRResponse(BaseModel):
    """PR响应"""
    id: int
    vendor_id: int
    vendor_name: Optional[str] = None
    author_name: Optional[str] = None
    github_pr_number: int
    github_pr_url: Optional[str] = None
    title: str
    branch: Optional[str] = None
    status: PRStatus
    lines_added: int
    lines_removed: int
    files_changed: int
    has_ai_code: bool
    ai_code_marked: bool
    created_at: datetime
    merged_at: Optional[datetime] = None
    gates: List[QualityGateResponse] = []

    class Config:
        from_attributes = True


class PRListResponse(BaseModel):
    """PR列表响应"""
    items: List[PRResponse]
    total: int


# ============ Review Schemas ============

class ReviewComment(BaseModel):
    """评审评论"""
    comment: str


class ReviewApprove(BaseModel):
    """批准合并"""
    comment: Optional[str] = None


class ReviewReject(BaseModel):
    """驳回修改"""
    reason: str
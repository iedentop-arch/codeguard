"""
代码审查相关 Schema
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


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
    details: dict[str, GateStatus] | None = None
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
    branch: str | None = None


class PRCreate(PRBase):
    """创建PR"""
    vendor_id: int
    author_id: int | None = None
    github_pr_url: str | None = None


class PRUpdate(BaseModel):
    """更新PR"""
    status: PRStatus | None = None
    lines_added: int | None = None
    lines_removed: int | None = None
    files_changed: int | None = None
    has_ai_code: bool | None = None
    ai_code_marked: bool | None = None


class PRResponse(BaseModel):
    """PR响应"""
    id: int
    vendor_id: int
    vendor_name: str | None = None
    author_name: str | None = None
    github_pr_number: int
    github_pr_url: str | None = None
    title: str
    branch: str | None = None
    status: PRStatus
    lines_added: int
    lines_removed: int
    files_changed: int
    has_ai_code: bool
    ai_code_marked: bool
    created_at: datetime
    merged_at: datetime | None = None
    gates: list[QualityGateResponse] = []

    class Config:
        from_attributes = True


class PRListResponse(BaseModel):
    """PR列表响应"""
    items: list[PRResponse]
    total: int


# ============ Review Schemas ============

class ReviewComment(BaseModel):
    """评审评论"""
    comment: str


class ReviewApprove(BaseModel):
    """批准合并"""
    comment: str | None = None


class ReviewReject(BaseModel):
    """驳回修改"""
    reason: str

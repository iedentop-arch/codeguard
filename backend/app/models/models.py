"""
SQLAlchemy 数据库模型

Author: AI-Assisted: 60%
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Text, Integer, Numeric, Boolean, DateTime, Date,
    ForeignKey, Index, Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class TimestampMixin:
    """时间戳混入类"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class VendorType(str, enum.Enum):
    """乙方类型"""
    A = "A"  # 前端
    B = "B"  # 后端
    C = "C"  # AI Agent
    D = "D"  # 全栈


class VendorStatus(str, enum.Enum):
    """乙方状态"""
    PENDING = "pending"
    ACTIVE = "active"
    WARNING = "warning"
    SUSPENDED = "suspended"
    EXITED = "exited"


class SLAGrade(str, enum.Enum):
    """SLA等级"""
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class Vendor(Base, TimestampMixin):
    """乙方组织表"""
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="乙方名称")
    vendor_type: Mapped[VendorType] = mapped_column(SQLEnum(VendorType), nullable=False, comment="乙方类型")
    status: Mapped[VendorStatus] = mapped_column(
        SQLEnum(VendorStatus), default=VendorStatus.PENDING, nullable=False, comment="状态"
    )
    contact_name: Mapped[Optional[str]] = mapped_column(String(50), comment="联系人")
    contact_email: Mapped[Optional[str]] = mapped_column(String(100), comment="联系邮箱")
    contract_start: Mapped[Optional[datetime]] = mapped_column(Date, comment="合同开始日期")
    contract_end: Mapped[Optional[datetime]] = mapped_column(Date, comment="合同结束日期")
    github_org: Mapped[Optional[str]] = mapped_column(String(100), comment="GitHub组织")
    current_grade: Mapped[Optional[SLAGrade]] = mapped_column(SQLEnum(SLAGrade), comment="当前等级")
    current_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 1), comment="当前评分")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 关联
    members: Mapped[list["VendorMember"]] = relationship(back_populates="vendor")
    pull_requests: Mapped[list["PullRequest"]] = relationship(back_populates="vendor")
    monthly_scores: Mapped[list["MonthlyScore"]] = relationship(back_populates="vendor")
    deliveries: Mapped[list["Delivery"]] = relationship(back_populates="vendor")


class VendorMember(Base, TimestampMixin):
    """乙方成员表"""
    __tablename__ = "vendor_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), comment="用户ID")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="姓名")
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="邮箱")
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="角色")
    status: Mapped[str] = mapped_column(String(16), default="pending", comment="状态")
    github_username: Mapped[Optional[str]] = mapped_column(String(50), comment="GitHub用户名")
    exam_score: Mapped[Optional[int]] = mapped_column(Integer, comment="考试分数")
    exam_attempts: Mapped[int] = mapped_column(Integer, default=0, comment="考试尝试次数")
    certification_id: Mapped[Optional[str]] = mapped_column(String(32), comment="认证编号")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 关联
    vendor: Mapped["Vendor"] = relationship(back_populates="members")


class SpecDocument(Base, TimestampMixin):
    """规范文档表"""
    __tablename__ = "spec_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="标题")
    file_path: Mapped[Optional[str]] = mapped_column(String(300), comment="文件路径(如02-architecture/system-design-principles.md)")
    category: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类")
    vendor_types: Mapped[str] = mapped_column(String(20), nullable=False, comment="适用乙方类型")
    content: Mapped[Optional[str]] = mapped_column(Text, comment="内容(Markdown)")
    read_time: Mapped[int] = mapped_column(Integer, default=10, comment="预计阅读时间(分钟)")
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否必读")
    version: Mapped[str] = mapped_column(String(20), default="1.0", comment="版本号")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ExamQuestion(Base, TimestampMixin):
    """考试题目表"""
    __tablename__ = "exam_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, comment="分类")
    rule_id: Mapped[Optional[str]] = mapped_column(String(20), comment="规则编号")
    severity: Mapped[str] = mapped_column(String(16), nullable=False, comment="严重程度")
    question_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="题型")
    question_text: Mapped[str] = mapped_column(Text, nullable=False, comment="题目内容")
    code_snippet: Mapped[Optional[str]] = mapped_column(Text, comment="代码片段")
    options: Mapped[str] = mapped_column(Text, nullable=False, comment="选项(JSON)")
    correct_answer: Mapped[str] = mapped_column(String(10), nullable=False, comment="正确答案")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, comment="解释")
    vendor_types: Mapped[str] = mapped_column(String(20), default="ABCD", comment="适用乙方类型")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PullRequest(Base, TimestampMixin):
    """Pull Request表"""
    __tablename__ = "pull_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False)
    author_id: Mapped[Optional[int]] = mapped_column(Integer, comment="作者ID")
    github_pr_number: Mapped[int] = mapped_column(Integer, nullable=False, comment="PR编号")
    github_pr_url: Mapped[Optional[str]] = mapped_column(String(500), comment="PR链接")
    head_sha: Mapped[Optional[str]] = mapped_column(String(64), comment="PR head commit SHA")
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="标题")
    branch: Mapped[Optional[str]] = mapped_column(String(100), comment="分支名")
    status: Mapped[str] = mapped_column(String(20), default="open", comment="状态")
    lines_added: Mapped[int] = mapped_column(Integer, default=0, comment="新增行数")
    lines_removed: Mapped[int] = mapped_column(Integer, default=0, comment="删除行数")
    files_changed: Mapped[int] = mapped_column(Integer, default=0, comment="变更文件数")
    has_ai_code: Mapped[bool] = mapped_column(Boolean, default=False, comment="包含AI代码")
    ai_code_marked: Mapped[bool] = mapped_column(Boolean, default=True, comment="AI代码已标记")
    merged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="合并时间")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 关联
    vendor: Mapped["Vendor"] = relationship(back_populates="pull_requests")
    quality_gates: Mapped[list["QualityGate"]] = relationship(back_populates="pr")


class QualityGate(Base, TimestampMixin):
    """质量门禁结果表"""
    __tablename__ = "quality_gates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pr_id: Mapped[int] = mapped_column(Integer, ForeignKey("pull_requests.id"), nullable=False)
    layer: Mapped[int] = mapped_column(Integer, nullable=False, comment="层级(1-6)")
    layer_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="层级名称")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
    details: Mapped[Optional[str]] = mapped_column(Text, comment="详情(JSON)")
    violations_count: Mapped[int] = mapped_column(Integer, default=0, comment="违规数")
    warnings_count: Mapped[int] = mapped_column(Integer, default=0, comment="警告数")

    # 关联
    pr: Mapped["PullRequest"] = relationship(back_populates="quality_gates")


class MonthlyScore(Base, TimestampMixin):
    """月度SLA评分表"""
    __tablename__ = "monthly_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False)
    score_period: Mapped[datetime] = mapped_column(Date, nullable=False, comment="评分月份")

    # 原始指标
    critical_violations: Mapped[int] = mapped_column(Integer, default=0, comment="CRITICAL违规数")
    warning_trend_pct: Mapped[Optional[float]] = mapped_column(Numeric(5, 1), comment="WARNING趋势")
    code_quality_score: Mapped[float] = mapped_column(Numeric(5, 1), default=0, comment="代码质量分")
    compliance_pass_rate: Mapped[float] = mapped_column(Numeric(5, 1), default=0, comment="合规通过率")
    pr_avg_review_rounds: Mapped[float] = mapped_column(Numeric(3, 1), default=0, comment="平均评审轮数")
    ai_code_marking_rate: Mapped[float] = mapped_column(Numeric(5, 1), default=0, comment="AI代码标记率")
    ci_success_rate: Mapped[float] = mapped_column(Numeric(5, 1), default=0, comment="CI成功率")

    # 综合评分
    total_score: Mapped[float] = mapped_column(Numeric(5, 1), nullable=False, comment="总分")
    grade: Mapped[SLAGrade] = mapped_column(SQLEnum(SLAGrade), nullable=False, comment="等级")

    # 索引
    __table_args__ = (
        Index("idx_vendor_period", "vendor_id", "score_period", unique=True),
    )

    # 关联
    vendor: Mapped["Vendor"] = relationship(back_populates="monthly_scores")


class Delivery(Base, TimestampMixin):
    """交付包表"""
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, comment="项目ID")
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, comment="版本号")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="描述")
    artifacts: Mapped[Optional[str]] = mapped_column(Text, comment="附件(JSON)")
    status: Mapped[str] = mapped_column(String(20), default="submitted", comment="状态")
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="评审时间")
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(64), comment="评审人")
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, comment="评审备注")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 关联
    vendor: Mapped["Vendor"] = relationship(back_populates="deliveries")
    checklist_items: Mapped[list["DeliveryChecklist"]] = relationship(back_populates="delivery")


class DeliveryChecklist(Base, TimestampMixin):
    """交付验收清单表"""
    __tablename__ = "delivery_checklists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(Integer, ForeignKey("deliveries.id"), nullable=False)
    dimension: Mapped[str] = mapped_column(String(50), nullable=False, comment="维度")
    item_number: Mapped[str] = mapped_column(String(10), nullable=False, comment="项编号")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="描述")
    acceptance_criteria: Mapped[str] = mapped_column(Text, nullable=False, comment="验收标准")
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="状态")
    auto_filled: Mapped[bool] = mapped_column(Boolean, default=False, comment="自动填充")
    evidence_url: Mapped[Optional[str]] = mapped_column(String(500), comment="证据链接")
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, comment="评审备注")

    # 关联
    delivery: Mapped["Delivery"] = relationship(back_populates="checklist_items")


class User(Base, TimestampMixin):
    """用户表（甲方用户）"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="邮箱")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="姓名")
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="角色")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
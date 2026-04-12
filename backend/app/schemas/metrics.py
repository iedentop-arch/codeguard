"""
SLA评分相关 Schema
"""
from datetime import date
from typing import Optional, List
from pydantic import BaseModel
from .vendor import SLAGrade


class MonthlyScoreBase(BaseModel):
    """月度评分基础"""
    critical_violations: int = 0
    warning_trend_pct: Optional[float] = None
    code_quality_score: float = 0
    compliance_pass_rate: float = 0
    pr_avg_review_rounds: float = 0
    ai_code_marking_rate: float = 0
    ci_success_rate: float = 0


class MonthlyScoreResponse(MonthlyScoreBase):
    """月度评分响应"""
    id: int
    vendor_id: int
    vendor_name: Optional[str] = None
    score_period: date
    total_score: float
    grade: SLAGrade
    created_at: date

    class Config:
        from_attributes = True


class VendorScorecard(BaseModel):
    """乙方评分卡"""
    vendor_id: int
    vendor_name: str
    vendor_type: str
    current_grade: SLAGrade
    current_score: float
    latest_score: Optional[MonthlyScoreResponse] = None
    dimensions: dict = {}  # 7维度详情


class DashboardOverview(BaseModel):
    """看板概览"""
    active_vendors: int
    critical_violations: int
    avg_ci_success_rate: float
    avg_sla_score: float
    vendors_by_grade: dict = {}  # A/B/C/D 各有多少


class TrendDataPoint(BaseModel):
    """趋势数据点"""
    period: str
    vendors: dict = {}  # vendor_name -> score


class TrendResponse(BaseModel):
    """趋势响应"""
    data: List[TrendDataPoint]
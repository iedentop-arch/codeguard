"""
SLA相关Schema定义
"""
from typing import Any

from pydantic import BaseModel, Field


class DimensionScoreResponse(BaseModel):
    """维度得分响应"""
    name: str
    score: float = Field(..., ge=0, le=100)
    weight: float
    weighted_score: float
    raw_value: Any
    target: str


class SLABreakdownResponse(BaseModel):
    """SLA维度详情响应"""
    vendor_id: int
    vendor_name: str
    period: str
    dimensions: list[DimensionScoreResponse]
    total_score: float
    grade: str


class SLACalculateRequest(BaseModel):
    """SLA计算请求"""
    vendor_id: int
    period: str | None = None  # YYYY-MM格式，默认上月


class SLACalculateResponse(BaseModel):
    """SLA计算响应"""
    vendor_id: int
    vendor_name: str
    period: str
    total_score: float
    grade: str
    dimensions: list[DimensionScoreResponse]
    message: str = "评分计算完成"


class VendorComparisonResponse(BaseModel):
    """供应商对比响应"""
    vendor_id: int
    vendor_name: str
    vendor_type: str
    current_grade: str
    current_score: float
    dimension_scores: dict[str, float]


class SLATrendResponse(BaseModel):
    """SLA趋势响应"""
    vendor_id: int
    vendor_name: str
    periods: list[str]
    scores: list[float]
    grades: list[str]

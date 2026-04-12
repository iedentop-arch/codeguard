"""
SLA指标 API
"""
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.models import Vendor, MonthlyScore
from app.schemas.metrics import (
    DashboardOverview, VendorScorecard, MonthlyScoreResponse, TrendDataPoint,
)
from app.schemas.response import ApiResponse
from app.models.models import SLAGrade

router = APIRouter()


@router.get("/overview", response_model=ApiResponse[DashboardOverview])
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取看板概览"""
    # 活跃乙方数
    active_result = await db.execute(
        select(func.count()).where(
            Vendor.status.in_(["active", "warning"]),
            Vendor.is_deleted == False
        )
    )
    active_vendors = active_result.scalar() or 0
    
    # 所有乙方
    vendors_result = await db.execute(
        select(Vendor).where(Vendor.is_deleted == False)
    )
    vendors = vendors_result.scalars().all()
    
    # CRITICAL违规总数（最近一个月）
    # TODO: 实现真实计算
    critical_violations = 5
    
    # 平均CI成功率
    avg_ci = 89.0
    
    # 平均SLA评分
    avg_score = sum(v.current_score or 0 for v in vendors) / len(vendors) if vendors else 0
    
    # 按等级统计
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for v in vendors:
        if v.current_grade:
            grade_counts[v.current_grade.value] = grade_counts.get(v.current_grade.value, 0) + 1
    
    return ApiResponse(data=DashboardOverview(
        active_vendors=active_vendors,
        critical_violations=critical_violations,
        avg_ci_success_rate=avg_ci,
        avg_sla_score=round(avg_score, 1),
        vendors_by_grade=grade_counts,
    ))


@router.get("/vendor/{vendor_id}", response_model=ApiResponse[VendorScorecard])
async def get_vendor_scorecard(
    vendor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取乙方评分卡"""
    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.is_deleted == False)
    )
    vendor = result.scalar_one_or_none()
    
    if not vendor:
        return ApiResponse(code=404, message="乙方不存在")
    
    # 获取最近评分
    score_result = await db.execute(
        select(MonthlyScore).where(
            MonthlyScore.vendor_id == vendor_id
        ).order_by(MonthlyScore.score_period.desc()).limit(1)
    )
    latest_score = score_result.scalar_one_or_none()
    
    dimensions = {
        "critical_violations": latest_score.critical_violations if latest_score else 0,
        "warning_trend": latest_score.warning_trend_pct if latest_score else 0,
        "code_quality": latest_score.code_quality_score if latest_score else 0,
        "compliance_rate": latest_score.compliance_pass_rate if latest_score else 0,
        "review_efficiency": latest_score.pr_avg_review_rounds if latest_score else 0,
        "ai_marking": latest_score.ai_code_marking_rate if latest_score else 0,
        "ci_success": latest_score.ci_success_rate if latest_score else 0,
    }
    
    return ApiResponse(data=VendorScorecard(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        vendor_type=vendor.vendor_type.value,
        current_grade=vendor.current_grade or SLAGrade.D,
        current_score=vendor.current_score or 0,
        latest_score=MonthlyScoreResponse.model_validate(latest_score) if latest_score else None,
        dimensions=dimensions,
    ))


@router.get("/trends")
async def get_trends(
    months: int = Query(3, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取评分趋势"""
    # 获取所有乙方
    vendors_result = await db.execute(
        select(Vendor).where(Vendor.is_deleted == False)
    )
    vendors = vendors_result.scalars().all()
    
    # 获取最近N个月的评分
    periods = ["2026-01", "2026-02", "2026-03"]  # TODO: 动态计算
    trend_data = []
    
    for period in periods:
        scores_result = await db.execute(
            select(MonthlyScore).where(MonthlyScore.score_period == period)
        )
        scores = scores_result.scalars().all()
        
        vendor_scores = {}
        for v in vendors:
            score = next((s for s in scores if s.vendor_id == v.id), None)
            vendor_scores[v.name] = score.total_score if score else None
        
        trend_data.append(TrendDataPoint(period=period, vendors=vendor_scores))
    
    return ApiResponse(data=[t.model_dump() for t in trend_data])


@router.get("/vendor/{vendor_id}/history")
async def get_vendor_history(
    vendor_id: int,
    months: int = Query(6, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取乙方历史评分"""
    result = await db.execute(
        select(MonthlyScore).where(
            MonthlyScore.vendor_id == vendor_id
        ).order_by(MonthlyScore.score_period.desc()).limit(months)
    )
    scores = result.scalars().all()
    
    return ApiResponse(data=[MonthlyScoreResponse.model_validate(s) for s in scores])
"""
SLA评分API端点
"""
from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.models import Vendor, MonthlyScore, User, SLAGrade
from app.services.sla_engine import SLAEngine
from app.schemas.sla import (
    SLABreakdownResponse, SLACalculateRequest, SLACalculateResponse,
    DimensionScoreResponse, VendorComparisonResponse, SLATrendResponse
)
from app.schemas.response import ApiResponse

router = APIRouter()


@router.post("/calculate", response_model=ApiResponse[SLACalculateResponse])
async def calculate_sla_score(
    request: SLACalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    手动触发SLA评分计算

    仅管理员可调用
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可触发评分计算")

    # 解析period参数
    if request.period:
        period = datetime.strptime(request.period, "%Y-%m").date()
    else:
        # 默认上月
        today = date.today()
        if today.month == 1:
            period = date(today.year - 1, 12, 1)
        else:
            period = date(today.year, today.month - 1, 1)

    try:
        result = await SLAEngine.calculate_vendor_monthly_score(
            request.vendor_id, period, db, save=True
        )

        dimensions = [
            DimensionScoreResponse(
                name=dim.name,
                score=dim.score,
                weight=dim.weight,
                weighted_score=round(dim.score * dim.weight, 2),
                raw_value=dim.raw_value,
                target=dim.target
            )
            for dim in result.dimensions
        ]

        return ApiResponse(data=SLACalculateResponse(
            vendor_id=result.vendor_id,
            vendor_name=result.vendor_name,
            period=result.period,
            total_score=result.total_score,
            grade=result.grade.value,
            dimensions=dimensions
        ))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评分计算失败: {str(e)}")


@router.get("/breakdown/{vendor_id}", response_model=ApiResponse[SLABreakdownResponse])
async def get_sla_breakdown(
    vendor_id: int,
    period: Optional[str] = Query(None, description="YYYY-MM格式，默认最新"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取乙方SLA维度得分详情 (用于雷达图展示)
    """
    # 获取乙方
    vendor_result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.is_deleted == False)
    )
    vendor = vendor_result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="乙方不存在")

    # 获取评分记录
    if period:
        period_date = datetime.strptime(period, "%Y-%m").date()
        score_result = await db.execute(
            select(MonthlyScore).where(
                MonthlyScore.vendor_id == vendor_id,
                MonthlyScore.score_period == period_date
            )
        )
    else:
        score_result = await db.execute(
            select(MonthlyScore).where(
                MonthlyScore.vendor_id == vendor_id
            ).order_by(MonthlyScore.score_period.desc()).limit(1)
        )

    monthly_score = score_result.scalar_one_or_none()

    if not monthly_score:
        # 没有评分记录，返回默认值
        dimensions = [
            DimensionScoreResponse(name="critical_violations", score=100, weight=0.30, weighted_score=30, raw_value=0, target="=0"),
            DimensionScoreResponse(name="warning_trend", score=80, weight=0.15, weighted_score=12, raw_value=0, target="≥10%下降"),
            DimensionScoreResponse(name="code_quality", score=80, weight=0.15, weighted_score=12, raw_value=80, target="≥90"),
            DimensionScoreResponse(name="compliance_pass_rate", score=90, weight=0.15, weighted_score=13.5, raw_value=90, target="≥95%"),
            DimensionScoreResponse(name="review_efficiency", score=100, weight=0.10, weighted_score=10, raw_value=2, target="≤2轮"),
            DimensionScoreResponse(name="ai_marking_rate", score=100, weight=0.10, weighted_score=10, raw_value=100, target="100%"),
            DimensionScoreResponse(name="ci_success_rate", score=85, weight=0.05, weighted_score=4.25, raw_value=85, target="≥95%"),
        ]
        return ApiResponse(data=SLABreakdownResponse(
            vendor_id=vendor_id,
            vendor_name=vendor.name,
            period=period or date.today().strftime("%Y-%m"),
            dimensions=dimensions,
            total_score=81.75,
            grade="B"
        ))

    # 构建维度得分
    raw_metrics = {
        "critical_violations": monthly_score.critical_violations,
        "warning_trend": monthly_score.warning_trend_pct or 0,
        "code_quality": monthly_score.code_quality_score,
        "compliance_pass_rate": monthly_score.compliance_pass_rate,
        "review_efficiency": monthly_score.pr_avg_review_rounds,
        "ai_marking_rate": monthly_score.ai_code_marking_rate,
        "ci_success_rate": monthly_score.ci_success_rate,
    }

    dimensions = []
    for dim_name, weight in SLAEngine.WEIGHTS.items():
        raw_value = raw_metrics.get(dim_name, 0)
        score = SLAEngine.calculate_dimension_score(dim_name, raw_value)
        target = SLAEngine.TARGETS[dim_name]["description"]
        dimensions.append(DimensionScoreResponse(
            name=dim_name,
            score=score,
            weight=weight,
            weighted_score=round(score * weight, 2),
            raw_value=raw_value,
            target=target
        ))

    return ApiResponse(data=SLABreakdownResponse(
        vendor_id=vendor_id,
        vendor_name=vendor.name,
        period=monthly_score.score_period.strftime("%Y-%m"),
        dimensions=dimensions,
        total_score=float(monthly_score.total_score),
        grade=monthly_score.grade.value
    ))


@router.get("/comparison", response_model=ApiResponse[List[VendorComparisonResponse]])
async def get_vendor_comparison(
    period: Optional[str] = Query(None, description="YYYY-MM格式"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取所有供应商SLA对比数据 (用于对比雷达图)
    """
    # 获取所有活跃乙方
    vendors_result = await db.execute(
        select(Vendor).where(
            Vendor.is_deleted == False
        )
    )
    vendors = vendors_result.scalars().all()

    comparisons = []
    for vendor in vendors:
        # 获取评分
        if period:
            period_date = datetime.strptime(period, "%Y-%m").date()
            score_result = await db.execute(
                select(MonthlyScore).where(
                    MonthlyScore.vendor_id == vendor.id,
                    MonthlyScore.score_period == period_date
                )
            )
        else:
            score_result = await db.execute(
                select(MonthlyScore).where(
                    MonthlyScore.vendor_id == vendor.id
                ).order_by(MonthlyScore.score_period.desc()).limit(1)
            )

        monthly_score = score_result.scalar_one_or_none()

        if monthly_score:
            dimension_scores = {
                "critical_violations": SLAEngine.calculate_dimension_score("critical_violations", monthly_score.critical_violations),
                "warning_trend": SLAEngine.calculate_dimension_score("warning_trend", monthly_score.warning_trend_pct),
                "code_quality": monthly_score.code_quality_score,
                "compliance_pass_rate": monthly_score.compliance_pass_rate,
                "review_efficiency": SLAEngine.calculate_dimension_score("review_efficiency", monthly_score.pr_avg_review_rounds),
                "ai_marking_rate": monthly_score.ai_code_marking_rate,
                "ci_success_rate": monthly_score.ci_success_rate,
            }
            comparisons.append(VendorComparisonResponse(
                vendor_id=vendor.id,
                vendor_name=vendor.name,
                vendor_type=vendor.vendor_type.value,
                current_grade=vendor.current_grade.value if vendor.current_grade else "D",
                current_score=float(vendor.current_score or 0),
                dimension_scores=dimension_scores
            ))

    return ApiResponse(data=comparisons)


@router.get("/trend/{vendor_id}", response_model=ApiResponse[SLATrendResponse])
async def get_sla_trend(
    vendor_id: int,
    months: int = Query(6, ge=1, le=12, description="查询月数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取乙方SLA评分历史趋势
    """
    vendor_result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id)
    )
    vendor = vendor_result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="乙方不存在")

    score_result = await db.execute(
        select(MonthlyScore).where(
            MonthlyScore.vendor_id == vendor_id
        ).order_by(MonthlyScore.score_period.desc()).limit(months)
    )
    scores = score_result.scalars().all()

    periods = [s.score_period.strftime("%Y-%m") for s in scores]
    score_values = [float(s.total_score) for s in scores]
    grades = [s.grade.value for s in scores]

    return ApiResponse(data=SLATrendResponse(
        vendor_id=vendor_id,
        vendor_name=vendor.name,
        periods=periods,
        scores=score_values,
        grades=grades
    ))


@router.post("/calculate-all")
async def calculate_all_vendors(
    period: Optional[str] = Query(None, description="YYYY-MM格式"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    批量计算所有乙方月度评分

    仅管理员可调用
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可批量计算评分")

    if period:
        period_date = datetime.strptime(period, "%Y-%m").date()
    else:
        today = date.today()
        if today.month == 1:
            period_date = date(today.year - 1, 12, 1)
        else:
            period_date = date(today.year, today.month - 1, 1)

    results = await SLAEngine.calculate_all_vendors_monthly_score(period_date, db)

    return ApiResponse(data={
        "period": period_date.strftime("%Y-%m"),
        "vendors_calculated": len(results),
        "results": [
            {
                "vendor_id": r.vendor_id,
                "vendor_name": r.vendor_name,
                "total_score": r.total_score,
                "grade": r.grade.value
            }
            for r in results
        ]
    })
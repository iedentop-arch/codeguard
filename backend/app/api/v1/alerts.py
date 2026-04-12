"""
告警管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.models import User, Vendor
from app.schemas.response import ApiResponse
from app.services.alert_engine import AlertEngine

router = APIRouter()


@router.get("")
async def list_alerts(
    vendor_id: int | None = Query(None),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取告警列表

    支持按供应商、严重程度、状态过滤
    """
    # 评估告警
    if vendor_id:
        alerts = await AlertEngine.evaluate_vendor(vendor_id, db)
    else:
        alerts = await AlertEngine.evaluate_all_vendors(db)

    # 过滤
    if severity:
        alerts = [a for a in alerts if a.severity == severity]

    return ApiResponse(data=[
        {
            "rule_id": a.rule_id,
            "vendor_id": a.vendor_id,
            "vendor_name": a.vendor_name,
            "severity": a.severity,
            "message": a.message,
            "triggered_at": a.triggered_at.isoformat(),
            "metadata": a.metadata
        }
        for a in alerts
    ])


@router.get("/rules")
async def get_alert_rules(
    current_user: User = Depends(get_current_user),
):
    """
    获取告警规则定义
    """
    return ApiResponse(data=AlertEngine.get_rule_descriptions())


@router.post("/evaluate/{vendor_id}")
async def evaluate_vendor_alerts(
    vendor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    手动触发供应商告警评估
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可触发告警评估")

    vendor_result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id)
    )
    vendor = vendor_result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="供应商不存在")

    alerts = await AlertEngine.evaluate_vendor(vendor_id, db)

    return ApiResponse(data={
        "vendor_id": vendor_id,
        "vendor_name": vendor.name,
        "alerts_count": len(alerts),
        "alerts": [
            {
                "rule_id": a.rule_id,
                "severity": a.severity,
                "message": a.message,
                "triggered_at": a.triggered_at.isoformat()
            }
            for a in alerts
        ]
    })


@router.post("/evaluate-all")
async def evaluate_all_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    批量评估所有供应商告警
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可批量评估告警")

    alerts = await AlertEngine.evaluate_all_vendors(db)

    # 统计
    critical_count = len([a for a in alerts if a.severity == "critical"])
    warning_count = len([a for a in alerts if a.severity == "warning"])

    return ApiResponse(data={
        "total_alerts": len(alerts),
        "critical_alerts": critical_count,
        "warning_alerts": warning_count,
        "alerts": [
            {
                "rule_id": a.rule_id,
                "vendor_id": a.vendor_id,
                "vendor_name": a.vendor_name,
                "severity": a.severity,
                "message": a.message
            }
            for a in alerts
        ]
    })

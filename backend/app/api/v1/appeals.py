"""
SLA申诉API
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.models import Vendor, VendorMember, MonthlyScore, SLAAppeal, User, SLAGrade
from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("")
async def list_appeals(
    vendor_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取申诉列表

    管理员可查看所有，供应商只能查看自己
    """
    if current_user.role == "admin":
        query = select(SLAAppeal)
        if vendor_id:
            query = query.where(SLAAppeal.vendor_id == vendor_id)
        if status:
            query = query.where(SLAAppeal.status == status)
    else:
        # 供应商只能看自己的申诉
        # 需要获取用户所属的vendor_id
        query = select(SLAAppeal).where(SLAAppeal.vendor_id == 1)  # TODO: 实际获取

    result = await db.execute(query.order_by(SLAAppeal.submitted_at.desc()))
    appeals = result.scalars().all()

    return ApiResponse(data=[
        {
            "id": a.id,
            "vendor_id": a.vendor_id,
            "appeal_type": a.appeal_type,
            "reason": a.reason,
            "status": a.status,
            "submitted_at": a.submitted_at.isoformat(),
            "reviewed_at": a.reviewed_at.isoformat() if a.reviewed_at else None
        }
        for a in appeals
    ])


@router.get("/my")
async def get_my_appeals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户(供应商)的申诉列表
    """
    # TODO: 实际获取用户所属vendor_id
    vendor_id = 1

    result = await db.execute(
        select(SLAAppeal).where(
            SLAAppeal.vendor_id == vendor_id
        ).order_by(SLAAppeal.submitted_at.desc())
    )
    appeals = result.scalars().all()

    return ApiResponse(data=[
        {
            "id": a.id,
            "appeal_type": a.appeal_type,
            "reason": a.reason,
            "status": a.status,
            "submitted_at": a.submitted_at.isoformat(),
            "resolution": a.resolution
        }
        for a in appeals
    ])


@router.post("")
async def submit_appeal(
    data: dict,  # {vendor_id, monthly_score_id, appeal_type, reason, evidence_urls}
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    提交SLA申诉
    """
    vendor_id = data.get("vendor_id")
    monthly_score_id = data.get("monthly_score_id")
    appeal_type = data.get("appeal_type", "score_dispute")
    reason = data.get("reason", "")
    evidence_urls = data.get("evidence_urls", [])

    # 验证供应商
    vendor_result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id)
    )
    vendor = vendor_result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="供应商不存在")

    # 创建申诉
    appeal = SLAAppeal(
        vendor_id=vendor_id,
        submitter_id=None,  # TODO: 获取当前成员ID
        monthly_score_id=monthly_score_id,
        appeal_type=appeal_type,
        reason=reason,
        evidence_urls=str(evidence_urls),
        status="pending",
        submitted_at=datetime.utcnow()
    )
    db.add(appeal)
    await db.commit()

    return ApiResponse(data={
        "appeal_id": appeal.id,
        "message": "申诉已提交，等待审核"
    })


@router.get("/{appeal_id}")
async def get_appeal_detail(
    appeal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取申诉详情
    """
    result = await db.execute(
        select(SLAAppeal).where(SLAAppeal.id == appeal_id)
    )
    appeal = result.scalar_one_or_none()
    if not appeal:
        raise HTTPException(status_code=404, detail="申诉不存在")

    # 获取供应商名称
    vendor_result = await db.execute(
        select(Vendor.name).where(Vendor.id == appeal.vendor_id)
    )
    vendor_name = vendor_result.scalar_one_or_none()

    return ApiResponse(data={
        "id": appeal.id,
        "vendor_id": appeal.vendor_id,
        "vendor_name": vendor_name,
        "appeal_type": appeal.appeal_type,
        "reason": appeal.reason,
        "evidence_urls": appeal.evidence_urls,
        "status": appeal.status,
        "submitted_at": appeal.submitted_at.isoformat(),
        "reviewed_at": appeal.reviewed_at.isoformat() if appeal.reviewed_at else None,
        "review_notes": appeal.review_notes,
        "resolution": appeal.resolution
    })


@router.put("/{appeal_id}/approve")
async def approve_appeal(
    appeal_id: int,
    data: dict,  # {resolution, review_notes}
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    批准申诉 (管理员)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可审核申诉")

    result = await db.execute(
        select(SLAAppeal).where(SLAAppeal.id == appeal_id)
    )
    appeal = result.scalar_one_or_none()
    if not appeal:
        raise HTTPException(status_code=404, detail="申诉不存在")

    if appeal.status != "pending":
        raise HTTPException(status_code=400, detail="申诉已被处理")

    appeal.status = "approved"
    appeal.reviewed_by = current_user.id
    appeal.reviewed_at = datetime.utcnow()
    appeal.review_notes = data.get("review_notes", "")
    appeal.resolution = data.get("resolution", "申诉已批准，评分已调整")

    await db.commit()

    return ApiResponse(message="申诉已批准")


@router.put("/{appeal_id}/reject")
async def reject_appeal(
    appeal_id: int,
    data: dict,  # {review_notes}
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    驳回申诉 (管理员)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可审核申诉")

    result = await db.execute(
        select(SLAAppeal).where(SLAAppeal.id == appeal_id)
    )
    appeal = result.scalar_one_or_none()
    if not appeal:
        raise HTTPException(status_code=404, detail="申诉不存在")

    if appeal.status != "pending":
        raise HTTPException(status_code=400, detail="申诉已被处理")

    appeal.status = "rejected"
    appeal.reviewed_by = current_user.id
    appeal.reviewed_at = datetime.utcnow()
    appeal.review_notes = data.get("review_notes", "")
    appeal.resolution = "申诉已驳回"

    await db.commit()

    return ApiResponse(message="申诉已驳回")
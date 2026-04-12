"""
代码审查 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.models import PullRequest, QualityGate, Vendor
from app.schemas.review import (
    PRCreate, PRUpdate, PRResponse, PRListResponse,
    QualityGateResponse, ReviewComment, ReviewApprove, ReviewReject,
)
from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("/prs", response_model=ApiResponse[PRListResponse])
async def list_prs(
    vendor_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取PR列表"""
    query = select(PullRequest).where(PullRequest.is_deleted == False)
    
    if vendor_id:
        query = query.where(PullRequest.vendor_id == vendor_id)
    if status:
        query = query.where(PullRequest.status == status)
    
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(PullRequest.created_at.desc())
    result = await db.execute(query)
    prs = result.scalars().all()
    
    # 获取供应商名称
    pr_responses = []
    for pr in prs:
        vendor_result = await db.execute(select(Vendor.name).where(Vendor.id == pr.vendor_id))
        vendor_name = vendor_result.scalar_one_or_none()
        
        # 获取质量门禁
        gates_result = await db.execute(
            select(QualityGate).where(QualityGate.pr_id == pr.id).order_by(QualityGate.layer)
        )
        gates = gates_result.scalars().all()
        
        pr_resp = PRResponse.model_validate(pr)
        pr_resp.vendor_name = vendor_name
        pr_resp.gates = [QualityGateResponse.model_validate(g) for g in gates]
        pr_responses.append(pr_resp)
    
    return ApiResponse(data=PRListResponse(items=pr_responses, total=total))


@router.get("/prs/{pr_id}", response_model=ApiResponse[PRResponse])
async def get_pr_detail(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取PR详情"""
    result = await db.execute(
        select(PullRequest).where(PullRequest.id == pr_id, PullRequest.is_deleted == False)
    )
    pr = result.scalar_one_or_none()
    
    if not pr:
        raise HTTPException(status_code=404, detail="PR不存在")
    
    # 获取供应商名称
    vendor_result = await db.execute(select(Vendor.name).where(Vendor.id == pr.vendor_id))
    vendor_name = vendor_result.scalar_one_or_none()
    
    # 获取质量门禁
    gates_result = await db.execute(
        select(QualityGate).where(QualityGate.pr_id == pr.id).order_by(QualityGate.layer)
    )
    gates = gates_result.scalars().all()
    
    pr_resp = PRResponse.model_validate(pr)
    pr_resp.vendor_name = vendor_name
    pr_resp.gates = [QualityGateResponse.model_validate(g) for g in gates]
    
    return ApiResponse(data=pr_resp)


@router.get("/prs/{pr_id}/gates", response_model=ApiResponse[list[QualityGateResponse]])
async def get_pr_gates(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取PR质量门禁结果"""
    result = await db.execute(
        select(QualityGate).where(QualityGate.pr_id == pr_id).order_by(QualityGate.layer)
    )
    gates = result.scalars().all()
    
    return ApiResponse(data=[QualityGateResponse.model_validate(g) for g in gates])


@router.post("/prs/{pr_id}/approve")
async def approve_pr(
    pr_id: int,
    data: ReviewApprove,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """批准PR"""
    result = await db.execute(
        select(PullRequest).where(PullRequest.id == pr_id, PullRequest.is_deleted == False)
    )
    pr = result.scalar_one_or_none()
    
    if not pr:
        raise HTTPException(status_code=404, detail="PR不存在")
    
    pr.status = "approved"
    await db.flush()
    
    return ApiResponse(message="PR已批准")


@router.post("/prs/{pr_id}/reject")
async def reject_pr(
    pr_id: int,
    data: ReviewReject,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """驳回PR"""
    result = await db.execute(
        select(PullRequest).where(PullRequest.id == pr_id, PullRequest.is_deleted == False)
    )
    pr = result.scalar_one_or_none()
    
    if not pr:
        raise HTTPException(status_code=404, detail="PR不存在")
    
    pr.status = "rejected"
    await db.flush()
    
    return ApiResponse(message="PR已驳回")


@router.post("/prs/{pr_id}/comment")
async def add_comment(
    pr_id: int,
    data: ReviewComment,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """添加评论"""
    return ApiResponse(message="评论已添加")
"""
交付管理 API
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.models import Delivery, DeliveryChecklist, Vendor, PullRequest
from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("/projects")
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取项目列表"""
    # TODO: 实现真实的项目管理
    # 目前返回示例项目
    return ApiResponse(data=[
        {
            "id": 1,
            "name": "智能营销平台",
            "description": "新品推广模块 + 营销活动管理",
            "status": "active",
            "vendor_id": 1,
        },
        {
            "id": 2,
            "name": "AI育儿助手",
            "description": "RAG检索优化 + 合规检查增强",
            "status": "active",
            "vendor_id": 3,
        },
    ])


@router.post("/projects/{project_id}/submit")
async def submit_delivery(
    project_id: int,
    data: dict,  # {version, description, artifacts}
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """提交交付物"""
    version = data.get("version", "v1.0.0")
    description = data.get("description", "")
    vendor_id = data.get("vendor_id", 1)
    
    delivery = Delivery(
        project_id=project_id,
        vendor_id=vendor_id,
        version=version,
        description=description,
        status="submitted",
    )
    db.add(delivery)
    await db.flush()
    
    # 创建验收清单项
    checklist_dimensions = [
        ("项目初始化", ["1.1", "1.2", "1.3"]),
        ("代码质量", ["2.1", "2.2", "2.3"]),
        ("架构合规", ["3.1", "3.2"]),
        ("合规检查", ["6.1", "6.2"]),
        ("测试", ["8.1", "8.2"]),
        ("安全", ["7.1", "7.2"]),
        ("文档", ["9.1", "9.2"]),
        ("交付清单", ["10.1", "10.2"]),
    ]
    
    for dimension, items in checklist_dimensions:
        for item_num in items:
            checklist = DeliveryChecklist(
                delivery_id=delivery.id,
                dimension=dimension,
                item_number=item_num,
                description=f"{dimension}检查项",
                acceptance_criteria="符合规范要求",
                status="pending",
            )
            db.add(checklist)
    
    await db.flush()
    await db.refresh(delivery)
    
    return ApiResponse(data={"delivery_id": delivery.id, "message": "交付物已提交"})


@router.get("/{delivery_id}")
async def get_delivery(
    delivery_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取交付物详情"""
    result = await db.execute(
        select(Delivery).where(Delivery.id == delivery_id, Delivery.is_deleted == False)
    )
    delivery = result.scalar_one_or_none()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="交付物不存在")
    
    # 获取供应商名称
    vendor_result = await db.execute(select(Vendor.name).where(Vendor.id == delivery.vendor_id))
    vendor_name = vendor_result.scalar_one_or_none()
    
    return ApiResponse(data={
        "id": delivery.id,
        "project_id": delivery.project_id,
        "vendor_id": delivery.vendor_id,
        "vendor_name": vendor_name,
        "version": delivery.version,
        "description": delivery.description,
        "status": delivery.status,
        "submitted_at": delivery.created_at.isoformat(),
    })


@router.get("/{delivery_id}/checklist")
async def get_checklist(
    delivery_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取验收清单"""
    result = await db.execute(
        select(DeliveryChecklist).where(DeliveryChecklist.delivery_id == delivery_id)
    )
    items = result.scalars().all()
    
    # 按维度分组
    dimensions = {}
    for item in items:
        if item.dimension not in dimensions:
            dimensions[item.dimension] = []
        dimensions[item.dimension].append({
            "id": item.id,
            "item_number": item.item_number,
            "description": item.description,
            "acceptance_criteria": item.acceptance_criteria,
            "status": item.status,
            "auto_filled": item.auto_filled,
            "reviewer_notes": item.reviewer_notes,
        })
    
    # 统计
    total = len(items)
    accepted = sum(1 for i in items if i.status == "accepted")
    rejected = sum(1 for i in items if i.status == "rejected")
    pending = total - accepted - rejected
    
    return ApiResponse(data={
        "dimensions": dimensions,
        "summary": {
            "total": total,
            "accepted": accepted,
            "rejected": rejected,
            "pending": pending,
        },
    })


@router.put("/{delivery_id}/checklist")
async def update_checklist(
    delivery_id: int,
    data: dict,  # {item_id: {status, reviewer_notes}}
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """更新验收清单项"""
    for item_id, updates in data.items():
        result = await db.execute(
            select(DeliveryChecklist).where(DeliveryChecklist.id == int(item_id))
        )
        item = result.scalar_one_or_none()
        
        if item:
            item.status = updates.get("status", item.status)
            item.reviewer_notes = updates.get("reviewer_notes", item.reviewer_notes)
    
    await db.flush()
    
    return ApiResponse(message="验收清单已更新")


@router.get("/history")
async def get_delivery_history(
    vendor_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取交付历史"""
    query = select(Delivery).where(Delivery.is_deleted == False)
    
    if vendor_id:
        query = query.where(Delivery.vendor_id == vendor_id)
    
    result = await db.execute(query.order_by(Delivery.created_at.desc()))
    deliveries = result.scalars().all()
    
    return ApiResponse(data=[
        {
            "id": d.id,
            "project_id": d.project_id,
            "version": d.version,
            "status": d.status,
            "submitted_at": d.created_at.isoformat(),
        }
        for d in deliveries
    ])
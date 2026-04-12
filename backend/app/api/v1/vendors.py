"""
乙方管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.models import Vendor, VendorMember, VendorStatus, VendorType
from app.schemas.response import ApiResponse
from app.schemas.vendor import (
    MemberCreate,
    MemberResponse,
    VendorCreate,
    VendorListResponse,
    VendorResponse,
    VendorUpdate,
)

router = APIRouter()


@router.get("", response_model=ApiResponse[VendorListResponse])
async def list_vendors(
    vendor_type: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取乙方列表"""
    query = select(Vendor).where(Vendor.is_deleted == False)

    if vendor_type:
        query = query.where(Vendor.vendor_type == VendorType(vendor_type))
    if status:
        query = query.where(Vendor.status == VendorStatus(status))

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页查询
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    vendors = result.scalars().all()

    # 获取成员数量
    vendor_responses = []
    for v in vendors:
        member_count_result = await db.execute(
            select(func.count()).where(VendorMember.vendor_id == v.id, VendorMember.is_deleted == False)
        )
        member_count = member_count_result.scalar() or 0
        vendor_resp = VendorResponse.model_validate(v)
        vendor_resp.member_count = member_count
        vendor_responses.append(vendor_resp)

    return ApiResponse(data=VendorListResponse(
        items=vendor_responses,
        total=total,
    ))


@router.post("", response_model=ApiResponse[VendorResponse])
async def create_vendor(
    vendor_data: VendorCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """创建乙方"""
    vendor = Vendor(
        name=vendor_data.name,
        vendor_type=VendorType(vendor_data.vendor_type),
        contact_name=vendor_data.contact_name,
        contact_email=vendor_data.contact_email,
        github_org=vendor_data.github_org,
        contract_start=vendor_data.contract_start,
        contract_end=vendor_data.contract_end,
        status=VendorStatus.PENDING,
    )
    db.add(vendor)
    await db.flush()
    await db.refresh(vendor)

    return ApiResponse(data=VendorResponse.model_validate(vendor))


@router.get("/{vendor_id}", response_model=ApiResponse[VendorResponse])
async def get_vendor(
    vendor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取乙方详情"""
    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.is_deleted == False)
    )
    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(status_code=404, detail="乙方不存在")

    member_count_result = await db.execute(
        select(func.count()).where(VendorMember.vendor_id == vendor.id, VendorMember.is_deleted == False)
    )
    member_count = member_count_result.scalar() or 0

    vendor_resp = VendorResponse.model_validate(vendor)
    vendor_resp.member_count = member_count

    return ApiResponse(data=vendor_resp)


@router.put("/{vendor_id}", response_model=ApiResponse[VendorResponse])
async def update_vendor(
    vendor_id: int,
    vendor_data: VendorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """更新乙方"""
    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.is_deleted == False)
    )
    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(status_code=404, detail="乙方不存在")

    update_data = vendor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "vendor_type" and value:
            setattr(vendor, field, VendorType(value))
        elif field == "status" and value:
            setattr(vendor, field, VendorStatus(value))
        else:
            setattr(vendor, field, value)

    await db.flush()
    await db.refresh(vendor)

    return ApiResponse(data=VendorResponse.model_validate(vendor))


@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """删除乙方（软删除）"""
    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.is_deleted == False)
    )
    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(status_code=404, detail="乙方不存在")

    vendor.is_deleted = True
    await db.flush()

    return ApiResponse(message="删除成功")


@router.get("/{vendor_id}/members", response_model=ApiResponse[list[MemberResponse]])
async def list_vendor_members(
    vendor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取乙方成员列表"""
    result = await db.execute(
        select(VendorMember).where(
            VendorMember.vendor_id == vendor_id,
            VendorMember.is_deleted == False
        )
    )
    members = result.scalars().all()

    return ApiResponse(data=[MemberResponse.model_validate(m) for m in members])


@router.post("/{vendor_id}/members", response_model=ApiResponse[MemberResponse])
async def create_member(
    vendor_id: int,
    member_data: MemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """创建乙方成员"""
    member = VendorMember(
        vendor_id=vendor_id,
        name=member_data.name,
        email=member_data.email,
        role=member_data.role,
        github_username=member_data.github_username,
        status="pending",
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)

    return ApiResponse(data=MemberResponse.model_validate(member))

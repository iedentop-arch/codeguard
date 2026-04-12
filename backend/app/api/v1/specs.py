"""
规范管理 API
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.models import SpecDocument
from app.schemas.response import ApiResponse

router = APIRouter()

# 分类名称映射
CATEGORY_NAMES = {
    "overview": "总览与入驻",
    "general": "通用编码规范",
    "architecture": "架构设计规范",
    "ai_agents": "AI Agent规范",
    "skills": "Skill开发规范",
    "mcp": "MCP开发规范",
    "sub_agents": "子代理规范",
    "compliance": "合规法规",
    "templates": "模板与工具",
    "delivery": "交付验收",
    "sdlc": "SDLC角色提示词",
}


@router.get("/categories")
async def get_spec_categories(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取规范分类统计"""
    result = await db.execute(
        select(
            SpecDocument.category,
            func.count(SpecDocument.id).label("count")
        )
        .where(SpecDocument.is_deleted == False)
        .group_by(SpecDocument.category)
        .order_by(func.count(SpecDocument.id).desc())
    )
    categories = result.all()

    return ApiResponse(data=[
        {
            "category": c.category,
            "name": CATEGORY_NAMES.get(c.category, c.category),
            "count": c.count,
        }
        for c in categories
    ])


@router.get("")
async def list_specs(
    category: str | None = Query(None),
    vendor_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取规范列表"""
    query = select(SpecDocument).where(SpecDocument.is_deleted == False)

    if category:
        query = query.where(SpecDocument.category == category)
    if vendor_type:
        query = query.where(SpecDocument.vendor_types.contains(vendor_type))

    result = await db.execute(query)
    specs = result.scalars().all()

    return ApiResponse(data=[
        {
            "id": s.id,
            "title": s.title,
            "file_path": s.file_path,
            "category": s.category,
            "vendor_types": s.vendor_types,
            "read_time": s.read_time,
            "is_required": s.is_required,
            "version": s.version,
        }
        for s in specs
    ])


@router.get("/by-vendor-type/{vendor_type}")
async def get_specs_by_vendor_type(
    vendor_type: str,
    db: AsyncSession = Depends(get_db),
):
    """按乙方类型获取规范"""
    result = await db.execute(
        select(SpecDocument).where(
            SpecDocument.vendor_types.contains(vendor_type),
            SpecDocument.is_deleted == False
        ).order_by(SpecDocument.is_required.desc(), SpecDocument.category)
    )
    specs = result.scalars().all()

    return ApiResponse(data=[
        {
            "id": s.id,
            "title": s.title,
            "file_path": s.file_path,
            "category": s.category,
            "vendor_types": s.vendor_types,
            "read_time": s.read_time,
            "is_required": s.is_required,
        }
        for s in specs
    ])


@router.get("/{spec_id}")
async def get_spec(
    spec_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取规范详情"""
    result = await db.execute(
        select(SpecDocument).where(SpecDocument.id == spec_id, SpecDocument.is_deleted == False)
    )
    spec = result.scalar_one_or_none()

    if not spec:
        return ApiResponse(code=404, message="规范不存在")

    return ApiResponse(data={
        "id": spec.id,
        "title": spec.title,
        "file_path": spec.file_path,
        "category": spec.category,
        "vendor_types": spec.vendor_types,
        "content": spec.content,
        "read_time": spec.read_time,
        "is_required": spec.is_required,
        "version": spec.version,
    })

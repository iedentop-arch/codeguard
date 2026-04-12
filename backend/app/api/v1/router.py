"""
API v1 路由聚合
"""
from fastapi import APIRouter

# Phase 2 新增路由
# Phase 3 新增路由
from app.api.v1 import (
    alerts,
    appeals,
    auth,
    config,
    deliverables,
    health,
    metrics,
    reviews,
    sla,
    specs,
    training,
    vendors,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["乙方管理"])
api_router.include_router(specs.router, prefix="/specs", tags=["规范管理"])
api_router.include_router(training.router, prefix="/training", tags=["入驻培训"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["代码审查"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["SLA指标"])
api_router.include_router(deliverables.router, prefix="/deliverables", tags=["交付管理"])
# Phase 2 新增
api_router.include_router(sla.router, prefix="/sla", tags=["SLA评分"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["告警管理"])
# Phase 3 新增
api_router.include_router(appeals.router, prefix="/appeals", tags=["SLA申诉"])
api_router.include_router(config.router, prefix="/config", tags=["系统配置"])
# Webhook 路由无需认证，GitHub 直接调用
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhook"])

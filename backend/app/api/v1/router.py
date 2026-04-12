"""
API v1 路由聚合
"""
from fastapi import APIRouter

from app.api.v1 import auth, vendors, specs, training, reviews, metrics, deliverables, webhooks, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["乙方管理"])
api_router.include_router(specs.router, prefix="/specs", tags=["规范管理"])
api_router.include_router(training.router, prefix="/training", tags=["入驻培训"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["代码审查"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["SLA指标"])
api_router.include_router(deliverables.router, prefix="/deliverables", tags=["交付管理"])
# Webhook 路由无需认证，GitHub 直接调用
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhook"])
"""
CodeGuard Backend Application
乙方代码管理系统后端服务

Author: AI-Assisted: 80% (初始结构由 AI 生成)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.core.config import settings, get_private_key
from app.core.database import init_db
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库连接
    await init_db()
    yield
    # 关闭时清理资源


app = FastAPI(
    title="CodeGuard API",
    description="乙方代码管理系统 API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """
    服务健康检查端点
    
    包含 GitHub App 配置状态摘要
    """
    private_key = get_private_key()
    
    github_ready = all([
        settings.GITHUB_APP_ID and not settings.GITHUB_APP_ID.startswith("placeholder"),
        private_key,
        settings.GITHUB_WEBHOOK_SECRET,
        settings.GITHUB_APP_INSTALLATION_ID > 0,
    ])
    
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "github_app": {
            "configured": github_ready,
            "app_id": settings.GITHUB_APP_ID if not settings.GITHUB_APP_ID.startswith("placeholder") else "not_set",
            "private_key": "configured" if private_key else "not_set",
            "webhook_secret": "configured" if settings.GITHUB_WEBHOOK_SECRET else "not_set",
            "installation_id": settings.GITHUB_APP_INSTALLATION_ID if settings.GITHUB_APP_INSTALLATION_ID > 0 else "not_set",
        },
    }


@app.get("/health/github")
async def github_config_status():
    """
    GitHub App 配置详细检查
    
    返回配置检查清单和下一步操作指引
    """
    private_key = get_private_key()
    
    checks = [
        {
            "item": "GITHUB_APP_ID",
            "status": "pass" if settings.GITHUB_APP_ID and not settings.GITHUB_APP_ID.startswith("placeholder") else "fail",
            "value": settings.GITHUB_APP_ID if not settings.GITHUB_APP_ID.startswith("placeholder") else None,
        },
        {
            "item": "GITHUB_APP_PRIVATE_KEY",
            "status": "pass" if private_key else "fail",
            "hint": "保存私钥到 backend/private-key.pem",
        },
        {
            "item": "GITHUB_WEBHOOK_SECRET",
            "status": "pass" if settings.GITHUB_WEBHOOK_SECRET else "fail",
            "value": settings.GITHUB_WEBHOOK_SECRET or None,
        },
        {
            "item": "GITHUB_APP_INSTALLATION_ID",
            "status": "pass" if settings.GITHUB_APP_INSTALLATION_ID > 0 else "fail",
            "value": settings.GITHUB_APP_INSTALLATION_ID,
        },
    ]
    
    passed = sum(1 for c in checks if c["status"] == "pass")
    
    return {
        "summary": {
            "passed": passed,
            "total": len(checks),
            "ready": passed == len(checks),
        },
        "checks": checks,
        "next_steps": [
            "1. ngrok config add-authtoken <your-token>",
            "2. ngrok http 8000",
            "3. 在 https://github.com/settings/apps 创建 GitHub App",
            "4. Webhook URL: https://<ngrok-id>.ngrok-free.app/api/v1/webhooks/github",
            "5. Webhook Secret: codeguard-webhook-secret-2024",
            "6. 下载私钥保存到 backend/private-key.pem",
            "7. 安装 App 到仓库，获取 Installation ID",
            "8. 运行 ./verify_github_app_config.sh 验证配置",
        ],
    }
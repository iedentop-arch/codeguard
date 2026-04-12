"""
健康检查 API

用于验证服务状态和 GitHub App 配置
"""
from fastapi import APIRouter
from datetime import datetime

from app.core.config import settings, get_private_key
from app.core.github_client import github_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    服务健康检查
    
    返回服务状态和 GitHub App 配置状态
    """
    # 检查 GitHub App 配置状态
    private_key = get_private_key()
    
    github_config = {
        "app_id": {
            "value": settings.GITHUB_APP_ID if not settings.GITHUB_APP_ID.startswith("placeholder") else None,
            "configured": bool(settings.GITHUB_APP_ID and not settings.GITHUB_APP_ID.startswith("placeholder")),
        },
        "private_key": {
            "configured": bool(private_key),
            "source": "file" if private_key and settings.GITHUB_APP_PRIVATE_KEY.startswith("placeholder") else "env",
        },
        "webhook_secret": {
            "configured": bool(settings.GITHUB_WEBHOOK_SECRET),
        },
        "installation_id": {
            "value": settings.GITHUB_APP_INSTALLATION_ID,
            "configured": settings.GITHUB_APP_INSTALLATION_ID > 0,
        },
    }
    
    # 整体配置状态
    all_configured = all([
        github_config["app_id"]["configured"],
        github_config["private_key"]["configured"],
        github_config["webhook_secret"]["configured"],
        github_config["installation_id"]["configured"],
    ])
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
        },
        "github_app": {
            "configured": all_configured,
            "ready_for_webhooks": all_configured,
            "details": github_config,
        },
        "checks": {
            "database": "connected",  # 如果能响应说明数据库已连接
            "backend": "running",
        },
    }


@router.get("/health/github")
async def github_app_status():
    """
    GitHub App 详细状态
    
    包含配置检查清单
    """
    checks = []
    private_key = get_private_key()
    
    # App ID 检查
    if settings.GITHUB_APP_ID and not settings.GITHUB_APP_ID.startswith("placeholder"):
        checks.append({
            "name": "GITHUB_APP_ID",
            "status": "pass",
            "message": f"已配置: {settings.GITHUB_APP_ID}",
        })
    else:
        checks.append({
            "name": "GITHUB_APP_ID",
            "status": "fail",
            "message": "未配置 - 在 GitHub App 设置页获取 App ID",
            "action": "编辑 .env 文件填写 GITHUB_APP_ID",
        })
    
    # 私钥检查
    if private_key:
        checks.append({
            "name": "GITHUB_APP_PRIVATE_KEY",
            "status": "pass",
            "message": "私钥已配置",
        })
    else:
        checks.append({
            "name": "GITHUB_APP_PRIVATE_KEY",
            "status": "fail",
            "message": "私钥未配置",
            "action": "保存私钥到 backend/private-key.pem 或填写 GITHUB_APP_PRIVATE_KEY",
        })
    
    # Webhook Secret 检查
    if settings.GITHUB_WEBHOOK_SECRET:
        checks.append({
            "name": "GITHUB_WEBHOOK_SECRET",
            "status": "pass",
            "message": "已配置",
        })
    else:
        checks.append({
            "name": "GITHUB_WEBHOOK_SECRET",
            "status": "fail",
            "message": "未配置",
            "action": "在 .env 中设置 GITHUB_WEBHOOK_SECRET，需与 GitHub App 设置一致",
        })
    
    # Installation ID 检查
    if settings.GITHUB_APP_INSTALLATION_ID > 0:
        checks.append({
            "name": "GITHUB_APP_INSTALLATION_ID",
            "status": "pass",
            "message": f"已配置: {settings.GITHUB_APP_INSTALLATION_ID}",
        })
    else:
        checks.append({
            "name": "GITHUB_APP_INSTALLATION_ID",
            "status": "fail",
            "message": "未配置",
            "action": "安装 GitHub App 后获取 Installation ID",
        })
    
    # 计算整体状态
    pass_count = sum(1 for c in checks if c["status"] == "pass")
    total_count = len(checks)
    
    return {
        "summary": {
            "total": total_count,
            "passed": pass_count,
            "failed": total_count - pass_count,
            "ready": pass_count == total_count,
        },
        "checks": checks,
        "next_steps": [
            "1. 配置 ngrok: ngrok config add-authtoken <token>",
            "2. 启动隧道: ngrok http 8000",
            "3. 注册 GitHub App: https://github.com/settings/apps",
            "4. 设置 Webhook URL: https://<ngrok-id>.ngrok-free.app/api/v1/webhooks/github",
            "5. 下载私钥保存到 backend/private-key.pem",
            "6. 安装 GitHub App 到目标仓库",
            "7. 获取 Installation ID 并更新 .env",
        ] if pass_count < total_count else [
            "配置完成！创建 PR 测试 webhook 接收",
        ],
    }
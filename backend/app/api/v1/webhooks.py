"""
GitHub Webhook 接收端点

接收 GitHub App 发送的 webhook 事件，处理：
- pull_request 事件 (opened, synchronize, closed)
- check_run 事件 (CI 完成)
- workflow_run 事件 (GitHub Actions 完成)
"""
import json
import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.pr_processor import handle_pull_request_event, handle_check_run_event, handle_workflow_run_event

logger = logging.getLogger(__name__)

router = APIRouter()


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    验证 GitHub Webhook HMAC-SHA256 签名
    
    GitHub 使用 webhook secret 对请求体进行 HMAC-SHA256 签名
    签名格式: sha256=<hex_digest>
    """
    if not settings.GITHUB_WEBHOOK_SECRET:
        logger.warning("GITHUB_WEBHOOK_SECRET not configured, skipping signature verification")
        return True  # 开发环境下跳过验证

    secret = settings.GITHUB_WEBHOOK_SECRET.encode()
    expected_signature = hmac.new(secret, body, hashlib.sha256).hexdigest()
    expected = f"sha256={expected_signature}"

    return hmac.compare_digest(expected, signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: str = Header(..., alias="X-Hub-Signature-256"),
    x_github_delivery: str = Header(None, alias="X-GitHub-Delivery"),
):
    """
    接收 GitHub Webhook 事件
    
    该端点无需认证，由 GitHub 直接调用
    所有事件立即返回 200，异步处理
    """
    # 读取原始请求体
    body = await request.body()

    # 验证签名
    if not verify_webhook_signature(body, x_hub_signature_256):
        logger.error("Webhook signature verification failed")
        raise HTTPException(status_code=403, detail="Invalid signature")

    # 解析 payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.error("Failed to parse webhook payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 记录事件
    logger.info(
        f"Received GitHub webhook: event={x_github_event}, delivery={x_github_delivery}"
    )

    # 分发事件处理
    try:
        if x_github_event == "pull_request":
            await handle_pull_request_event(payload, db)
        elif x_github_event == "check_run":
            await handle_check_run_event(payload, db)
        elif x_github_event == "workflow_run":
            await handle_workflow_run_event(payload, db)
        elif x_github_event == "ping":
            # GitHub App 安装时发送 ping 事件
            logger.info(f"GitHub App ping received: {payload.get('zen', '')}")
        else:
            logger.info(f"Unhandled event type: {x_github_event}")
    except Exception as e:
        # 处理失败不影响返回 200（避免 GitHub 重试）
        logger.error(f"Error processing webhook event: {e}", exc_info=True)

    return {"status": "ok", "event": x_github_event}
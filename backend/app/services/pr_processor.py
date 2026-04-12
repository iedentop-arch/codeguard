"""
PR 事件处理器

处理 GitHub pull_request webhook 事件：
- opened/synchronize: 创建 PR 记录，触发质量门禁
- closed (merged): 更新状态，触发 SLA 评分
- closed (not merged): 标记为已关闭
"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.github_client import github_client
from app.models.models import PullRequest, Vendor
from app.services.quality_gates import run_quality_gates

logger = logging.getLogger(__name__)


async def handle_pull_request_event(payload: dict, db: AsyncSession):
    """
    处理 pull_request 事件
    
    Args:
        payload: GitHub webhook payload
        db: 数据库 session
    """
    action = payload.get("action")
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})

    owner = repo_data.get("owner", {}).get("login")
    repo = repo_data.get("name")
    pr_number = pr_data.get("number")

    logger.info(f"Processing PR #{pr_number} in {owner}/{repo}, action={action}")

    if action in ("opened", "synchronize"):
        await process_new_pr(payload, db)
    elif action == "closed":
        if pr_data.get("merged"):
            await process_merged_pr(payload, db)
        else:
            await process_closed_pr(payload, db)


async def process_new_pr(payload: dict, db: AsyncSession):
    """
    处理新建/更新的 PR
    
    1. 根据 repo owner 匹配 Vendor.github_org
    2. 创建/更新 PullRequest 记录
    3. 设置 commit status 为 pending
    4. 触发质量门禁检查
    """
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    owner = repo_data.get("owner", {}).get("login")
    repo = repo_data.get("name")
    pr_number = pr_data.get("number")

    # 查找匹配的 Vendor
    result = await db.execute(
        select(Vendor).where(Vendor.github_org == owner, Vendor.is_deleted == False)
    )
    vendor = result.scalar_one_or_none()

    if not vendor:
        logger.warning(f"No vendor found for github_org={owner}")
        return

    # 检查是否已有 PR 记录
    result = await db.execute(
        select(PullRequest).where(
            PullRequest.vendor_id == vendor.id,
            PullRequest.github_pr_number == pr_number,
            PullRequest.is_deleted == False,
        )
    )
    existing_pr = result.scalar_one_or_none()

    # PR 数据
    head_sha = pr_data.get("head", {}).get("sha")

    if existing_pr:
        # 更新现有 PR
        existing_pr.title = pr_data.get("title")
        existing_pr.branch = pr_data.get("head", {}).get("ref")
        existing_pr.lines_added = pr_data.get("additions", 0)
        existing_pr.lines_removed = pr_data.get("deletions", 0)
        existing_pr.files_changed = pr_data.get("changed_files", 0)
        existing_pr.head_sha = head_sha
        existing_pr.status = "ci_checking"
        pr_record = existing_pr
        logger.info(f"Updated existing PR #{pr_number} (ID={existing_pr.id})")
    else:
        # 创建新 PR
        pr_record = PullRequest(
            vendor_id=vendor.id,
            github_pr_number=pr_number,
            github_pr_url=pr_data.get("html_url"),
            head_sha=head_sha,
            title=pr_data.get("title"),
            branch=pr_data.get("head", {}).get("ref"),
            status="ci_checking",
            lines_added=pr_data.get("additions", 0),
            lines_removed=pr_data.get("deletions", 0),
            files_changed=pr_data.get("changed_files", 0),
            has_ai_code=False,
            ai_code_marked=True,
            is_deleted=False,
        )
        db.add(pr_record)
        await db.flush()
        logger.info(f"Created new PR #{pr_number} (ID={pr_record.id})")

    await db.commit()

    # 设置 GitHub commit status 为 pending
    if github_client.is_configured() and pr_record.head_sha:
        try:
            await github_client.create_commit_status(
                owner=owner,
                repo=repo,
                sha=pr_record.head_sha,
                state="pending",
                context="CodeGuard/QualityGates",
                description="Running quality gate checks...",
            )
        except Exception as e:
            logger.error(f"Failed to set commit status: {e}")

        # 获取 PR diff 并运行质量门禁
        try:
            pr_diff = await github_client.get_pr_diff(owner, repo, pr_number)
            await run_quality_gates(pr_record, pr_diff, db, owner, repo, pr_record.head_sha)
        except Exception as e:
            logger.error(f"Failed to run quality gates: {e}")
    else:
        logger.info("GitHub client not configured, skipping commit status and quality gates")


async def process_merged_pr(payload: dict, db: AsyncSession):
    """
    处理已合并的 PR
    
    1. 更新 PR 状态为 merged
    2. 记录合并时间
    3. 触发 SLA 评分更新 (TODO)
    """
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    owner = repo_data.get("owner", {}).get("login")
    pr_number = pr_data.get("number")

    # 查找 PR 记录
    result = await db.execute(
        select(PullRequest).where(
            PullRequest.github_pr_number == pr_number,
            PullRequest.is_deleted == False,
        )
    )
    pr_record = result.scalar_one_or_none()

    if not pr_record:
        logger.warning(f"PR #{pr_number} not found in database")
        return

    pr_record.status = "merged"
    pr_record.merged_at = datetime.utcnow()

    await db.commit()
    logger.info(f"PR #{pr_number} marked as merged")

    # TODO: 触发 SLA 评分更新


async def process_closed_pr(payload: dict, db: AsyncSession):
    """
    处理已关闭但未合并的 PR
    """
    pr_data = payload.get("pull_request", {})
    pr_number = pr_data.get("number")

    # 查找 PR 记录
    result = await db.execute(
        select(PullRequest).where(
            PullRequest.github_pr_number == pr_number,
            PullRequest.is_deleted == False,
        )
    )
    pr_record = result.scalar_one_or_none()

    if not pr_record:
        logger.warning(f"PR #{pr_number} not found in database")
        return

    pr_record.status = "closed"

    await db.commit()
    logger.info(f"PR #{pr_number} marked as closed")


async def handle_check_run_event(payload: dict, db: AsyncSession):
    """
    处理 check_run 事件 (CI 完成)
    
    当 GitHub Actions 或其他 CI 完成时，更新对应质量门禁状态
    """
    action = payload.get("action")
    check_run = payload.get("check_run", {})

    if action == "completed":
        status = check_run.get("conclusion")  # success, failure, cancelled, timed_out
        name = check_run.get("name")

        # 查找 PR
        pull_requests = check_run.get("pull_requests", [])
        if pull_requests:
            pr_number = pull_requests[0].get("number")
            logger.info(f"Check run '{name}' completed with status={status} for PR #{pr_number}")

            # TODO: 更新对应的质量门禁状态
        else:
            logger.info(f"Check run '{name}' completed (no PR associated)")


async def handle_workflow_run_event(payload: dict, db: AsyncSession):
    """
    处理 workflow_run 事件 (GitHub Actions workflow 完成)
    
    当 GitHub Actions workflow 完成时，更新 L4_METRICS 门禁状态
    """
    action = payload.get("action")
    workflow_run = payload.get("workflow_run", {})

    if action == "completed":
        conclusion = workflow_run.get("conclusion")
        name = workflow_run.get("name")

        # 查找 PR
        pull_requests = workflow_run.get("pull_requests", [])
        if pull_requests:
            pr_number = pull_requests[0].get("number")
            logger.info(f"Workflow '{name}' completed with conclusion={conclusion} for PR #{pr_number}")

            # TODO: 更新 L4_METRICS 门禁状态
        else:
            logger.info(f"Workflow '{name}' completed (no PR associated)")

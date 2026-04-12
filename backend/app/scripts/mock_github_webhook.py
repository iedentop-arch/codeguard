"""
模拟 GitHub Webhook 事件脚本
用于本地开发测试，无需配置真实的 GitHub App
"""
import asyncio

from app.core.database import async_session_maker
from app.models.models import PullRequest, QualityGate, Vendor


async def mock_pr_webhook():
    """模拟 PR 创建事件"""
    print("模拟 GitHub PR Webhook 事件...")

    # 模拟 PR 数据
    pr_data = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "id": 123456789,
            "number": 42,
            "title": "feat: 新增用户认证模块",
            "html_url": "https://github.com/example/repo/pull/42",
            "state": "open",
            "user": {"login": "vendor-dev"},
            "head": {"ref": "feature/auth"},
            "base": {"ref": "main"},
            "additions": 150,
            "deletions": 20,
            "changed_files": 8,
        },
        "repository": {"full_name": "example/repo"},
    }

    async with async_session_maker() as session:
        # 检查是否有乙方
        from sqlalchemy import select
        result = await session.execute(select(Vendor).limit(1))
        vendor = result.scalar_one_or_none()

        if not vendor:
            # 创建测试乙方
            vendor = Vendor(
                name="测试乙方-A",
                vendor_type="C",
                status="active",
                contact_name="张三",
                contact_email="vendor@example.com",
                github_org="example",
                is_deleted=False,
            )
            session.add(vendor)
            await session.flush()
            print(f"创建测试乙方: {vendor.name} (ID: {vendor.id})")

        # 创建 PR 记录
        pr = PullRequest(
            vendor_id=vendor.id,
            github_pr_number=pr_data["number"],
            github_pr_url=pr_data["pull_request"]["html_url"],
            title=pr_data["pull_request"]["title"],
            branch=pr_data["pull_request"]["head"]["ref"],
            status="pending",
            lines_added=pr_data["pull_request"]["additions"],
            lines_removed=pr_data["pull_request"]["deletions"],
            files_changed=pr_data["pull_request"]["changed_files"],
            has_ai_code=False,
            is_deleted=False,
        )
        session.add(pr)
        await session.flush()
        print(f"创建 PR: #{pr.github_pr_number} - {pr.title}")

        # 模拟六层质量门禁检查结果
        gates = [
            ("L1_RED_LINE", "红线检查", "passed", "无 CRITICAL 规范违规"),
            ("L2_MANDATORY", "强制检查", "passed", "类型注解完整，API 文档完整"),
            ("L3_AI_ASSISTED", "AI辅助审查", "passed", "代码质量评分 85/100"),
            ("L4_METRICS", "度量检查", "warning", "测试覆盖率 65%，低于目标 80%"),
            ("L5_DOCUMENTATION", "文档检查", "passed", "README 和 CHANGELOG 已更新"),
            ("L6_COMPLIANCE", "合规检查", "passed", "无广告法违规内容"),
        ]

        for gate_id, gate_name, status, detail in gates:
            gate = QualityGate(
                pr_id=pr.id,
                gate_id=gate_id,
                gate_name=gate_name,
                status=status,
                detail=detail,
                is_deleted=False,
            )
            session.add(gate)
            print(f"  质量门禁 [{gate_name}]: {status}")

        await session.commit()
        print("\n模拟完成！PR 数据已入库。")


async def mock_pr_merge_webhook():
    """模拟 PR 合并事件"""
    print("\n模拟 GitHub PR Merge Webhook 事件...")
    print("PR #42 已合并到 main 分支")
    print("触发 SLA 评分更新...")


if __name__ == "__main__":
    print("=== GitHub Webhook 模拟工具 ===")
    print("用于本地开发测试，无需配置真实的 GitHub App")
    print("=" * 40)
    asyncio.run(mock_pr_webhook())
    asyncio.run(mock_pr_merge_webhook())

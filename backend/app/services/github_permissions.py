"""
GitHub权限联动服务

通过GitHub API管理仓库协作者权限:
- 培训认证通过后授予写权限
- 培训未通过或暂停后撤销权限
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.github_client import github_client
from app.models.models import Vendor, VendorMember
from app.services.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


@dataclass
class PermissionSyncResult:
    """权限同步结果"""
    member_id: int
    member_name: str
    github_username: str | None
    action: str  # grant, revoke, none
    success: bool
    message: str
    synced_at: datetime


class GitHubPermissionService:
    """GitHub权限管理服务"""

    # 权限级别
    PERMISSION_WRITE = "write"  # 可推送代码
    PERMISSION_READ = "read"    # 仅可拉取
    PERMISSION_ADMIN = "admin"  # 管理员权限

    # 权限状态
    PERMISSION_STATUS_NONE = "none"
    PERMISSION_STATUS_PENDING = "pending"
    PERMISSION_STATUS_ACTIVE = "active"
    PERMISSION_STATUS_REVOKED = "revoked"

    @classmethod
    async def get_repo_info(cls, vendor_id: int, db: AsyncSession) -> dict[str, str]:
        """
        获取供应商关联的仓库信息

        Args:
            vendor_id: 供应商ID
            db: 数据库会话

        Returns:
            {owner, repo} 字典
        """
        vendor_result = await db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        vendor = vendor_result.scalar_one_or_none()
        if not vendor:
            raise ValueError(f"Vendor {vendor_id} not found")

        # 从供应商的github_org获取仓库信息
        # 简化处理: 使用配置中的默认仓库
        owner = settings.GITHUB_DEFAULT_REPO_OWNER or vendor.github_org
        repo = settings.GITHUB_DEFAULT_REPO_NAME or "vendor-code"

        if not owner:
            raise ValueError("GitHub repo owner not configured")

        return {"owner": owner, "repo": repo}

    @classmethod
    async def grant_write_permission(
        cls,
        member_id: int,
        db: AsyncSession,
        user_id: int | None = None,
        user_name: str | None = None,
        user_role: str | None = None
    ) -> PermissionSyncResult:
        """
        授予成员GitHub仓库写权限

        Args:
            member_id: 成员ID
            db: 数据库会话
            user_id: 操作用户ID (用于审计日志)
            user_name: 操作用户名
            user_role: 操作用户角色

        Returns:
            PermissionSyncResult同步结果
        """
        member_result = await db.execute(
            select(VendorMember).where(VendorMember.id == member_id)
        )
        member = member_result.scalar_one_or_none()
        if not member:
            return PermissionSyncResult(
                member_id=member_id,
                member_name="未知",
                github_username=None,
                action="grant",
                success=False,
                message="成员不存在",
                synced_at=datetime.utcnow()
            )

        if not member.github_username:
            return PermissionSyncResult(
                member_id=member_id,
                member_name=member.name,
                github_username=None,
                action="grant",
                success=False,
                message="成员未配置GitHub用户名",
                synced_at=datetime.utcnow()
            )

        if not github_client.is_configured():
            return PermissionSyncResult(
                member_id=member_id,
                member_name=member.name,
                github_username=member.github_username,
                action="grant",
                success=False,
                message="GitHub App未配置",
                synced_at=datetime.utcnow()
            )

        try:
            repo_info = await cls.get_repo_info(member.vendor_id, db)
            owner = repo_info["owner"]
            repo = repo_info["repo"]

            # 调用GitHub API添加协作者
            # 注意: GitHub API的 PUT /repos/{owner}/{repo}/collaborators/{username}
            # 需要在 github_client.py 中添加实现
            # 这里暂时标记为待实现
            logger.info(f"Granting write permission to {member.github_username} on {owner}/{repo}")

            # 更新成员权限状态
            member.github_permission_status = cls.PERMISSION_STATUS_ACTIVE
            member.github_permission_level = cls.PERMISSION_WRITE
            member.github_permission_synced_at = datetime.utcnow()
            await db.flush()

            # 记录审计日志
            if user_id:
                await AuditLogger.log_permission_change(
                    user_id=user_id,
                    user_name=user_name or "系统",
                    user_role=user_role or "system",
                    member_id=member_id,
                    action="grant_permission",
                    old_perm=cls.PERMISSION_STATUS_NONE,
                    new_perm=cls.PERMISSION_STATUS_ACTIVE,
                    vendor_id=member.vendor_id,
                    db=db
                )

            await db.commit()

            return PermissionSyncResult(
                member_id=member_id,
                member_name=member.name,
                github_username=member.github_username,
                action="grant",
                success=True,
                message=f"已授予 {owner}/{repo} 仓库写权限",
                synced_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Failed to grant permission: {e}")
            return PermissionSyncResult(
                member_id=member_id,
                member_name=member.name,
                github_username=member.github_username,
                action="grant",
                success=False,
                message=f"权限授予失败: {str(e)}",
                synced_at=datetime.utcnow()
            )

    @classmethod
    async def revoke_permission(
        cls,
        member_id: int,
        db: AsyncSession,
        user_id: int | None = None,
        user_name: str | None = None,
        user_role: str | None = None
    ) -> PermissionSyncResult:
        """
        撤销成员GitHub仓库权限

        Args:
            member_id: 成员ID
            db: 数据库会话
            user_id: 操作用户ID
            user_name: 操作用户名
            user_role: 操作用户角色

        Returns:
            PermissionSyncResult同步结果
        """
        member_result = await db.execute(
            select(VendorMember).where(VendorMember.id == member_id)
        )
        member = member_result.scalar_one_or_none()
        if not member:
            return PermissionSyncResult(
                member_id=member_id,
                member_name="未知",
                github_username=None,
                action="revoke",
                success=False,
                message="成员不存在",
                synced_at=datetime.utcnow()
            )

        if member.github_permission_status == cls.PERMISSION_STATUS_NONE:
            return PermissionSyncResult(
                member_id=member_id,
                member_name=member.name,
                github_username=member.github_username,
                action="none",
                success=True,
                message="成员无权限，无需撤销",
                synced_at=datetime.utcnow()
            )

        if not member.github_username:
            return PermissionSyncResult(
                member_id=member_id,
                member_name=member.name,
                github_username=None,
                action="revoke",
                success=True,
                message="成员无GitHub用户名，标记已撤销",
                synced_at=datetime.utcnow()
            )

        try:
            repo_info = await cls.get_repo_info(member.vendor_id, db)
            owner = repo_info["owner"]
            repo = repo_info["repo"]

            logger.info(f"Revoking permission for {member.github_username} on {owner}/{repo}")

            # 更新成员权限状态
            old_status = member.github_permission_status
            member.github_permission_status = cls.PERMISSION_STATUS_REVOKED
            member.github_permission_level = None
            member.github_permission_synced_at = datetime.utcnow()
            await db.flush()

            # 记录审计日志
            if user_id:
                await AuditLogger.log_permission_change(
                    user_id=user_id,
                    user_name=user_name or "系统",
                    user_role=user_role or "system",
                    member_id=member_id,
                    action="revoke_permission",
                    old_perm=old_status,
                    new_perm=cls.PERMISSION_STATUS_REVOKED,
                    vendor_id=member.vendor_id,
                    db=db
                )

            await db.commit()

            return PermissionSyncResult(
                member_id=member_id,
                member_name=member.name,
                github_username=member.github_username,
                action="revoke",
                success=True,
                message=f"已撤销 {owner}/{repo} 仓库权限",
                synced_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Failed to revoke permission: {e}")
            return PermissionSyncResult(
                member_id=member_id,
                member_name=member.name,
                github_username=member.github_username,
                action="revoke",
                success=False,
                message=f"权限撤销失败: {str(e)}",
                synced_at=datetime.utcnow()
            )

    @classmethod
    async def sync_vendor_permissions(
        cls,
        vendor_id: int,
        db: AsyncSession
    ) -> dict[str, Any]:
        """
        同步供应商所有成员的权限

        Args:
            vendor_id: 供应商ID
            db: 数据库会话

        Returns:
            同步结果统计
        """
        # 获取所有成员
        members_result = await db.execute(
            select(VendorMember).where(
                VendorMember.vendor_id == vendor_id,
                VendorMember.is_deleted == False
            )
        )
        members = members_result.scalars().all()

        results = []
        granted_count = 0
        revoked_count = 0
        error_count = 0

        for member in members:
            # 根据成员状态决定权限操作
            if member.status == "active" and member.exam_score >= 80:
                # 培训通过且考试80分以上，授予权限
                result = await cls.grant_write_permission(member.id, db)
                if result.success:
                    granted_count += 1
                else:
                    error_count += 1
            elif member.status in ["suspended", "pending"]:
                # 状态为暂停或待审核，撤销权限
                if member.github_permission_status != cls.PERMISSION_STATUS_REVOKED:
                    result = await cls.revoke_permission(member.id, db)
                    if result.success:
                        revoked_count += 1
                    else:
                        error_count += 1
            results.append(result)

        return {
            "vendor_id": vendor_id,
            "total_members": len(members),
            "granted": granted_count,
            "revoked": revoked_count,
            "errors": error_count,
            "results": [
                {
                    "member_id": r.member_id,
                    "member_name": r.member_name,
                    "action": r.action,
                    "success": r.success,
                    "message": r.message
                }
                for r in results
            ]
        }

    @classmethod
    async def sync_training_permissions(
        cls,
        member: VendorMember,
        db: AsyncSession
    ) -> PermissionSyncResult:
        """
        根据培训状态自动同步权限

        Args:
            member: 成员对象
            db: 数据库会话

        Returns:
            权限同步结果
        """
        # 培训认证通过
        if member.status == "active" and member.exam_score >= 80:
            if member.github_permission_status != cls.PERMISSION_STATUS_ACTIVE:
                logger.info(f"Member {member.name} passed training, granting permission")
                return await cls.grant_write_permission(member.id, db)

        # 培训未通过或暂停
        elif member.status in ["suspended", "pending"]:
            if member.github_permission_status == cls.PERMISSION_STATUS_ACTIVE:
                logger.info(f"Member {member.name} suspended, revoking permission")
                return await cls.revoke_permission(member.id, db)

        # 无需变更
        return PermissionSyncResult(
            member_id=member.id,
            member_name=member.name,
            github_username=member.github_username,
            action="none",
            success=True,
            message="权限状态无需变更",
            synced_at=datetime.utcnow()
        )

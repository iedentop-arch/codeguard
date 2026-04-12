"""
审计日志服务

记录关键操作，支持追溯查询:
- PR审批操作
- 配置变更操作
- 权限授予操作
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    user_id: int
    user_name: str
    user_role: str
    action_type: str
    resource_type: str
    resource_id: int | None
    vendor_id: int | None
    old_value: dict | None
    new_value: dict | None
    description: str
    ip_address: str | None


class AuditLogger:
    """审计日志记录器"""

    # 关键操作类型
    ACTION_TYPES = {
        "approve_pr": "批准PR",
        "reject_pr": "驳回PR",
        "add_comment": "添加评论",
        "grant_permission": "授予权限",
        "revoke_permission": "撤销权限",
        "change_config": "变更配置",
        "create_vendor": "创建供应商",
        "update_vendor": "更新供应商",
        "delete_vendor": "删除供应商",
        "submit_delivery": "提交交付物",
        "approve_appeal": "批准申诉",
        "reject_appeal": "驳回申诉",
        "login": "用户登录",
        "logout": "用户登出",
    }

    # 资源类型
    RESOURCE_TYPES = {
        "pull_request": "PR",
        "vendor": "供应商",
        "vendor_member": "供应商成员",
        "delivery": "交付物",
        "appeal": "申诉",
        "config": "配置",
        "user": "用户",
    }

    @classmethod
    async def log_action(
        cls,
        entry: AuditLogEntry,
        db: AsyncSession
    ) -> int:
        """
        记录审计日志

        Args:
            entry: 日志条目
            db: 数据库会话

        Returns:
            日志ID
        """
        from app.models.models import AuditLog

        log = AuditLog(
            user_id=entry.user_id,
            user_name=entry.user_name,
            user_role=entry.user_role,
            action_type=entry.action_type,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            vendor_id=entry.vendor_id,
            old_value=json.dumps(entry.old_value) if entry.old_value else None,
            new_value=json.dumps(entry.new_value) if entry.new_value else None,
            description=entry.description,
            ip_address=entry.ip_address,
            created_at=datetime.utcnow()
        )
        db.add(log)
        await db.flush()

        logger.info(f"Audit log created: {entry.action_type} by {entry.user_name}")
        return log.id

    @classmethod
    async def log_pr_action(
        cls,
        user_id: int,
        user_name: str,
        user_role: str,
        pr_id: int,
        action: str,
        old_status: str,
        new_status: str,
        comment: str | None,
        vendor_id: int | None,
        db: AsyncSession
    ) -> int:
        """
        记录PR操作日志

        Args:
            user_id: 用户ID
            user_name: 用户名
            user_role: 用户角色
            pr_id: PR ID
            action: 操作类型
            old_status: 原状态
            new_status: 新状态
            comment: 评论内容
            vendor_id: 供应商ID
            db: 数据库会话

        Returns:
            日志ID
        """
        entry = AuditLogEntry(
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            action_type=action,
            resource_type="pull_request",
            resource_id=pr_id,
            vendor_id=vendor_id,
            old_value={"status": old_status},
            new_value={"status": new_status, "comment": comment},
            description=f"PR #{pr_id} 状态从 {old_status} 变为 {new_status}",
            ip_address=None
        )
        return await cls.log_action(entry, db)

    @classmethod
    async def log_permission_change(
        cls,
        user_id: int,
        user_name: str,
        user_role: str,
        member_id: int,
        action: str,
        old_perm: str | None,
        new_perm: str,
        vendor_id: int,
        db: AsyncSession
    ) -> int:
        """
        记录权限变更日志

        Args:
            user_id: 操作用户ID
            user_name: 操作用户名
            user_role: 操作用户角色
            member_id: 目标成员ID
            action: 操作类型
            old_perm: 原权限
            new_perm: 新权限
            vendor_id: 供应商ID
            db: 数据库会话

        Returns:
            日志ID
        """
        entry = AuditLogEntry(
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            action_type=action,
            resource_type="vendor_member",
            resource_id=member_id,
            vendor_id=vendor_id,
            old_value={"permission": old_perm},
            new_value={"permission": new_perm},
            description=f"成员 {member_id} 权限变更: {old_perm} → {new_perm}",
            ip_address=None
        )
        return await cls.log_action(entry, db)

    @classmethod
    async def log_config_change(
        cls,
        user_id: int,
        user_name: str,
        user_role: str,
        config_key: str,
        old_value: Any,
        new_value: Any,
        db: AsyncSession
    ) -> int:
        """
        记录配置变更日志

        Args:
            user_id: 用户ID
            user_name: 用户名
            user_role: 用户角色
            config_key: 配置键
            old_value: 原值
            new_value: 新值
            db: 数据库会话

        Returns:
            日志ID
        """
        entry = AuditLogEntry(
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            action_type="change_config",
            resource_type="config",
            resource_id=None,
            vendor_id=None,
            old_value={"key": config_key, "value": old_value},
            new_value={"key": config_key, "value": new_value},
            description=f"配置 {config_key} 变更: {old_value} → {new_value}",
            ip_address=None
        )
        return await cls.log_action(entry, db)


def audit_action(action_type: str):
    """
    审计操作装饰器

    自动记录操作日志
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从kwargs获取db和current_user
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')

            if db and current_user:
                # 执行原函数
                result = await func(*args, **kwargs)

                # 记录审计日志
                try:
                    entry = AuditLogEntry(
                        user_id=current_user.id,
                        user_name=current_user.name,
                        user_role=current_user.role,
                        action_type=action_type,
                        resource_type="unknown",
                        resource_id=None,
                        vendor_id=None,
                        old_value=None,
                        new_value=None,
                        description=f"执行操作: {action_type}",
                        ip_address=None
                    )
                    await AuditLogger.log_action(entry, db)
                except Exception as e:
                    logger.error(f"Failed to create audit log: {e}")

                return result
            else:
                return await func(*args, **kwargs)
        return wrapper
    return decorator

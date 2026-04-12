"""
验收验证服务

实现验收一票否决逻辑：
- CRITICAL合规违规自动阻断验收
- L1红线检查失败阻断验收
- 硬编码密钥检测阻断验收
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Delivery, PullRequest, QualityGate, Vendor

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验收验证结果"""
    delivery_id: int
    vendor_id: int
    vendor_name: str
    passed: bool
    veto_triggered: bool
    veto_reason: str | None
    violations: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    checked_at: datetime


class DeliveryValidator:
    """验收验证器"""

    # 一票否决规则
    VETO_RULES = [
        "L1_RED_LINE_FAILED",      # L1红线检查失败
        "HARDcoded_SECRETS",       # 硬编码密钥
        "ADVERTISING_LAW_VIOLATION",  # 广告法违规
        "INFANT_FORMULA_VIOLATION",   # 婴幼儿奶粉法规违规
        "CRITICAL_EXCEED_3",       # CRITICAL违规超过3次/月
    ]

    @classmethod
    async def check_critical_violations(
        cls,
        vendor_id: int,
        period: date,
        db: AsyncSession
    ) -> dict[str, Any]:
        """
        检查供应商在指定月份的CRITICAL违规

        Args:
            vendor_id: 供应商ID
            period: 检查月份
            db: 数据库会话

        Returns:
            违规检查结果 {critical_count, violations}
        """
        # 查询L1红线失败的门禁
        l1_failed_result = await db.execute(
            select(QualityGate).where(
                QualityGate.pr_id.in_(
                    select(PullRequest.id).where(
                        PullRequest.vendor_id == vendor_id,
                        PullRequest.created_at >= period
                    )
                ),
                QualityGate.layer == 1,
                QualityGate.status == "failed"
            )
        )
        l1_failures = l1_failed_result.scalars().all()

        # 查询L6合规失败的门禁
        l6_failed_result = await db.execute(
            select(QualityGate).where(
                QualityGate.pr_id.in_(
                    select(PullRequest.id).where(
                        PullRequest.vendor_id == vendor_id,
                        PullRequest.created_at >= period
                    )
                ),
                QualityGate.layer == 6,
                QualityGate.status == "failed"
            )
        )
        l6_failures = l6_failed_result.scalars().all()

        violations = []
        for gate in l1_failures:
            violations.append({
                "type": "L1_RED_LINE",
                "pr_id": gate.pr_id,
                "details": gate.details,
                "severity": "CRITICAL"
            })

        for gate in l6_failures:
            violations.append({
                "type": "L6_COMPLIANCE",
                "pr_id": gate.pr_id,
                "details": gate.details,
                "severity": "CRITICAL"
            })

        return {
            "critical_count": len(violations),
            "violations": violations
        }

    @classmethod
    async def validate_delivery(
        cls,
        delivery_id: int,
        db: AsyncSession
    ) -> ValidationResult:
        """
        验证交付物是否符合验收条件

        Args:
            delivery_id: 交付物ID
            db: 数据库会话

        Returns:
            ValidationResult验证结果
        """
        # 获取交付物信息
        delivery_result = await db.execute(
            select(Delivery).where(Delivery.id == delivery_id)
        )
        delivery = delivery_result.scalar_one_or_none()
        if not delivery:
            raise ValueError(f"Delivery {delivery_id} not found")

        # 获取供应商信息
        vendor_result = await db.execute(
            select(Vendor).where(Vendor.id == delivery.vendor_id)
        )
        vendor = vendor_result.scalar_one_or_none()
        if not vendor:
            raise ValueError(f"Vendor {delivery.vendor_id} not found")

        # 检查CRITICAL违规
        current_period = date.today().replace(day=1)
        violation_check = await cls.check_critical_violations(
            vendor.id, current_period, db
        )

        violations = violation_check["violations"]
        warnings = []

        # 评估一票否决条件
        veto_triggered = False
        veto_reason = None

        # 1. L1红线检查失败
        l1_violations = [v for v in violations if v["type"] == "L1_RED_LINE"]
        if l1_violations:
            veto_triggered = True
            veto_reason = f"发现L1红线检查失败 {len(l1_violations)} 次，包含硬编码密钥或SQL注入风险"

        # 2. L6合规检查失败 (广告法或奶粉法规)
        l6_violations = [v for v in violations if v["type"] == "L6_COMPLIANCE"]
        if l6_violations:
            # 检查是否包含广告法或奶粉法规违规
            for v in l6_violations:
                details = v.get("details", {})
                if isinstance(details, dict):
                    message = details.get("message", "")
                    if "广告法" in message or "敏感词" in message:
                        if not veto_triggered:
                            veto_triggered = True
                            veto_reason = "发现广告法敏感词违规，内容合规检查失败"
                    if "母乳替代" in message or "婴幼儿" in message:
                        if not veto_triggered:
                            veto_triggered = True
                            veto_reason = "发现婴幼儿奶粉法规违规，禁止母乳替代宣称"

        # 3. CRITICAL违规超过3次/月
        if violation_check["critical_count"] > 3:
            if not veto_triggered:
                veto_triggered = True
                veto_reason = f"本月CRITICAL违规超过阈值 ({violation_check['critical_count']}次 > 3次)"

        # 4. 检查供应商当前状态
        if vendor.status == "suspended":
            if not veto_triggered:
                veto_triggered = True
                veto_reason = "供应商已被暂停，无法进行验收"

        # 检查其他警告条件
        # 检查AI代码标记率
        if vendor.current_score:
            # 如果评分低于75，添加警告
            if vendor.current_score < 75 and not veto_triggered:
                warnings.append({
                    "type": "LOW_SCORE",
                    "message": f"供应商当前评分 {vendor.current_score} 分，建议关注"
                })

        # 构建结果
        result = ValidationResult(
            delivery_id=delivery_id,
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            passed=not veto_triggered,
            veto_triggered=veto_triggered,
            veto_reason=veto_reason,
            violations=violations,
            warnings=warnings,
            checked_at=datetime.utcnow()
        )

        return result

    @classmethod
    async def get_delivery_validation_status(
        cls,
        delivery_id: int,
        db: AsyncSession
    ) -> dict[str, Any]:
        """
        获取交付物的验证状态摘要

        Args:
            delivery_id: 交付物ID
            db: 数据库会话

        Returns:
            验证状态摘要
        """
        result = await cls.validate_delivery(delivery_id, db)

        return {
            "delivery_id": result.delivery_id,
            "vendor_name": result.vendor_name,
            "passed": result.passed,
            "veto_triggered": result.veto_triggered,
            "veto_reason": result.veto_reason,
            "critical_violations": len(result.violations),
            "warnings_count": len(result.warnings),
            "violations_detail": result.violations[:5],  # 最多显示5条
            "warnings_detail": result.warnings,
            "checked_at": result.checked_at.isoformat(),
            "recommendation": cls._get_recommendation(result)
        }

    @classmethod
    def _get_recommendation(cls, result: ValidationResult) -> str:
        """
        根据验证结果给出建议

        Args:
            result: 验证结果

        Returns:
            建议文本
        """
        if result.passed:
            if result.warnings:
                return "验收条件满足，但存在警告项建议关注处理"
            return "验收条件全部满足，建议批准验收"
        else:
            if result.veto_triggered:
                return f"验收条件不满足: {result.veto_reason}，必须修复后重新提交"
            return "验收条件不满足，建议驳回"

    @classmethod
    def get_veto_rules_description(cls) -> list[dict[str, str]]:
        """
        获取一票否决规则描述

        Returns:
            规则描述列表
        """
        return [
            {"rule": "L1_RED_LINE_FAILED", "description": "L1红线检查失败 (硬编码密钥、SQL注入)"},
            {"rule": "HARDCODED_SECRETS", "description": "检测到硬编码的密码/API密钥"},
            {"rule": "ADVERTISING_LAW_VIOLATION", "description": "广告法违规 (绝对化用语)"},
            {"rule": "INFANT_FORMULA_VIOLATION", "description": "婴幼儿奶粉法规违规 (母乳替代宣称)"},
            {"rule": "CRITICAL_EXCEED_3", "description": "单月CRITICAL违规超过3次"},
        ]

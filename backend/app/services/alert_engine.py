"""
告警规则引擎

检测供应商SLA异常，触发告警：
- 连续退步检测 (连续C/D级)
- 阈值超标检测 (CRITICAL违规、CI成功率)
- 即时告警 (>3 CRITICAL违规单月)
"""
from datetime import datetime, date
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
import logging

from app.models.models import Vendor, MonthlyScore, QualityGate, PullRequest, SLAGrade

logger = logging.getLogger(__name__)


@dataclass
class AlertRule:
    """告警规则定义"""
    rule_id: str
    rule_type: str  # threshold, trend, immediate
    severity: str  # warning, critical
    description: str
    condition: str  # 条件描述


@dataclass
class AlertInstance:
    """告警实例"""
    rule_id: str
    vendor_id: int
    vendor_name: str
    severity: str
    message: str
    triggered_at: datetime
    metadata: Dict[str, Any]


class AlertEngine:
    """告警规则引擎"""

    # 预定义告警规则
    RULES = [
        AlertRule(
            rule_id="CONSECUTIVE_DROP_2",
            rule_type="trend",
            severity="warning",
            description="连续2个月C/D级",
            condition="连续2个月评分等级为C或D"
        ),
        AlertRule(
            rule_id="CONSECUTIVE_DROP_3",
            rule_type="trend",
            severity="critical",
            description="连续3个月C/D级",
            condition="连续3个月评分等级为C或D"
        ),
        AlertRule(
            rule_id="CRITICAL_SPIKE",
            rule_type="immediate",
            severity="critical",
            description="单月CRITICAL违规超过3次",
            condition="单月CRITICAL违规数 > 3"
        ),
        AlertRule(
            rule_id="CI_FAILURE_RATE",
            rule_type="threshold",
            severity="warning",
            description="CI成功率低于80%",
            condition="ci_success_rate < 80"
        ),
        AlertRule(
            rule_id="AI_MARKING_LOW",
            rule_type="threshold",
            severity="warning",
            description="AI代码标记率低于90%",
            condition="ai_marking_rate < 90"
        ),
        AlertRule(
            rule_id="SCORE_DROP_20",
            rule_type="trend",
            severity="warning",
            description="评分环比下降超过20分",
            condition="本月评分 - 上月评分 > 20分下降"
        ),
        AlertRule(
            rule_id="COMPLIANCE_FAIL",
            rule_type="immediate",
            severity="critical",
            description="合规检查失败",
            condition="L6合规门禁检查失败"
        ),
    ]

    @classmethod
    async def evaluate_vendor(
        cls,
        vendor_id: int,
        db: AsyncSession
    ) -> List[AlertInstance]:
        """
        评估单个供应商的告警状态

        Args:
            vendor_id: 供应商ID
            db: 数据库会话

        Returns:
            触发的告警列表
        """
        alerts = []

        # 获取供应商信息
        vendor_result = await db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        vendor = vendor_result.scalar_one_or_none()
        if not vendor:
            return alerts

        # 获取最近3个月评分
        scores_result = await db.execute(
            select(MonthlyScore).where(
                MonthlyScore.vendor_id == vendor_id
            ).order_by(MonthlyScore.score_period.desc()).limit(3)
        )
        recent_scores = scores_result.scalars().all()

        # 评估每条规则
        for rule in cls.RULES:
            try:
                alert = await cls._evaluate_rule(rule, vendor, recent_scores, db)
                if alert:
                    alerts.append(alert)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {e}")

        return alerts

    @classmethod
    async def _evaluate_rule(
        cls,
        rule: AlertRule,
        vendor: Vendor,
        recent_scores: List[MonthlyScore],
        db: AsyncSession
    ) -> Optional[AlertInstance]:
        """
        评估单条规则

        Args:
            rule: 告警规则
            vendor: 供应商
            recent_scores: 最近评分记录
            db: 数据库会话

        Returns:
            触发的告警实例或None
        """
        if rule.rule_id == "CONSECUTIVE_DROP_2":
            # 连续2个月C/D级
            if len(recent_scores) >= 2:
                if recent_scores[0].grade in [SLAGrade.C, SLAGrade.D] and \
                   recent_scores[1].grade in [SLAGrade.C, SLAGrade.D]:
                    return AlertInstance(
                        rule_id=rule.rule_id,
                        vendor_id=vendor.id,
                        vendor_name=vendor.name,
                        severity=rule.severity,
                        message=f"{vendor.name} 连续2个月评分等级为{recent_scores[0].grade.value}",
                        triggered_at=datetime.utcnow(),
                        metadata={
                            "grades": [s.grade.value for s in recent_scores[:2]],
                            "scores": [float(s.total_score) for s in recent_scores[:2]]
                        }
                    )

        elif rule.rule_id == "CONSECUTIVE_DROP_3":
            # 连续3个月C/D级
            if len(recent_scores) >= 3:
                if all(s.grade in [SLAGrade.C, SLAGrade.D] for s in recent_scores[:3]):
                    return AlertInstance(
                        rule_id=rule.rule_id,
                        vendor_id=vendor.id,
                        vendor_name=vendor.name,
                        severity=rule.severity,
                        message=f"{vendor.name} 连续3个月评分等级为{recent_scores[0].grade.value}，建议启动替换流程",
                        triggered_at=datetime.utcnow(),
                        metadata={
                            "grades": [s.grade.value for s in recent_scores[:3]],
                            "scores": [float(s.total_score) for s in recent_scores[:3]]
                        }
                    )

        elif rule.rule_id == "CRITICAL_SPIKE":
            # 单月CRITICAL违规超过3次
            if recent_scores:
                latest_score = recent_scores[0]
                if latest_score.critical_violations > 3:
                    return AlertInstance(
                        rule_id=rule.rule_id,
                        vendor_id=vendor.id,
                        vendor_name=vendor.name,
                        severity=rule.severity,
                        message=f"{vendor.name} 本月CRITICAL违规{latest_score.critical_violations}次，触发即时约谈",
                        triggered_at=datetime.utcnow(),
                        metadata={
                            "critical_violations": latest_score.critical_violations,
                            "period": latest_score.score_period.strftime("%Y-%m")
                        }
                    )

        elif rule.rule_id == "CI_FAILURE_RATE":
            # CI成功率低于80%
            if recent_scores:
                latest_score = recent_scores[0]
                if latest_score.ci_success_rate < 80:
                    return AlertInstance(
                        rule_id=rule.rule_id,
                        vendor_id=vendor.id,
                        vendor_name=vendor.name,
                        severity=rule.severity,
                        message=f"{vendor.name} CI成功率{latest_score.ci_success_rate}%低于80%阈值",
                        triggered_at=datetime.utcnow(),
                        metadata={
                            "ci_success_rate": float(latest_score.ci_success_rate),
                            "period": latest_score.score_period.strftime("%Y-%m")
                        }
                    )

        elif rule.rule_id == "AI_MARKING_LOW":
            # AI代码标记率低于90%
            if recent_scores:
                latest_score = recent_scores[0]
                if latest_score.ai_code_marking_rate < 90:
                    return AlertInstance(
                        rule_id=rule.rule_id,
                        vendor_id=vendor.id,
                        vendor_name=vendor.name,
                        severity=rule.severity,
                        message=f"{vendor.name} AI代码标记率{latest_score.ai_code_marking_rate}%低于90%阈值",
                        triggered_at=datetime.utcnow(),
                        metadata={
                            "ai_marking_rate": float(latest_score.ai_code_marking_rate),
                            "period": latest_score.score_period.strftime("%Y-%m")
                        }
                    )

        elif rule.rule_id == "SCORE_DROP_20":
            # 评分环比下降超过20分
            if len(recent_scores) >= 2:
                score_diff = float(recent_scores[1].total_score) - float(recent_scores[0].total_score)
                if score_diff > 20:
                    return AlertInstance(
                        rule_id=rule.rule_id,
                        vendor_id=vendor.id,
                        vendor_name=vendor.name,
                        severity=rule.severity,
                        message=f"{vendor.name} 评分环比下降{score_diff:.1f}分",
                        triggered_at=datetime.utcnow(),
                        metadata={
                            "previous_score": float(recent_scores[1].total_score),
                            "current_score": float(recent_scores[0].total_score),
                            "drop": score_diff
                        }
                    )

        elif rule.rule_id == "COMPLIANCE_FAIL":
            # 合规检查失败
            # 查询最近的L6门禁失败
            failed_compliance_result = await db.execute(
                select(QualityGate).where(
                    QualityGate.pr_id.in_(
                        select(PullRequest.id).where(
                            PullRequest.vendor_id == vendor.id,
                            PullRequest.created_at >= date.today().replace(day=1)
                        )
                    ),
                    QualityGate.layer == 6,
                    QualityGate.status == "failed"
                ).limit(1)
            )
            failed_gate = failed_compliance_result.scalar_one_or_none()
            if failed_gate:
                return AlertInstance(
                    rule_id=rule.rule_id,
                    vendor_id=vendor.id,
                    vendor_name=vendor.name,
                    severity=rule.severity,
                    message=f"{vendor.name} 合规检查失败，发现敏感词或违规内容",
                    triggered_at=datetime.utcnow(),
                    metadata={
                        "gate_id": failed_gate.id,
                        "details": failed_gate.details
                    }
                )

        return None

    @classmethod
    async def evaluate_all_vendors(cls, db: AsyncSession) -> List[AlertInstance]:
        """
        评估所有活跃供应商

        Args:
            db: 数据库会话

        Returns:
            所有触发的告警列表
        """
        # 获取所有活跃供应商
        vendors_result = await db.execute(
            select(Vendor).where(
                Vendor.status.in_(["active", "warning"]),
                Vendor.is_deleted == False
            )
        )
        vendors = vendors_result.scalars().all()

        all_alerts = []
        for vendor in vendors:
            alerts = await cls.evaluate_vendor(vendor.id, db)
            all_alerts.extend(alerts)

        return all_alerts

    @classmethod
    def get_rule_descriptions(cls) -> List[Dict[str, str]]:
        """
        获取所有规则描述

        Returns:
            规则描述列表
        """
        return [
            {
                "rule_id": rule.rule_id,
                "rule_type": rule.rule_type,
                "severity": rule.severity,
                "description": rule.description,
                "condition": rule.condition
            }
            for rule in cls.RULES
        ]
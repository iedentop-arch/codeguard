"""
SLA评分引擎

实现7维度加权评分计算:
- CRITICAL违规: 30%
- WARNING趋势: 15%
- 代码质量: 15%
- 合规通过率: 15%
- PR评审效率: 10%
- AI标记率: 10%
- CI成功率: 5%
"""
from datetime import date, datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import logging

from app.models.models import Vendor, MonthlyScore, QualityGate, PullRequest, SLAGrade

logger = logging.getLogger(__name__)


@dataclass
class DimensionScore:
    """维度得分"""
    name: str
    raw_value: float
    score: float  # 0-100标准化得分
    weight: float
    target: str  # 目标值描述


@dataclass
class SLACalculationResult:
    """SLA计算结果"""
    vendor_id: int
    vendor_name: str
    period: str
    dimensions: List[DimensionScore]
    total_score: float
    grade: SLAGrade
    raw_metrics: Dict[str, Any]


class SLAEngine:
    """SLA评分引擎"""

    # 7维度权重配置
    WEIGHTS = {
        "critical_violations": 0.30,
        "warning_trend": 0.15,
        "code_quality": 0.15,
        "compliance_pass_rate": 0.15,
        "review_efficiency": 0.10,
        "ai_marking_rate": 0.10,
        "ci_success_rate": 0.05,
    }

    # 目标值配置
    TARGETS = {
        "critical_violations": {"target": 0, "description": "=0"},
        "warning_trend": {"target": -10, "description": "≥10%下降"},
        "code_quality": {"target": 90, "description": "≥90"},
        "compliance_pass_rate": {"target": 95, "description": "≥95%"},
        "review_efficiency": {"target": 2, "description": "≤2轮"},
        "ai_marking_rate": {"target": 100, "description": "100%"},
        "ci_success_rate": {"target": 95, "description": "≥95%"},
    }

    # 等级阈值
    GRADE_THRESHOLDS = {
        SLAGrade.A: 90,
        SLAGrade.B: 75,
        SLAGrade.C: 60,
        SLAGrade.D: 0,
    }

    @classmethod
    def calculate_dimension_score(cls, dimension: str, raw_value: Any) -> float:
        """
        计算单个维度的标准化得分 (0-100)

        Args:
            dimension: 维度名称
            raw_value: 原始值

        Returns:
            标准化得分 (0-100)
        """
        if dimension == "critical_violations":
            # CRITICAL违规: 0次=100分, 5次以上=0分, 线性递减
            if raw_value == 0:
                return 100.0
            elif raw_value >= 5:
                return 0.0
            else:
                return 100.0 - (raw_value / 5) * 100

        elif dimension == "warning_trend":
            # WARNING趋势: 下降(负值)=100分, 0%=80分, 上升线性递减
            if raw_value is None:
                return 80.0  # 默认值
            if raw_value <= -10:  # 下降10%以上
                return 100.0
            elif raw_value <= 0:  # 没增长
                return 80.0
            elif raw_value >= 30:  # 增长30%以上
                return 0.0
            else:
                return 80.0 - (raw_value / 30) * 80

        elif dimension == "code_quality":
            # 代码质量: 直接映射 (Ruff+MyPy得分)
            return min(100.0, max(0.0, float(raw_value or 0)))

        elif dimension == "compliance_pass_rate":
            # 合规通过率: 直接百分比映射
            return min(100.0, max(0.0, float(raw_value or 0)))

        elif dimension == "review_efficiency":
            # PR评审效率: ≤2轮=100分, ≥4轮=60分, 线性递减
            if raw_value is None:
                return 80.0
            if raw_value <= 2:
                return 100.0
            elif raw_value >= 4:
                return 60.0
            else:
                return 100.0 - (raw_value - 2) * 20

        elif dimension == "ai_marking_rate":
            # AI标记率: 100%=100分, 线性递减到0%
            return min(100.0, max(0.0, float(raw_value or 0)))

        elif dimension == "ci_success_rate":
            # CI成功率: 直接百分比映射
            return min(100.0, max(0.0, float(raw_value or 0)))

        else:
            return 0.0

    @classmethod
    def determine_grade(cls, total_score: float) -> SLAGrade:
        """
        根据总分确定等级

        Args:
            total_score: 加权总分

        Returns:
            SLAGrade等级
        """
        if total_score >= cls.GRADE_THRESHOLDS[SLAGrade.A]:
            return SLAGrade.A
        elif total_score >= cls.GRADE_THRESHOLDS[SLAGrade.B]:
            return SLAGrade.B
        elif total_score >= cls.GRADE_THRESHOLDS[SLAGrade.C]:
            return SLAGrade.C
        else:
            return SLAGrade.D

    @classmethod
    async def collect_vendor_metrics(
        cls,
        vendor_id: int,
        period: date,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        收集乙方在指定月份的原始指标数据

        Args:
            vendor_id: 乙方ID
            period: 评分月份
            db: 数据库会话

        Returns:
            原始指标字典
        """
        metrics = {}

        # 1. CRITICAL违规数 - 从质量门禁结果统计
        critical_result = await db.execute(
            select(func.count()).where(
                QualityGate.pr_id.in_(
                    select(PullRequest.id).where(
                        PullRequest.vendor_id == vendor_id,
                        PullRequest.created_at >= period,
                        PullRequest.created_at < date(period.year, period.month + 1) if period.month < 12 else date(period.year + 1, 1)
                    )
                ),
                QualityGate.status == "failed",
                QualityGate.layer == 1  # L1红线检查
            )
        )
        metrics["critical_violations"] = critical_result.scalar() or 0

        # 2. WARNING趋势 - 需要对比上月数据
        # 简化处理: 暂时设为0 (无变化)
        metrics["warning_trend"] = 0

        # 3. 代码质量分数 - 从L4门禁获取
        # 简化处理: 基于质量门禁通过率估算
        quality_result = await db.execute(
            select(func.count()).where(
                QualityGate.pr_id.in_(
                    select(PullRequest.id).where(
                        PullRequest.vendor_id == vendor_id,
                        PullRequest.status.in_(["merged", "approved"])
                    )
                ),
                QualityGate.status == "passed"
            )
        )
        passed_gates = quality_result.scalar() or 0

        total_result = await db.execute(
            select(func.count()).where(
                QualityGate.pr_id.in_(
                    select(PullRequest.id).where(
                        PullRequest.vendor_id == vendor_id
                    )
                )
            )
        )
        total_gates = total_result.scalar() or 1

        metrics["code_quality"] = (passed_gates / total_gates) * 100 if total_gates > 0 else 80

        # 4. 合规通过率 - 从L6门禁获取
        compliance_result = await db.execute(
            select(func.count()).where(
                QualityGate.pr_id.in_(
                    select(PullRequest.id).where(
                        PullRequest.vendor_id == vendor_id
                    )
                ),
                QualityGate.layer == 6,
                QualityGate.status == "passed"
            )
        )
        compliance_passed = compliance_result.scalar() or 0

        compliance_total_result = await db.execute(
            select(func.count()).where(
                QualityGate.pr_id.in_(
                    select(PullRequest.id).where(
                        PullRequest.vendor_id == vendor_id
                    )
                ),
                QualityGate.layer == 6
            )
        )
        compliance_total = compliance_total_result.scalar() or 1

        metrics["compliance_pass_rate"] = (compliance_passed / compliance_total) * 100 if compliance_total > 0 else 90

        # 5. PR评审效率 - 平均评审轮数
        # 简化处理: 基于PR状态估算
        pr_result = await db.execute(
            select(PullRequest).where(
                PullRequest.vendor_id == vendor_id,
                PullRequest.status.in_(["merged", "approved", "rejected"])
            )
        )
        prs = pr_result.scalars().all()
        # 假设每个PR平均2轮评审
        metrics["review_efficiency"] = 2.0

        # 6. AI标记率 - 从PR统计
        ai_marked_result = await db.execute(
            select(func.count()).where(
                PullRequest.vendor_id == vendor_id,
                PullRequest.has_ai_code == True,
                PullRequest.ai_code_marked == True
            )
        )
        ai_marked = ai_marked_result.scalar() or 0

        ai_total_result = await db.execute(
            select(func.count()).where(
                PullRequest.vendor_id == vendor_id,
                PullRequest.has_ai_code == True
            )
        )
        ai_total = ai_total_result.scalar() or 0

        if ai_total > 0:
            metrics["ai_marking_rate"] = (ai_marked / ai_total) * 100
        else:
            metrics["ai_marking_rate"] = 100.0  # 没有AI代码视为100%

        # 7. CI成功率 - 基于PR状态
        ci_passed_result = await db.execute(
            select(func.count()).where(
                PullRequest.vendor_id == vendor_id,
                PullRequest.status.in_(["ci_passed", "approved", "merged"])
            )
        )
        ci_passed = ci_passed_result.scalar() or 0

        ci_total_result = await db.execute(
            select(func.count()).where(
                PullRequest.vendor_id == vendor_id,
                PullRequest.status != "open"
            )
        )
        ci_total = ci_total_result.scalar() or 1

        metrics["ci_success_rate"] = (ci_passed / ci_total) * 100 if ci_total > 0 else 85

        return metrics

    @classmethod
    async def calculate_vendor_monthly_score(
        cls,
        vendor_id: int,
        period: date,
        db: AsyncSession,
        save: bool = True
    ) -> SLACalculationResult:
        """
        计算乙方月度SLA评分

        Args:
            vendor_id: 乙方ID
            period: 评分月份
            db: 数据库会话
            save: 是否保存到数据库

        Returns:
            SLACalculationResult计算结果
        """
        # 获取乙方信息
        vendor_result = await db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        vendor = vendor_result.scalar_one_or_none()
        if not vendor:
            raise ValueError(f"Vendor {vendor_id} not found")

        # 收集原始指标
        raw_metrics = await cls.collect_vendor_metrics(vendor_id, period, db)

        # 计算各维度得分
        dimensions = []
        weighted_sum = 0.0

        for dim_name, weight in cls.WEIGHTS.items():
            raw_value = raw_metrics.get(dim_name, 0)
            score = cls.calculate_dimension_score(dim_name, raw_value)
            target = cls.TARGETS[dim_name]["description"]

            dimensions.append(DimensionScore(
                name=dim_name,
                raw_value=raw_value,
                score=score,
                weight=weight,
                target=target
            ))
            weighted_sum += score * weight

        # 确定等级
        grade = cls.determine_grade(weighted_sum)

        result = SLACalculationResult(
            vendor_id=vendor_id,
            vendor_name=vendor.name,
            period=period.strftime("%Y-%m"),
            dimensions=dimensions,
            total_score=round(weighted_sum, 1),
            grade=grade,
            raw_metrics=raw_metrics
        )

        # 保存到数据库
        if save:
            monthly_score = MonthlyScore(
                vendor_id=vendor_id,
                score_period=period,
                critical_violations=int(raw_metrics["critical_violations"]),
                warning_trend_pct=raw_metrics.get("warning_trend"),
                code_quality_score=raw_metrics["code_quality"],
                compliance_pass_rate=raw_metrics["compliance_pass_rate"],
                pr_avg_review_rounds=raw_metrics["review_efficiency"],
                ai_code_marking_rate=raw_metrics["ai_marking_rate"],
                ci_success_rate=raw_metrics["ci_success_rate"],
                total_score=result.total_score,
                grade=grade
            )
            db.add(monthly_score)

            # 更新乙方当前评分
            vendor.current_score = result.total_score
            vendor.current_grade = grade

            await db.commit()
            logger.info(f"Saved monthly score for vendor {vendor_id}: {result.total_score} ({grade})")

        return result

    @classmethod
    async def calculate_all_vendors_monthly_score(
        cls,
        period: date,
        db: AsyncSession
    ) -> List[SLACalculationResult]:
        """
        计算所有活跃乙方的月度评分

        Args:
            period: 评分月份
            db: 数据库会话

        Returns:
            所有乙方的计算结果列表
        """
        # 获取所有活跃乙方
        vendors_result = await db.execute(
            select(Vendor).where(
                Vendor.status.in_(["active", "warning"]),
                Vendor.is_deleted == False
            )
        )
        vendors = vendors_result.scalars().all()

        results = []
        for vendor in vendors:
            try:
                result = await cls.calculate_vendor_monthly_score(
                    vendor.id, period, db, save=True
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to calculate score for vendor {vendor.id}: {e}")

        return results

    @classmethod
    def get_dimension_breakdown(cls, result: SLACalculationResult) -> Dict[str, Any]:
        """
        获取维度得分详情 (用于前端雷达图展示)

        Args:
            result: SLA计算结果

        Returns:
            维度详情字典
        """
        return {
            "dimensions": [
                {
                    "name": dim.name,
                    "score": dim.score,
                    "weight": dim.weight,
                    "weighted_score": round(dim.score * dim.weight, 2),
                    "raw_value": dim.raw_value,
                    "target": dim.target
                }
                for dim in result.dimensions
            ],
            "total_score": result.total_score,
            "grade": result.grade.value,
            "vendor_name": result.vendor_name,
            "period": result.period
        }
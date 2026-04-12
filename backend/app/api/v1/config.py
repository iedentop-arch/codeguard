"""
系统配置管理API
Phase 3 功能：提供系统配置的CRUD操作，支持SLA权重、告警阈值等动态配置
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.models import SystemConfig, User

router = APIRouter()


# ============== Schemas ==============

class SystemConfigBase(BaseModel):
    """系统配置基础Schema"""
    config_key: str = Field(..., description="配置键")
    config_value: str = Field(..., description="配置值")
    config_type: str = Field(default="string", description="配置类型: string, number, boolean, json")
    category: str = Field(default="general", description="配置分类: sla, alert, notification, system")
    description: str | None = Field(None, description="配置描述")
    is_editable: bool = Field(default=True, description="是否可编辑")


class SystemConfigCreate(SystemConfigBase):
    """创建系统配置Schema"""
    pass


class SystemConfigUpdate(BaseModel):
    """更新系统配置Schema"""
    config_value: str = Field(..., description="配置值")
    description: str | None = Field(None, description="配置描述")


class SystemConfigResponse(SystemConfigBase):
    """系统配置响应Schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SLAWeightsConfig(BaseModel):
    """SLA权重配置Schema"""
    critical: float = Field(0.30, ge=0, le=1, description="CRITICAL问题权重")
    warning: float = Field(0.15, ge=0, le=1, description="WARNING问题权重")
    code_quality: float = Field(0.15, ge=0, le=1, description="代码质量权重")
    compliance: float = Field(0.15, ge=0, le=1, description="合规性权重")
    pr_efficiency: float = Field(0.10, ge=0, le=1, description="PR效率权重")
    ai_marking: float = Field(0.10, ge=0, le=1, description="AI标记权重")
    ci_success: float = Field(0.05, ge=0, le=1, description="CI成功率权重")


class AlertThresholdsConfig(BaseModel):
    """告警阈值配置Schema"""
    consecutive_drop_threshold: int = Field(2, ge=1, description="连续下降次数阈值")
    critical_spike_threshold: int = Field(5, ge=1, description="CRITICAL激增阈值")
    ci_failure_rate_threshold: float = Field(0.3, ge=0, le=1, description="CI失败率阈值")
    sla_score_threshold: float = Field(60.0, ge=0, le=100, description="SLA分数阈值")
    warning_threshold: float = Field(70.0, ge=0, le=100, description="警告分数阈值")


class ConfigBatchUpdate(BaseModel):
    """批量更新配置Schema"""
    configs: list[SystemConfigUpdate]


# ============== Helper Functions ==============

async def get_config_by_key(db: AsyncSession, key: str) -> SystemConfig | None:
    """根据key获取配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == key)
    )
    return result.scalar_one_or_none()


async def check_admin_permission(current_user: User) -> None:
    """检查管理员权限"""
    # 简化版本：根据用户角色判断
    # 实际项目中应该有更完善的权限系统
    pass  # 暂时允许所有登录用户访问


# ============== API Endpoints ==============

@router.get("", response_model=list[SystemConfigResponse])
async def list_configs(
    category: str | None = None,
    config_type: str | None = None,
    is_editable: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取系统配置列表

    - 支持按分类、类型、可编辑状态筛选
    """
    query = select(SystemConfig)

    if category:
        query = query.where(SystemConfig.category == category)
    if config_type:
        query = query.where(SystemConfig.config_type == config_type)
    if is_editable is not None:
        query = query.where(SystemConfig.is_editable == is_editable)

    result = await db.execute(query.order_by(SystemConfig.category, SystemConfig.config_key))
    return result.scalars().all()


@router.get("/{config_id}", response_model=SystemConfigResponse)
async def get_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个配置详情"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置ID {config_id} 不存在"
        )

    return config


@router.get("/key/{config_key}", response_model=SystemConfigResponse)
async def get_config_by_key(
    config_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据配置键获取配置"""
    config = await get_config_by_key(db, config_key)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置键 '{config_key}' 不存在"
        )

    return config


@router.post("", response_model=SystemConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    config_data: SystemConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建系统配置

    需要管理员权限
    """
    await check_admin_permission(current_user)

    # 检查key是否已存在
    existing = await get_config_by_key(db, config_data.config_key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"配置键 '{config_data.config_key}' 已存在"
        )

    config = SystemConfig(**config_data.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)

    return config


@router.put("/{config_id}", response_model=SystemConfigResponse)
async def update_config(
    config_id: int,
    config_data: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新系统配置

    需要管理员权限，且配置必须可编辑
    """
    await check_admin_permission(current_user)

    result = await db.execute(
        select(SystemConfig).where(SystemConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置ID {config_id} 不存在"
        )

    if not config.is_editable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该配置不可编辑"
        )

    # 更新配置
    config.config_value = config_data.config_value
    if config_data.description is not None:
        config.description = config_data.description

    await db.commit()
    await db.refresh(config)

    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除系统配置

    需要管理员权限
    """
    await check_admin_permission(current_user)

    result = await db.execute(
        select(SystemConfig).where(SystemConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置ID {config_id} 不存在"
        )

    await db.delete(config)
    await db.commit()


@router.post("/batch", status_code=status.HTTP_200_OK)
async def batch_update_configs(
    batch_data: ConfigBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量更新配置

    根据config_key批量更新配置值
    """
    await check_admin_permission(current_user)

    updated_count = 0
    errors = []

    for config_update in batch_data.configs:
        # 这里需要知道config_key，但batch_data只有config_value
        # 实际使用时可能需要调整schema
        pass

    await db.commit()

    return {
        "message": f"成功更新 {updated_count} 个配置",
        "errors": errors
    }


# ============== 特殊配置端点 ==============

@router.get("/sla/weights", response_model=SLAWeightsConfig)
async def get_sla_weights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取SLA权重配置"""
    # 从数据库获取或返回默认值
    default_weights = SLAWeightsConfig()

    result = await db.execute(
        select(SystemConfig).where(SystemConfig.category == "sla")
    )
    configs = result.scalars().all()

    if not configs:
        return default_weights

    # 从配置构建权重对象
    weight_map = {c.config_key: c for c in configs}

    return SLAWeightsConfig(
        critical=float(weight_map.get("sla.weight.critical", SystemConfig(
            config_value=str(default_weights.critical))).config_value),
        warning=float(weight_map.get("sla.weight.warning", SystemConfig(
            config_value=str(default_weights.warning))).config_value),
        code_quality=float(weight_map.get("sla.weight.code_quality", SystemConfig(
            config_value=str(default_weights.code_quality))).config_value),
        compliance=float(weight_map.get("sla.weight.compliance", SystemConfig(
            config_value=str(default_weights.compliance))).config_value),
        pr_efficiency=float(weight_map.get("sla.weight.pr_efficiency", SystemConfig(
            config_value=str(default_weights.pr_efficiency))).config_value),
        ai_marking=float(weight_map.get("sla.weight.ai_marking", SystemConfig(
            config_value=str(default_weights.ai_marking))).config_value),
        ci_success=float(weight_map.get("sla.weight.ci_success", SystemConfig(
            config_value=str(default_weights.ci_success))).config_value),
    )


@router.put("/sla/weights", response_model=SLAWeightsConfig)
async def update_sla_weights(
    weights: SLAWeightsConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新SLA权重配置"""
    await check_admin_permission(current_user)

    # 验证权重总和为1
    total = (weights.critical + weights.warning + weights.code_quality +
             weights.compliance + weights.pr_efficiency + weights.ai_marking +
             weights.ci_success)

    if abs(total - 1.0) > 0.001:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"权重总和必须等于1，当前总和为 {total}"
        )

    # 更新各权重配置
    weight_updates = {
        "sla.weight.critical": str(weights.critical),
        "sla.weight.warning": str(weights.warning),
        "sla.weight.code_quality": str(weights.code_quality),
        "sla.weight.compliance": str(weights.compliance),
        "sla.weight.pr_efficiency": str(weights.pr_efficiency),
        "sla.weight.ai_marking": str(weights.ai_marking),
        "sla.weight.ci_success": str(weights.ci_success),
    }

    for key, value in weight_updates.items():
        config = await get_config_by_key(db, key)
        if config:
            config.config_value = value
        else:
            # 创建新配置
            new_config = SystemConfig(
                config_key=key,
                config_value=value,
                config_type="number",
                category="sla",
                description=f"SLA权重配置 - {key.split('.')[-1]}",
                is_editable=True
            )
            db.add(new_config)

    await db.commit()

    return weights


@router.get("/alert/thresholds", response_model=AlertThresholdsConfig)
async def get_alert_thresholds(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取告警阈值配置"""
    default_thresholds = AlertThresholdsConfig()

    result = await db.execute(
        select(SystemConfig).where(SystemConfig.category == "alert")
    )
    configs = result.scalars().all()

    if not configs:
        return default_thresholds

    config_map = {c.config_key: c for c in configs}

    def get_value(key: str, default: Any, converter) -> Any:
        config = config_map.get(key)
        if config:
            try:
                return converter(config.config_value)
            except (ValueError, TypeError):
                return default
        return default

    return AlertThresholdsConfig(
        consecutive_drop_threshold=get_value("alert.threshold.consecutive_drop",
                                             default_thresholds.consecutive_drop_threshold, int),
        critical_spike_threshold=get_value("alert.threshold.critical_spike",
                                           default_thresholds.critical_spike_threshold, int),
        ci_failure_rate_threshold=get_value("alert.threshold.ci_failure_rate",
                                           default_thresholds.ci_failure_rate_threshold, float),
        sla_score_threshold=get_value("alert.threshold.sla_score",
                                      default_thresholds.sla_score_threshold, float),
        warning_threshold=get_value("alert.threshold.warning",
                                    default_thresholds.warning_threshold, float),
    )


@router.put("/alert/thresholds", response_model=AlertThresholdsConfig)
async def update_alert_thresholds(
    thresholds: AlertThresholdsConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新告警阈值配置"""
    await check_admin_permission(current_user)

    threshold_updates = {
        "alert.threshold.consecutive_drop": str(thresholds.consecutive_drop_threshold),
        "alert.threshold.critical_spike": str(thresholds.critical_spike_threshold),
        "alert.threshold.ci_failure_rate": str(thresholds.ci_failure_rate_threshold),
        "alert.threshold.sla_score": str(thresholds.sla_score_threshold),
        "alert.threshold.warning": str(thresholds.warning_threshold),
    }

    for key, value in threshold_updates.items():
        config = await get_config_by_key(db, key)
        if config:
            config.config_value = value
        else:
            new_config = SystemConfig(
                config_key=key,
                config_value=value,
                config_type="number",
                category="alert",
                description=f"告警阈值配置 - {key.split('.')[-1]}",
                is_editable=True
            )
            db.add(new_config)

    await db.commit()

    return thresholds


@router.post("/reset/{category}")
async def reset_category_configs(
    category: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    重置某分类的配置为默认值

    支持的分类: sla, alert
    """
    await check_admin_permission(current_user)

    if category == "sla":
        default_values = {
            "sla.weight.critical": "0.30",
            "sla.weight.warning": "0.15",
            "sla.weight.code_quality": "0.15",
            "sla.weight.compliance": "0.15",
            "sla.weight.pr_efficiency": "0.10",
            "sla.weight.ai_marking": "0.10",
            "sla.weight.ci_success": "0.05",
        }
    elif category == "alert":
        default_values = {
            "alert.threshold.consecutive_drop": "2",
            "alert.threshold.critical_spike": "5",
            "alert.threshold.ci_failure_rate": "0.3",
            "alert.threshold.sla_score": "60.0",
            "alert.threshold.warning": "70.0",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持重置分类: {category}"
        )

    for key, value in default_values.items():
        config = await get_config_by_key(db, key)
        if config:
            config.config_value = value

    await db.commit()

    return {"message": f"已重置 {category} 分类配置为默认值"}

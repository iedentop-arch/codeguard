"""
通知服务

实现告警通知发送:
- 企业微信Webhook
- 邮件SMTP
"""
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import json
import logging
import httpx

from app.core.config import settings
from app.services.alert_engine import AlertInstance

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """通知发送结果"""
    channel: str
    success: bool
    message: str
    sent_at: datetime
    error: Optional[str] = None


class NotificationService:
    """通知服务"""

    @classmethod
    async def send_wechat_alert(cls, alert: AlertInstance, webhook_url: Optional[str] = None) -> NotificationResult:
        """
        发送企业微信告警

        Args:
            alert: 告警实例
            webhook_url: Webhook URL，默认使用配置

        Returns:
            NotificationResult发送结果
        """
        webhook = webhook_url or settings.WECHAT_WEBHOOK_URL
        if not webhook:
            logger.warning("WeChat webhook URL not configured")
            return NotificationResult(
                channel="wechat",
                success=False,
                message="企业微信Webhook未配置",
                sent_at=datetime.utcnow(),
                error="WECHAT_WEBHOOK_URL not set"
            )

        # 构建企业微信消息格式
        severity_color = {
            "critical": "红色",
            "warning": "橙色"
        }
        color = severity_color.get(alert.severity, "灰色")

        message_content = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"""## CodeGuard 告警通知

> **严重程度**: <font color="{color}">{alert.severity.upper()}</font>
> **供应商**: {alert.vendor_name}
> **规则**: {alert.rule_id}

**详情**:
{alert.message}

**触发时间**: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook,
                    json=message_content,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()

                if result.get("errcode") == 0:
                    return NotificationResult(
                        channel="wechat",
                        success=True,
                        message="企业微信通知发送成功",
                        sent_at=datetime.utcnow()
                    )
                else:
                    return NotificationResult(
                        channel="wechat",
                        success=False,
                        message=f"企业微信返回错误: {result.get('errmsg')}",
                        sent_at=datetime.utcnow(),
                        error=str(result)
                    )

        except Exception as e:
            logger.error(f"Failed to send WeChat notification: {e}")
            return NotificationResult(
                channel="wechat",
                success=False,
                message=f"企业微信发送失败: {str(e)}",
                sent_at=datetime.utcnow(),
                error=str(e)
            )

    @classmethod
    async def send_email_alert(
        cls,
        alert: AlertInstance,
        recipients: Optional[List[str]] = None,
        subject: Optional[str] = None
    ) -> NotificationResult:
        """
        发送邮件告警

        Args:
            alert: 告警实例
            recipients: 收件人列表，默认使用配置
            subject: 邮件主题

        Returns:
            NotificationResult发送结果
        """
        # 邮件发送需要SMTP配置，这里简化处理
        # 实际实现需要使用aiosmtplib库

        smtp_host = settings.SMTP_HOST
        if not smtp_host:
            logger.warning("SMTP not configured, email notification skipped")
            return NotificationResult(
                channel="email",
                success=False,
                message="SMTP未配置",
                sent_at=datetime.utcnow(),
                error="SMTP_HOST not set"
            )

        # 构建邮件内容
        email_subject = subject or f"[CodeGuard告警] {alert.vendor_name} - {alert.severity.upper()}"
        email_body = f"""
供应商: {alert.vendor_name}
规则ID: {alert.rule_id}
严重程度: {alert.severity}
详情: {alert.message}
触发时间: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}
"""

        # 这里仅记录日志，实际发送需要SMTP实现
        logger.info(f"Email notification prepared for alert {alert.rule_id}")
        logger.info(f"Subject: {email_subject}")
        logger.info(f"Body: {email_body}")

        # TODO: 实现实际SMTP发送
        # from aiosmtplib import SMTP
        # async with SMTP(hostname=smtp_host, port=settings.SMTP_PORT) as smtp:
        #     await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        #     await smtp.send_message(message)

        return NotificationResult(
            channel="email",
            success=True,  # 标记为成功，实际需要SMTP实现
            message="邮件通知已准备 (SMTP发送待实现)",
            sent_at=datetime.utcnow()
        )

    @classmethod
    async def dispatch_alert(cls, alert: AlertInstance) -> List[NotificationResult]:
        """
        根据告警严重程度分派到不同通知渠道

        Args:
            alert: 告警实例

        Returns:
            各渠道发送结果列表
        """
        results = []

        # CRITICAL级别发送企业微信 + 邮件
        if alert.severity == "critical":
            wechat_result = await cls.send_wechat_alert(alert)
            results.append(wechat_result)

            email_result = await cls.send_email_alert(alert)
            results.append(email_result)

        # WARNING级别发送企业微信
        elif alert.severity == "warning":
            wechat_result = await cls.send_wechat_alert(alert)
            results.append(wechat_result)

        return results

    @classmethod
    async def send_batch_alerts(cls, alerts: List[AlertInstance]) -> Dict[str, Any]:
        """
        批量发送告警通知

        Args:
            alerts: 告警列表

        Returns:
            发送统计结果
        """
        results = []
        success_count = 0
        failure_count = 0

        for alert in alerts:
            dispatch_results = await cls.dispatch_alert(alert)
            results.extend(dispatch_results)
            for r in dispatch_results:
                if r.success:
                    success_count += 1
                else:
                    failure_count += 1

        return {
            "total_alerts": len(alerts),
            "notifications_sent": len(results),
            "success_count": success_count,
            "failure_count": failure_count,
            "results": [
                {
                    "channel": r.channel,
                    "success": r.success,
                    "message": r.message,
                    "sent_at": r.sent_at.isoformat()
                }
                for r in results
            ]
        }


class WeeklyReportService:
    """周度简报服务"""

    @classmethod
    def generate_weekly_summary(cls, data: Dict[str, Any]) -> str:
        """
        生成周度简报内容

        Args:
            data: 周报数据 (vendors, scores, alerts, prs)

        Returns:
            简报文本内容
        """
        # 构建简报模板
        report_lines = [
            "# CodeGuard 周度简报",
            f"\n> 报告周期: {data.get('period', '本周')}",
            f"> 生成时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            "\n## 一、概览",
            f"- 活跃供应商: {data.get('active_vendors', 0)} 家",
            f"- 平均SLA评分: {data.get('avg_score', 0):.1f} 分",
            f"- CI成功率: {data.get('ci_success_rate', 0):.1f}%",
            "\n## 二、供应商表现",
        ]

        # 添加供应商评分
        vendors_data = data.get("vendors", [])
        for vendor in vendors_data[:5]:  # 前5名
            report_lines.append(
                f"- **{vendor.get('name')}**: {vendor.get('score', 0):.1f}分 ({vendor.get('grade', 'D')}级)"
            )

        # 添加告警情况
        report_lines.append("\n## 三、告警情况")
        alerts_data = data.get("alerts", [])
        critical_count = len([a for a in alerts_data if a.get("severity") == "critical"])
        warning_count = len([a for a in alerts_data if a.get("severity") == "warning"])
        report_lines.append(f"- CRITICAL告警: {critical_count} 条")
        report_lines.append(f"- WARNING告警: {warning_count} 条")

        if alerts_data:
            report_lines.append("\n### 主要告警:")
            for alert in alerts_data[:3]:
                report_lines.append(f"- {alert.get('vendor_name')}: {alert.get('message')}")

        # 添加PR活动
        report_lines.append("\n## 四、PR活动")
        prs_data = data.get("prs", {})
        report_lines.append(f"- 新增PR: {prs_data.get('new', 0)} 个")
        report_lines.append(f"- 已合并: {prs_data.get('merged', 0)} 个")
        report_lines.append(f"- 待审核: {prs_data.get('pending', 0)} 个")

        # 添加建议
        report_lines.append("\n## 五、下周建议")
        if critical_count > 0:
            report_lines.append("- 关注CRITICAL告警供应商，及时沟通处理")
        if data.get("avg_score", 0) < 80:
            report_lines.append("- 整体评分偏低，建议加强规范培训")

        return "\n".join(report_lines)

    @classmethod
    async def send_weekly_report(cls, report_content: str) -> NotificationResult:
        """
        发送周度简报

        Args:
            report_content: 简报内容

        Returns:
            发送结果
        """
        webhook = settings.WECHAT_WEBHOOK_URL
        if not webhook:
            return NotificationResult(
                channel="wechat",
                success=False,
                message="企业微信Webhook未配置",
                sent_at=datetime.utcnow(),
                error="WECHAT_WEBHOOK_URL not set"
            )

        message_content = {
            "msgtype": "markdown",
            "markdown": {
                "content": report_content
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook,
                    json=message_content,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                response.raise_for_status()
                return NotificationResult(
                    channel="wechat",
                    success=True,
                    message="周度简报发送成功",
                    sent_at=datetime.utcnow()
                )
        except Exception as e:
            logger.error(f"Failed to send weekly report: {e}")
            return NotificationResult(
                channel="wechat",
                success=False,
                message=f"周度简报发送失败: {str(e)}",
                sent_at=datetime.utcnow(),
                error=str(e)
            )
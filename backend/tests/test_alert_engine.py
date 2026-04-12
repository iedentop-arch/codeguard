"""
告警引擎单元测试
"""
import pytest
from datetime import datetime
from app.services.alert_engine import AlertEngine, AlertRule, AlertInstance


class TestAlertRulesConfiguration:
    """告警规则配置测试"""

    def test_alert_rules_count(self):
        """必须有7条告警规则"""
        assert len(AlertEngine.RULES) == 7

    def test_rule_ids_unique(self):
        """规则ID必须唯一"""
        rule_ids = [r.rule_id for r in AlertEngine.RULES]
        assert len(rule_ids) == len(set(rule_ids))

    def test_severity_values_valid(self):
        """严重程度值必须有效"""
        valid_severities = ["info", "warning", "critical"]
        for rule in AlertEngine.RULES:
            assert rule.severity in valid_severities


class TestAlertClassesExist:
    """告警类存在测试"""

    def test_alert_rule_class_exists(self):
        assert AlertRule is not None

    def test_alert_instance_class_exists(self):
        assert AlertInstance is not None
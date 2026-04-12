"""
SLA引擎单元测试
"""
import pytest
from app.services.sla_engine import SLAEngine
from app.models.models import SLAGrade


class TestSLAWeightsConfiguration:
    """SLA权重配置测试"""

    def test_weights_sum_to_one(self):
        """权重总和必须等于1"""
        total = sum(SLAEngine.WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_all_weights_positive(self):
        """所有权重必须为正数"""
        for dimension, weight in SLAEngine.WEIGHTS.items():
            assert weight > 0

    def test_weight_dimensions_count(self):
        """必须有7个维度权重"""
        assert len(SLAEngine.WEIGHTS) == 7


class TestDetermineGrade:
    """等级划分测试"""

    def test_grade_a(self):
        grade = SLAEngine.determine_grade(90.0)
        assert grade == SLAGrade.A

    def test_grade_b(self):
        grade = SLAEngine.determine_grade(75.0)
        assert grade == SLAGrade.B

    def test_grade_c(self):
        grade = SLAEngine.determine_grade(60.0)
        assert grade == SLAGrade.C

    def test_grade_d(self):
        grade = SLAEngine.determine_grade(50.0)
        assert grade == SLAGrade.D


class TestSLAGradeEnum:
    """SLA等级枚举测试"""

    def test_grade_values(self):
        assert SLAGrade.A.value == "A"
        assert SLAGrade.B.value == "B"
        assert SLAGrade.C.value == "C"
        assert SLAGrade.D.value == "D"
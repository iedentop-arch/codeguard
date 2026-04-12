"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-04-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建乙方表
    op.create_table(
        'vendors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, comment='乙方名称'),
        sa.Column('vendor_type', sa.Enum('A', 'B', 'C', 'D', name='vendortype'), nullable=False, comment='乙方类型'),
        sa.Column('status', sa.Enum('pending', 'active', 'warning', 'suspended', 'exited', name='vendorstatus'), nullable=False, comment='状态'),
        sa.Column('contact_name', sa.String(50), comment='联系人'),
        sa.Column('contact_email', sa.String(100), comment='联系邮箱'),
        sa.Column('contract_start', sa.Date(), comment='合同开始日期'),
        sa.Column('contract_end', sa.Date(), comment='合同结束日期'),
        sa.Column('github_org', sa.String(100), comment='GitHub组织'),
        sa.Column('current_grade', sa.Enum('A', 'B', 'C', 'D', name='slagrade'), comment='当前等级'),
        sa.Column('current_score', sa.Numeric(5, 1), comment='当前评分'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    
    # 创建乙方成员表
    op.create_table(
        'vendor_members',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(64), comment='用户ID'),
        sa.Column('name', sa.String(50), nullable=False, comment='姓名'),
        sa.Column('email', sa.String(100), nullable=False, comment='邮箱'),
        sa.Column('role', sa.String(20), nullable=False, comment='角色'),
        sa.Column('status', sa.String(16), comment='状态'),
        sa.Column('github_username', sa.String(50), comment='GitHub用户名'),
        sa.Column('exam_score', sa.Integer(), comment='考试分数'),
        sa.Column('exam_attempts', sa.Integer(), comment='考试尝试次数'),
        sa.Column('certification_id', sa.String(32), comment='认证编号'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
        sa.UniqueConstraint('email'),
    )
    
    # 创建规范文档表
    op.create_table(
        'spec_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(200), nullable=False, comment='标题'),
        sa.Column('category', sa.String(50), nullable=False, comment='分类'),
        sa.Column('vendor_types', sa.String(20), nullable=False, comment='适用乙方类型'),
        sa.Column('content', sa.Text(), comment='内容'),
        sa.Column('read_time', sa.Integer(), comment='阅读时间'),
        sa.Column('is_required', sa.Boolean(), comment='是否必读'),
        sa.Column('version', sa.String(20), comment='版本号'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # 创建考试题目表
    op.create_table(
        'exam_questions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('category', sa.String(32), nullable=False, comment='分类'),
        sa.Column('rule_id', sa.String(20), comment='规则编号'),
        sa.Column('severity', sa.String(16), nullable=False, comment='严重程度'),
        sa.Column('question_type', sa.String(20), nullable=False, comment='题型'),
        sa.Column('question_text', sa.Text(), nullable=False, comment='题目'),
        sa.Column('code_snippet', sa.Text(), comment='代码片段'),
        sa.Column('options', sa.Text(), nullable=False, comment='选项'),
        sa.Column('correct_answer', sa.String(10), nullable=False, comment='正确答案'),
        sa.Column('explanation', sa.Text(), nullable=False, comment='解释'),
        sa.Column('vendor_types', sa.String(20), comment='适用乙方类型'),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # 创建PR表
    op.create_table(
        'pull_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), comment='作者ID'),
        sa.Column('github_pr_number', sa.Integer(), nullable=False, comment='PR编号'),
        sa.Column('github_pr_url', sa.String(500), comment='PR链接'),
        sa.Column('title', sa.String(200), nullable=False, comment='标题'),
        sa.Column('branch', sa.String(100), comment='分支'),
        sa.Column('status', sa.String(20), comment='状态'),
        sa.Column('lines_added', sa.Integer(), comment='新增行数'),
        sa.Column('lines_removed', sa.Integer(), comment='删除行数'),
        sa.Column('files_changed', sa.Integer(), comment='变更文件数'),
        sa.Column('has_ai_code', sa.Boolean(), comment='包含AI代码'),
        sa.Column('ai_code_marked', sa.Boolean(), comment='AI代码已标记'),
        sa.Column('merged_at', sa.DateTime(), comment='合并时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
    )
    
    # 创建质量门禁表
    op.create_table(
        'quality_gates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('pr_id', sa.Integer(), nullable=False),
        sa.Column('layer', sa.Integer(), nullable=False, comment='层级'),
        sa.Column('layer_name', sa.String(50), nullable=False, comment='层级名称'),
        sa.Column('status', sa.String(16), nullable=False, comment='状态'),
        sa.Column('details', sa.Text(), comment='详情'),
        sa.Column('violations_count', sa.Integer(), comment='违规数'),
        sa.Column('warnings_count', sa.Integer(), comment='警告数'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['pr_id'], ['pull_requests.id']),
    )
    
    # 创建月度评分表
    op.create_table(
        'monthly_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('score_period', sa.Date(), nullable=False, comment='评分月份'),
        sa.Column('critical_violations', sa.Integer(), comment='CRITICAL违规数'),
        sa.Column('warning_trend_pct', sa.Numeric(5, 1), comment='WARNING趋势'),
        sa.Column('code_quality_score', sa.Numeric(5, 1), comment='代码质量分'),
        sa.Column('compliance_pass_rate', sa.Numeric(5, 1), comment='合规通过率'),
        sa.Column('pr_avg_review_rounds', sa.Numeric(3, 1), comment='平均评审轮数'),
        sa.Column('ai_code_marking_rate', sa.Numeric(5, 1), comment='AI代码标记率'),
        sa.Column('ci_success_rate', sa.Numeric(5, 1), comment='CI成功率'),
        sa.Column('total_score', sa.Numeric(5, 1), nullable=False, comment='总分'),
        sa.Column('grade', sa.Enum('A', 'B', 'C', 'D', name='slagrade_scores'), nullable=False, comment='等级'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
    )
    op.create_index('idx_vendor_period', 'monthly_scores', ['vendor_id', 'score_period'], unique=True)
    
    # 创建交付表
    op.create_table(
        'deliveries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), comment='项目ID'),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, comment='版本号'),
        sa.Column('description', sa.Text(), comment='描述'),
        sa.Column('artifacts', sa.Text(), comment='附件'),
        sa.Column('status', sa.String(20), comment='状态'),
        sa.Column('reviewed_at', sa.DateTime(), comment='评审时间'),
        sa.Column('reviewed_by', sa.String(64), comment='评审人'),
        sa.Column('reviewer_notes', sa.Text(), comment='评审备注'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
    )
    
    # 创建验收清单表
    op.create_table(
        'delivery_checklists',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('delivery_id', sa.Integer(), nullable=False),
        sa.Column('dimension', sa.String(50), nullable=False, comment='维度'),
        sa.Column('item_number', sa.String(10), nullable=False, comment='项编号'),
        sa.Column('description', sa.Text(), nullable=False, comment='描述'),
        sa.Column('acceptance_criteria', sa.Text(), nullable=False, comment='验收标准'),
        sa.Column('status', sa.String(20), comment='状态'),
        sa.Column('auto_filled', sa.Boolean(), comment='自动填充'),
        sa.Column('evidence_url', sa.String(500), comment='证据链接'),
        sa.Column('reviewer_notes', sa.Text(), comment='评审备注'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['delivery_id'], ['deliveries.id']),
    )
    
    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(100), nullable=False, comment='邮箱'),
        sa.Column('hashed_password', sa.String(255), nullable=False, comment='密码哈希'),
        sa.Column('name', sa.String(50), nullable=False, comment='姓名'),
        sa.Column('role', sa.String(20), nullable=False, comment='角色'),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )


def downgrade() -> None:
    op.drop_table('delivery_checklists')
    op.drop_table('deliveries')
    op.drop_index('idx_vendor_period', 'monthly_scores')
    op.drop_table('monthly_scores')
    op.drop_table('quality_gates')
    op.drop_table('pull_requests')
    op.drop_table('exam_questions')
    op.drop_table('spec_documents')
    op.drop_table('vendor_members')
    op.drop_table('vendors')
    op.drop_table('users')
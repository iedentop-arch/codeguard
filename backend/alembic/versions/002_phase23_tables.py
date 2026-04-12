"""Phase 2 & Phase 3 数据库表迁移

Revision ID: 002_phase23_tables
Revises: 001_initial
Create Date: 2026-04-13

新增表:
- task_logs: 任务执行日志
- alerts: 告警记录
- spec_versions: 规范版本历史
- spec_change_notifications: 规范变更通知
- notification_records: 通知发送记录
- quarterly_trainings: 季度培训计划
- training_records: 培训记录
- audit_logs: 审计日志
- sla_appeals: SLA申诉
- system_configs: 系统配置

修改表:
- vendor_members: 新增GitHub权限字段
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '002_phase23_tables'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === Phase 2 表 ===

    # 1. task_logs: 任务执行日志
    op.create_table(
        'task_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_name', sa.String(100), nullable=False, comment='任务名称'),
        sa.Column('status', sa.String(20), nullable=False, comment='状态'),
        sa.Column('started_at', sa.DateTime(), comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(), comment='完成时间'),
        sa.Column('error_message', sa.Text(), comment='错误信息'),
        sa.Column('metadata', sa.JSON(), comment='元数据'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. alerts: 告警记录
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vendor_id', sa.Integer(), sa.ForeignKey('vendors.id'), nullable=False),
        sa.Column('rule_id', sa.String(50), nullable=False, comment='规则ID'),
        sa.Column('severity', sa.String(20), nullable=False, comment='严重程度'),
        sa.Column('status', sa.String(20), server_default='active', comment='状态'),
        sa.Column('message', sa.Text(), nullable=False, comment='告警消息'),
        sa.Column('triggered_at', sa.DateTime(), server_default=sa.func.now(), comment='触发时间'),
        sa.Column('resolved_at', sa.DateTime(), comment='解决时间'),
        sa.Column('metadata', sa.JSON(), comment='元数据'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_alerts_vendor', 'vendor_id'),
        sa.Index('idx_alerts_status', 'status')
    )

    # 3. spec_versions: 规范版本历史
    op.create_table(
        'spec_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('spec_id', sa.Integer(), sa.ForeignKey('spec_documents.id'), nullable=False),
        sa.Column('version', sa.String(20), nullable=False, comment='版本号'),
        sa.Column('content_snapshot', sa.Text(), comment='内容快照'),
        sa.Column('change_summary', sa.Text(), comment='变更摘要'),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.func.now(), comment='变更时间'),
        sa.Column('changed_by', sa.Integer(), sa.ForeignKey('users.id'), comment='变更人'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_spec_versions_spec', 'spec_id')
    )

    # === Phase 3 表 ===

    # 4. spec_change_notifications: 规范变更通知
    op.create_table(
        'spec_change_notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('spec_id', sa.Integer(), sa.ForeignKey('spec_documents.id')),
        sa.Column('old_version', sa.String(20), comment='旧版本'),
        sa.Column('new_version', sa.String(20), comment='新版本'),
        sa.Column('change_type', sa.String(20), comment='变更类型'),
        sa.Column('change_summary', sa.Text(), comment='变更摘要'),
        sa.Column('notify_status', sa.String(20), server_default='pending', comment='通知状态'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. notification_records: 通知发送记录
    op.create_table(
        'notification_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('notification_id', sa.Integer(), sa.ForeignKey('spec_change_notifications.id')),
        sa.Column('vendor_id', sa.Integer(), sa.ForeignKey('vendors.id')),
        sa.Column('member_id', sa.Integer(), sa.ForeignKey('vendor_members.id')),
        sa.Column('channel', sa.String(20), comment='通知渠道'),
        sa.Column('status', sa.String(20), comment='发送状态'),
        sa.Column('sent_at', sa.DateTime(), comment='发送时间'),
        sa.Column('error_message', sa.Text(), comment='错误信息'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_notification_records_notification', 'notification_id')
    )

    # 6. quarterly_trainings: 季度培训计划
    op.create_table(
        'quarterly_trainings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('year', sa.Integer(), nullable=False, comment='年份'),
        sa.Column('quarter', sa.Integer(), nullable=False, comment='季度(1-4)'),
        sa.Column('title', sa.String(200), comment='培训标题'),
        sa.Column('description', sa.Text(), comment='培训描述'),
        sa.Column('spec_ids', sa.Text(), comment='关联规范ID(JSON)'),
        sa.Column('start_date', sa.Date(), comment='开始日期'),
        sa.Column('end_date', sa.Date(), comment='结束日期'),
        sa.Column('status', sa.String(20), server_default='draft', comment='状态'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_quarterly_trainings_year_quarter', 'year', 'quarter')
    )

    # 7. training_records: 培训记录
    op.create_table(
        'training_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quarterly_training_id', sa.Integer(), sa.ForeignKey('quarterly_trainings.id')),
        sa.Column('vendor_member_id', sa.Integer(), sa.ForeignKey('vendor_members.id')),
        sa.Column('vendor_id', sa.Integer(), sa.ForeignKey('vendors.id')),
        sa.Column('status', sa.String(20), server_default='enrolled', comment='状态'),
        sa.Column('exam_score', sa.Integer(), comment='考试分数'),
        sa.Column('exam_passed', sa.Boolean(), comment='是否通过'),
        sa.Column('certification_id', sa.String(32), comment='认证编号'),
        sa.Column('enrolled_at', sa.DateTime(), comment='报名时间'),
        sa.Column('completed_at', sa.DateTime(), comment='完成时间'),
        sa.Column('notes', sa.Text(), comment='备注'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_training_records_training_member', 'quarterly_training_id', 'vendor_member_id')
    )

    # 8. audit_logs: 审计日志
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('user_name', sa.String(50), comment='用户名'),
        sa.Column('user_role', sa.String(20), comment='用户角色'),
        sa.Column('action_type', sa.String(50), nullable=False, comment='操作类型'),
        sa.Column('resource_type', sa.String(50), comment='资源类型'),
        sa.Column('resource_id', sa.Integer(), comment='资源ID'),
        sa.Column('vendor_id', sa.Integer(), comment='涉及供应商'),
        sa.Column('old_value', sa.Text(), comment='旧值(JSON)'),
        sa.Column('new_value', sa.Text(), comment='新值(JSON)'),
        sa.Column('description', sa.Text(), comment='操作描述'),
        sa.Column('ip_address', sa.String(45), comment='IP地址'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_audit_logs_user', 'user_id', 'created_at'),
        sa.Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        sa.Index('idx_audit_logs_vendor', 'vendor_id', 'created_at')
    )

    # 9. sla_appeals: SLA申诉
    op.create_table(
        'sla_appeals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vendor_id', sa.Integer(), sa.ForeignKey('vendors.id'), nullable=False),
        sa.Column('submitter_id', sa.Integer(), sa.ForeignKey('vendor_members.id')),
        sa.Column('monthly_score_id', sa.Integer(), sa.ForeignKey('monthly_scores.id')),
        sa.Column('appeal_type', sa.String(20), comment='申诉类型'),
        sa.Column('reason', sa.Text(), comment='申诉理由'),
        sa.Column('evidence_urls', sa.Text(), comment='证据链接(JSON)'),
        sa.Column('status', sa.String(20), server_default='pending', comment='状态'),
        sa.Column('reviewed_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('reviewed_at', sa.DateTime(), comment='审核时间'),
        sa.Column('review_notes', sa.Text(), comment='审核备注'),
        sa.Column('resolution', sa.Text(), comment='处理结果'),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_appeals_vendor', 'vendor_id', 'status'),
        sa.Index('idx_appeals_status', 'status', 'submitted_at')
    )

    # 10. system_configs: 系统配置
    op.create_table(
        'system_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('config_key', sa.String(100), unique=True, nullable=False, comment='配置键'),
        sa.Column('config_value', sa.Text(), comment='配置值'),
        sa.Column('config_type', sa.String(20), comment='配置类型'),
        sa.Column('description', sa.Text(), comment='配置描述'),
        sa.Column('category', sa.String(50), comment='配置分类'),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # === 修改 vendor_members 表 ===
    op.add_column('vendor_members', sa.Column('github_permission_status', sa.String(20), server_default='none', comment='GitHub权限状态'))
    op.add_column('vendor_members', sa.Column('github_permission_level', sa.String(10), comment='GitHub权限级别'))
    op.add_column('vendor_members', sa.Column('github_permission_synced_at', sa.DateTime(), comment='权限同步时间'))


def downgrade() -> None:
    # 删除 vendor_members 新增字段
    op.drop_column('vendor_members', 'github_permission_synced_at')
    op.drop_column('vendor_members', 'github_permission_level')
    op.drop_column('vendor_members', 'github_permission_status')

    # 删除 Phase 3 表
    op.drop_table('system_configs')
    op.drop_table('sla_appeals')
    op.drop_table('audit_logs')
    op.drop_table('training_records')
    op.drop_table('quarterly_trainings')
    op.drop_table('notification_records')
    op.drop_table('spec_change_notifications')

    # 删除 Phase 2 表
    op.drop_table('spec_versions')
    op.drop_table('alerts')
    op.drop_table('task_logs')
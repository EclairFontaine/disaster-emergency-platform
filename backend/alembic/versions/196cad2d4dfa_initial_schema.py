"""initial_schema

Revision ID: 196cad2d4dfa
Revises: 
Create Date: 2026-07-24 11:40:59.047633

云南自然灾害应急协同决策平台 — 数据库初始建表迁移
包含全部13张业务表：roles, users, incidents, incident_reports,
resources, dispatch_orders, emergency_plans, data_sources,
agent_runs, citations, audit_logs, resource_locks, collected_events
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '196cad2d4dfa'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. roles 角色表
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(32), unique=True, nullable=False),
        sa.Column('description', sa.Text()),
    )

    # 2. users 用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('username', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('real_name', sa.String(64)),
        sa.Column('phone', sa.String(20)),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id')),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 3. incidents 灾情事件表
    op.create_table(
        'incidents',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('category', sa.String(32), index=True),
        sa.Column('severity', sa.String(16), default='P3'),
        sa.Column('status', sa.String(16), default='pending_review', index=True),
        sa.Column('latitude', sa.Float()),
        sa.Column('longitude', sa.Float()),
        sa.Column('risk_radius', sa.Float(), default=1000.0),
        sa.Column('affected_count', sa.Integer()),
        sa.Column('reported_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('confirmed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('extra_data', postgresql.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 4. incident_reports 灾情上报记录表
    op.create_table(
        'incident_reports',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id')),
        sa.Column('reporter_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('images', postgresql.ARRAY(sa.String()), default=list),
        sa.Column('contact_info', sa.String(128)),
        sa.Column('latitude', sa.Float()),
        sa.Column('longitude', sa.Float()),
        sa.Column('verification', sa.String(16), default='unverified'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 5. resources 应急资源表
    op.create_table(
        'resources',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('type', sa.String(32), nullable=False, index=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('quantity', sa.Integer(), default=1),
        sa.Column('available_qty', sa.Integer(), default=1),
        sa.Column('latitude', sa.Float()),
        sa.Column('longitude', sa.Float()),
        sa.Column('contact_info', sa.String(128)),
        sa.Column('status', sa.String(16), default='idle'),
        sa.Column('locked_qty', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 6. dispatch_orders 调度指令表
    op.create_table(
        'dispatch_orders',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id')),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('resource_id', sa.Integer(), sa.ForeignKey('resources.id')),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('dest_latitude', sa.Float()),
        sa.Column('dest_longitude', sa.Float()),
        sa.Column('status', sa.String(16), default='pending'),
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('dispatched_at', sa.DateTime(timezone=True)),
        sa.Column('arrived_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 7. emergency_plans 应急预案知识库
    op.create_table(
        'emergency_plans',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=True),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('generated_by', sa.String(32), default='ai'),
        sa.Column('source_refs', postgresql.JSON(), default=list),
        sa.Column('status', sa.String(16), default='draft'),
        sa.Column('reviewed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 8. data_sources 外部数据源配置
    op.create_table(
        'data_sources',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('type', sa.String(32)),
        sa.Column('url', sa.String(512)),
        sa.Column('fetch_interval', sa.Integer(), default=3600),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_fetch_at', sa.DateTime(timezone=True)),
    )

    # 9. agent_runs AI执行记录
    op.create_table(
        'agent_runs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id')),
        sa.Column('run_type', sa.String(32), index=True),
        sa.Column('input_data', postgresql.JSON()),
        sa.Column('output_data', postgresql.JSON()),
        sa.Column('status', sa.String(16), default='running'),
        sa.Column('error_message', sa.Text()),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(timezone=True)),
    )

    # 10. citations 引用来源
    op.create_table(
        'citations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('agent_run_id', sa.Integer(), sa.ForeignKey('agent_runs.id')),
        sa.Column('doc_name', sa.String(256)),
        sa.Column('chunk_text', sa.Text()),
        sa.Column('relevance_score', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 11. audit_logs 操作审计日志
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(64)),
        sa.Column('resource_type', sa.String(32)),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('detail', postgresql.JSON()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 12. resource_locks 资源锁定记录
    op.create_table(
        'resource_locks',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('resource_id', sa.Integer(), sa.ForeignKey('resources.id')),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id')),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('locked_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('locked_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('released_at', sa.DateTime(timezone=True)),
    )

    # 13. collected_events 采集事件持久化
    op.create_table(
        'collected_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('source', sa.String(64), nullable=False, index=True),
        sa.Column('event_type', sa.String(32), nullable=False),
        sa.Column('external_id', sa.String(256)),
        sa.Column('title', sa.String(512)),
        sa.Column('data', postgresql.JSON(), default=dict),
        sa.Column('latitude', sa.Float()),
        sa.Column('longitude', sa.Float()),
        sa.Column('magnitude', sa.Float()),
        sa.Column('created_incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=True),
        sa.Column('collected_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """回滚：按依赖顺序删除所有表"""
    op.drop_table('collected_events')
    op.drop_table('resource_locks')
    op.drop_table('audit_logs')
    op.drop_table('citations')
    op.drop_table('agent_runs')
    op.drop_table('data_sources')
    op.drop_table('emergency_plans')
    op.drop_table('dispatch_orders')
    op.drop_table('resources')
    op.drop_table('incident_reports')
    op.drop_table('incidents')
    op.drop_table('users')
    op.drop_table('roles')

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(32), unique=True, nullable=False)
    description = Column(Text)
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    real_name = Column(String(64))
    phone = Column(String(20))
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role", back_populates="users")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text)
    category = Column(String(32), index=True)
    severity = Column(String(16), default="P3")
    status = Column(String(16), default="pending_review", index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    risk_radius = Column(Float, default=1000.0)
    affected_count = Column(Integer)
    reported_by = Column(Integer, ForeignKey("users.id"))
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class IncidentReport(Base):
    __tablename__ = "incident_reports"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    reporter_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    images = Column(ARRAY(String), default=list)
    contact_info = Column(String(128))
    latitude = Column(Float)
    longitude = Column(Float)
    verification = Column(String(16), default="unverified")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(32), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    quantity = Column(Integer, default=1)
    available_qty = Column(Integer, default=1)
    latitude = Column(Float)
    longitude = Column(Float)
    contact_info = Column(String(128))
    status = Column(String(16), default="idle")
    locked_qty = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DispatchOrder(Base):
    __tablename__ = "dispatch_orders"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    plan_id = Column(Integer, nullable=True)
    resource_id = Column(Integer, ForeignKey("resources.id"))
    quantity = Column(Integer, nullable=False)
    dest_latitude = Column(Float)
    dest_longitude = Column(Float)
    status = Column(String(16), default="pending")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    dispatched_at = Column(DateTime(timezone=True))
    arrived_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmergencyPlan(Base):
    __tablename__ = "emergency_plans"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    title = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    generated_by = Column(String(32), default="ai")
    source_refs = Column(JSON, default=list)
    status = Column(String(16), default="draft")
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DataSource(Base):
    __tablename__ = "data_sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    type = Column(String(32))
    url = Column(String(512))
    fetch_interval = Column(Integer, default=3600)
    is_active = Column(Boolean, default=True)
    last_fetch_at = Column(DateTime(timezone=True))


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    run_type = Column(String(32), index=True)
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String(16), default="running")
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))


class Citation(Base):
    __tablename__ = "citations"
    id = Column(Integer, primary_key=True, index=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id"))
    doc_name = Column(String(256))
    chunk_text = Column(Text)
    relevance_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(64))
    resource_type = Column(String(32))
    resource_id = Column(Integer, nullable=True)
    detail = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ResourceLock(Base):
    __tablename__ = "resource_locks"
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"))
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    quantity = Column(Integer, nullable=False)
    locked_by = Column(Integer, ForeignKey("users.id"))
    locked_at = Column(DateTime(timezone=True), server_default=func.now())
    released_at = Column(DateTime(timezone=True))


class CollectedEvent(Base):
    """采集事件持久化"""
    __tablename__ = "collected_events"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(64), nullable=False, index=True)       # USGS/QWeather/NMC/Warning
    event_type = Column(String(32), nullable=False)                # earthquake/weather/warning
    external_id = Column(String(256))                               # 外部事件ID
    title = Column(String(512))
    data = Column(JSON, default=dict)                               # 完整数据
    latitude = Column(Float)
    longitude = Column(Float)
    magnitude = Column(Float)                                       # 震级 or 严重度
    created_incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())

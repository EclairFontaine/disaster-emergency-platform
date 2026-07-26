from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.sql import func

from database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, index=True)
    run_type = Column(String(32), index=True)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    status = Column(String(16), default="running")
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))


class Citation(Base):
    __tablename__ = "citations"
    id = Column(Integer, primary_key=True, index=True)
    agent_run_id = Column(Integer)
    doc_name = Column(String(256))
    chunk_text = Column(Text)
    relevance_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    real_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: int


class UserResponse(BaseModel):
    id: int
    username: str
    real_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: int
    role: Optional[RoleResponse] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    real_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class IncidentCreate(BaseModel):
    title: str = Field(min_length=2, max_length=256)
    description: Optional[str] = None
    category: Optional[str] = None
    severity: str = "P3"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    affected_count: Optional[int] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    risk_radius: Optional[float] = None
    affected_count: Optional[int] = None


class IncidentStatusUpdate(BaseModel):
    status: str
    reason: str = ""


class IncidentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    severity: str
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    risk_radius: Optional[float] = None
    affected_count: Optional[int] = None
    reported_by: Optional[int] = None
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    extra_data: dict = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentReportCreate(BaseModel):
    content: str
    images: List[str] = []
    contact_info: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class IncidentReportResponse(BaseModel):
    id: int
    incident_id: int
    reporter_id: Optional[int] = None
    content: str
    images: List[str] = []
    contact_info: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    verification: str = "unverified"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResourceCreate(BaseModel):
    type: str
    name: str
    description: Optional[str] = None
    quantity: int = 1
    available_qty: int = 1
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_info: Optional[str] = None


class ResourceResponse(BaseModel):
    id: int
    type: str
    name: str
    description: Optional[str] = None
    quantity: int
    available_qty: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_info: Optional[str] = None
    status: str
    locked_qty: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResourceUpdate(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    available_qty: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_info: Optional[str] = None
    status: Optional[str] = None


class ResourceLockRequest(BaseModel):
    incident_id: int
    quantity: int


class ResourceReleaseRequest(BaseModel):
    pass


class DispatchOrderCreate(BaseModel):
    incident_id: int
    resource_id: int
    quantity: int
    dest_latitude: Optional[float] = None
    dest_longitude: Optional[float] = None


class DispatchOrderResponse(BaseModel):
    id: int
    incident_id: int
    plan_id: Optional[int] = None
    resource_id: int
    quantity: int
    dest_latitude: Optional[float] = None
    dest_longitude: Optional[float] = None
    status: str
    approved_by: Optional[int] = None
    dispatched_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DispatchOrderStatusUpdate(BaseModel):
    status: str


class EmergencyPlanCreate(BaseModel):
    title: str
    content: str
    incident_id: Optional[int] = None


class EmergencyPlanResponse(BaseModel):
    id: int
    incident_id: Optional[int] = None
    title: str
    content: str
    generated_by: str = "ai"
    source_refs: list = []
    status: str = "draft"
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmergencyPlanUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class PlanSearchRequest(BaseModel):
    query: str


class PlanReviewRequest(BaseModel):
    status: str
    comment: str = ""


class PlanGenerateRequest(BaseModel):
    incident_id: int


class DataSourceCreate(BaseModel):
    name: str
    type: Optional[str] = None
    url: Optional[str] = None
    fetch_interval: int = 3600
    is_active: bool = True


class DataSourceResponse(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    url: Optional[str] = None
    fetch_interval: int = 3600
    is_active: bool = True
    last_fetch_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None
    fetch_interval: Optional[int] = None
    is_active: Optional[bool] = None


class AgentRunResponse(BaseModel):
    id: int
    incident_id: int
    run_type: str
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CitationResponse(BaseModel):
    id: int
    agent_run_id: int
    doc_name: str
    chunk_text: Optional[str] = None
    relevance_score: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    detail: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StatisticsResponse(BaseModel):
    total_incidents: int = 0
    active_incidents: int = 0
    total_resources: int = 0
    dispatched_resources: int = 0
    incidents_by_category: dict = {}
    incidents_by_severity: dict = {}
    recent_incidents: List[IncidentResponse] = []

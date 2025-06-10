from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.common import BaseSchema
from app.models.project import ProjectStatus, PaymentStatus, Currency


class ServiceItem(BaseModel):
    """服务项目"""
    camera: str
    qty: int
    unit_price: float
    price: float


class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str
    client_id: int
    deadline: Optional[datetime] = None
    budget: float
    currency: Currency = Currency.CNY
    exchange_rate: float = 1.0
    project_type: Optional[str] = None
    description: Optional[str] = None
    services: Optional[List[ServiceItem]] = None


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = None
    deadline: Optional[datetime] = None
    budget: Optional[float] = None
    currency: Optional[Currency] = None
    exchange_rate: Optional[float] = None
    project_type: Optional[str] = None
    description: Optional[str] = None
    services: Optional[List[ServiceItem]] = None


class ProjectStatusUpdate(BaseModel):
    """更新项目状态"""
    status: ProjectStatus


class ProjectProgressUpdate(BaseModel):
    """更新项目进度"""
    progress: int
    
    @validator('progress')
    def validate_progress(cls, v):
        if v < 0 or v > 100:
            raise ValueError('进度必须在0-100之间')
        return v


class ProjectResponse(BaseSchema):
    """项目响应"""
    id: int
    protocol_number: str
    name: str
    client_id: int
    status: ProjectStatus
    deadline: Optional[datetime]
    budget: float
    currency: Currency
    exchange_rate: float
    budget_cny: float
    payment_status: PaymentStatus
    progress: int
    project_type: Optional[str]
    description: Optional[str]
    services: Optional[List[Dict[str, Any]]]
    created_at: datetime
    updated_at: datetime


class ProjectListQuery(BaseModel):
    """项目列表查询参数"""
    page: int = 1
    page_size: int = 20
    status: Optional[ProjectStatus] = None
    client: Optional[str] = None
    search: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class GanttTask(BaseModel):
    """甘特图任务"""
    id: str
    name: str
    start: str
    end: str
    progress: int


class GanttProject(BaseModel):
    """甘特图项目"""
    id: str
    name: str
    start: str
    end: str
    progress: int
    dependencies: List[str] = []
    tasks: List[GanttTask] = [] 
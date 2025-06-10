from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum

class ReportType(str, Enum):
    """报表类型枚举"""
    PROJECTS = "projects"
    CLIENTS = "clients"
    FINANCE = "finance"
    TEAM = "team"
    PROFIT_LOSS = "profit_loss"
    CASH_FLOW = "cash_flow"
    REVENUE_DETAIL = "revenue_detail"

class ExportFormat(str, Enum):
    """导出格式枚举"""
    EXCEL = "excel"
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"

class ReportExportRequest(BaseModel):
    """报表导出请求"""
    report_type: ReportType = Field(..., description="报表类型")
    format: ExportFormat = Field(..., description="导出格式")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    filters: Optional[Dict[str, Any]] = Field(None, description="筛选条件")
    include_details: bool = Field(True, description="包含明细数据")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('结束日期不能早于开始日期')
        return v

class ReportExportResponse(BaseModel):
    """报表导出响应"""
    task_id: str = Field(..., description="任务ID")
    report_type: ReportType = Field(..., description="报表类型")
    format: ExportFormat = Field(..., description="导出格式")
    status: str = Field(..., description="任务状态")
    file_url: Optional[str] = Field(None, description="文件下载URL")
    created_at: datetime = Field(..., description="创建时间")
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")

class ProjectReportData(BaseModel):
    """项目报表数据"""
    project_id: int
    project_name: str
    protocol_number: str
    client_name: str
    status: str
    progress: float
    budget: float
    currency: str
    budget_cny: float
    payment_status: str
    deadline: date
    created_at: datetime

class ClientReportData(BaseModel):
    """客户报表数据"""
    client_id: int
    company_name: str
    contact_person: str
    email: str
    phone: str
    region: str
    total_projects: int
    total_revenue: float
    active_projects: int
    created_at: datetime

class FinanceReportData(BaseModel):
    """财务报表数据"""
    period: str
    total_revenue: float
    total_costs: float
    net_profit: float
    profit_margin: float
    receivables: float
    cash_flow: float

class TeamReportData(BaseModel):
    """团队报表数据"""
    member_id: int
    member_name: str
    department: str
    unit_price: float
    current_projects: int
    workload: float
    monthly_salary: float
    status: str

class ReportTemplate(BaseModel):
    """报表模板"""
    template_id: str = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名称")
    report_type: ReportType = Field(..., description="报表类型")
    columns: List[str] = Field(..., description="包含的列")
    filters: Optional[Dict[str, Any]] = Field(None, description="默认筛选条件")
    created_by: int = Field(..., description="创建者ID")
    is_public: bool = Field(False, description="是否公开")

class ReportSchedule(BaseModel):
    """报表计划任务"""
    schedule_id: str = Field(..., description="计划ID")
    schedule_name: str = Field(..., description="计划名称")
    report_type: ReportType = Field(..., description="报表类型")
    format: ExportFormat = Field(..., description="导出格式")
    frequency: str = Field(..., description="频率: daily, weekly, monthly")
    recipients: List[str] = Field(..., description="收件人邮箱列表")
    is_active: bool = Field(True, description="是否启用")
    next_run: datetime = Field(..., description="下次执行时间") 
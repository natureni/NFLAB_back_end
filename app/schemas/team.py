from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum
from app.models.team import Department, PriceType, MemberStatus


class PaymentStatus(str, Enum):
    """支付状态枚举"""
    PENDING = "pending"      # 待支付
    PAID = "paid"           # 已支付
    CANCELLED = "cancelled"  # 已取消


class TeamMemberBase(BaseModel):
    """团队成员基础模型"""
    name: str = Field(..., description="姓名", max_length=100)
    department: Department = Field(..., description="部门")
    phone: Optional[str] = Field(None, description="电话号码", max_length=50)
    id_card: Optional[str] = Field(None, description="身份证号", max_length=100)
    unit_price: float = Field(0, description="单价", ge=0)
    price_type: PriceType = Field(PriceType.FIXED, description="计价类型")
    bird_view_price: Optional[float] = Field(None, description="鸟瞰图价格", ge=0)
    human_view_price: Optional[float] = Field(None, description="人视图价格", ge=0)
    animation_price: Optional[float] = Field(None, description="动画价格", ge=0)
    custom_price: Optional[float] = Field(None, description="自定义价格", ge=0)
    bank_info: Optional[str] = Field(None, description="银行信息", max_length=500)
    payment_cycle: int = Field(30, description="支付周期（天）", ge=1)
    skills: Optional[List[str]] = Field(None, description="技能列表")
    join_date: Optional[date] = Field(None, description="入职日期")
    status: MemberStatus = Field(MemberStatus.ACTIVE, description="状态")


class TeamMemberCreate(TeamMemberBase):
    """创建团队成员"""
    pass


class TeamMemberUpdate(BaseModel):
    """更新团队成员"""
    name: Optional[str] = Field(None, description="姓名", max_length=100)
    department: Optional[Department] = Field(None, description="部门")
    phone: Optional[str] = Field(None, description="电话号码", max_length=50)
    id_card: Optional[str] = Field(None, description="身份证号", max_length=100)
    unit_price: Optional[float] = Field(None, description="单价", ge=0)
    price_type: Optional[PriceType] = Field(None, description="计价类型")
    bird_view_price: Optional[float] = Field(None, description="鸟瞰图价格", ge=0)
    human_view_price: Optional[float] = Field(None, description="人视图价格", ge=0)
    animation_price: Optional[float] = Field(None, description="动画价格", ge=0)
    custom_price: Optional[float] = Field(None, description="自定义价格", ge=0)
    bank_info: Optional[str] = Field(None, description="银行信息", max_length=500)
    payment_cycle: Optional[int] = Field(None, description="支付周期（天）", ge=1)
    skills: Optional[List[str]] = Field(None, description="技能列表")
    join_date: Optional[date] = Field(None, description="入职日期")
    status: Optional[MemberStatus] = Field(None, description="状态")


class TeamMemberResponse(TeamMemberBase):
    """团队成员响应模型"""
    id: int = Field(..., description="成员ID")
    current_projects: Optional[List[Dict[str, Any]]] = Field(None, description="当前项目")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class TeamMemberList(BaseModel):
    """团队成员列表"""
    id: int = Field(..., description="成员ID")
    name: str = Field(..., description="姓名")
    department: Department = Field(..., description="部门")
    status: MemberStatus = Field(..., description="状态")
    current_projects: Optional[List[Dict[str, Any]]] = Field(None, description="当前项目")
    
    class Config:
        from_attributes = True


class WorkloadResponse(BaseModel):
    """工作量响应模型"""
    member_id: int = Field(..., description="成员ID")
    member_name: str = Field(..., description="成员姓名")
    department: Department = Field(..., description="部门")
    current_projects: List[Dict[str, Any]] = Field([], description="当前项目")
    total_workload: int = Field(0, description="总工作量")
    estimated_hours: float = Field(0, description="预计工时")
    utilization_rate: float = Field(0, description="利用率", ge=0, le=1)


class PaymentCreate(BaseModel):
    """创建支付记录"""
    member_id: int = Field(..., description="成员ID")
    amount: float = Field(..., description="支付金额", gt=0)
    payment_date: date = Field(..., description="支付日期")
    payment_type: str = Field(..., description="支付类型")
    description: Optional[str] = Field(None, description="支付说明")


class PaymentResponse(BaseModel):
    """薪资支付记录响应模型"""
    payment_id: int = Field(..., description="支付记录ID")
    member_id: int = Field(..., description="成员ID")
    member_name: str = Field(..., description="成员姓名")
    department: Department = Field(..., description="部门")
    year: int = Field(..., description="年份")
    month: int = Field(..., description="月份")
    base_salary: float = Field(..., description="基础薪资")
    project_bonus: float = Field(..., description="项目奖金")
    total_salary: float = Field(..., description="总薪资")
    payment_status: PaymentStatus = Field(..., description="支付状态")
    calculated_at: datetime = Field(..., description="计算时间")
    paid_at: Optional[datetime] = Field(None, description="支付时间")
    notes: Optional[str] = Field(None, description="备注信息")


class WorkloadAssignment(BaseModel):
    """工作量分配模型"""
    project_ids: List[int] = Field(..., description="项目ID列表")
    
    @validator('project_ids')
    def validate_project_ids(cls, v):
        if not v:
            raise ValueError('项目ID列表不能为空')
        return v


class SalaryCalculation(BaseModel):
    """薪资计算模型"""
    member_id: int = Field(..., description="成员ID")
    member_name: str = Field(..., description="成员姓名")
    base_salary: float = Field(..., description="基础薪资")
    project_bonus: float = Field(0, description="项目奖金")
    total_salary: float = Field(..., description="总薪资")
    calculation_date: date = Field(..., description="计算日期")


class SalaryCalculationResponse(BaseModel):
    """薪资计算响应模型"""
    year: int = Field(..., description="年份")
    month: int = Field(..., description="月份")
    calculations: List[SalaryCalculation] = Field(..., description="薪资计算详情")
    total_amount: float = Field(..., description="总金额")


class PaymentStatusUpdate(BaseModel):
    """支付状态更新模型"""
    payment_status: PaymentStatus = Field(..., description="支付状态")
    notes: Optional[str] = Field(None, description="备注信息", max_length=500)


class PaymentHistoryResponse(BaseModel):
    """薪资支付历史记录响应模型"""
    payment_id: int = Field(..., description="支付记录ID")
    member_id: int = Field(..., description="成员ID")
    member_name: str = Field(..., description="成员姓名")
    department: Department = Field(..., description="部门")
    period: str = Field(..., description="支付周期(YYYY-MM)")
    total_salary: float = Field(..., description="总薪资")
    payment_status: PaymentStatus = Field(..., description="支付状态")
    paid_at: Optional[datetime] = Field(None, description="支付时间")
    working_days: int = Field(..., description="工作天数")
    daily_rate: float = Field(..., description="日薪率")
    notes: Optional[str] = Field(None, description="备注信息") 
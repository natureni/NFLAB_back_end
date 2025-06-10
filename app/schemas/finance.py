from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum
from app.models.project import Currency, PaymentStatus


class ReminderType(str, Enum):
    """提醒类型枚举"""
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"


class CostFrequency(str, Enum):
    """成本频率枚举"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ONE_TIME = "one_time"


class FinanceOverviewResponse(BaseModel):
    """财务概览响应模型"""
    period: str = Field(..., description="统计期间")
    currency: Currency = Field(..., description="显示货币")
    total_revenue: float = Field(..., description="总收入")
    paid_revenue: float = Field(..., description="已收款")
    pending_revenue: float = Field(..., description="待收款")
    total_costs: float = Field(..., description="总成本")
    fixed_costs: float = Field(..., description="固定成本")
    project_costs: float = Field(..., description="项目成本")
    net_profit: float = Field(..., description="净利润")
    profit_margin: float = Field(..., description="利润率（%）")
    total_projects: int = Field(..., description="总项目数")
    paid_projects: int = Field(..., description="已付款项目数")
    pending_projects: int = Field(..., description="待付款项目数")


class RevenueDetailResponse(BaseModel):
    """收入明细响应模型"""
    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    protocol_number: str = Field(..., description="协议编号")
    client_name: str = Field(..., description="客户名称")
    amount: float = Field(..., description="金额")
    currency: Currency = Field(..., description="货币")
    amount_cny: float = Field(..., description="人民币金额")
    payment_status: PaymentStatus = Field(..., description="支付状态")
    invoice_date: date = Field(..., description="开票日期")
    payment_date: Optional[date] = Field(None, description="付款日期")
    payment_terms: int = Field(..., description="付款期限（天）")


class CostBreakdown(BaseModel):
    """成本分解模型"""
    category: str = Field(..., description="成本类别")
    amount: float = Field(..., description="金额")
    percentage: float = Field(..., description="占比（%）")


class CostStructureResponse(BaseModel):
    """成本结构响应模型"""
    period: str = Field(..., description="统计期间")
    total_costs: float = Field(..., description="总成本")
    fixed_costs: float = Field(..., description="固定成本")
    variable_costs: float = Field(..., description="可变成本")
    cost_breakdown: List[CostBreakdown] = Field(..., description="成本分解")


class FixedCostBase(BaseModel):
    """固定成本基础模型"""
    category: str = Field(..., description="成本类别")
    description: str = Field(..., description="说明")
    amount: float = Field(..., description="金额", gt=0)
    currency: Currency = Field(Currency.CNY, description="货币")
    frequency: CostFrequency = Field(..., description="频率")
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")


class FixedCostCreate(FixedCostBase):
    """创建固定成本"""
    pass


class FixedCostUpdate(BaseModel):
    """更新固定成本"""
    category: Optional[str] = Field(None, description="成本类别")
    description: Optional[str] = Field(None, description="说明")
    amount: Optional[float] = Field(None, description="金额", gt=0)
    currency: Optional[Currency] = Field(None, description="货币")
    frequency: Optional[CostFrequency] = Field(None, description="频率")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")


class FixedCostResponse(FixedCostBase):
    """固定成本响应模型"""
    id: int = Field(..., description="成本ID")
    created_at: datetime = Field(..., description="创建时间")


class ReceivableResponse(BaseModel):
    """应收账款响应模型"""
    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    protocol_number: str = Field(..., description="协议编号")
    client_name: str = Field(..., description="客户名称")
    client_contact: str = Field(..., description="客户联系人")
    amount: float = Field(..., description="应收金额")
    currency: Currency = Field(..., description="货币")
    invoice_date: date = Field(..., description="开票日期")
    due_date: date = Field(..., description="到期日期")
    days_overdue: int = Field(..., description="逾期天数")
    payment_status: PaymentStatus = Field(..., description="支付状态")


class PaymentReminderRequest(BaseModel):
    """付款提醒请求模型"""
    reminder_type: ReminderType = Field(..., description="提醒类型")
    message: Optional[str] = Field(None, description="自定义消息")
    send_copy_to_admin: bool = Field(True, description="抄送管理员")


class ProfitLossResponse(BaseModel):
    """利润表响应模型"""
    period: str = Field(..., description="统计期间")
    total_revenue: float = Field(..., description="营业收入")
    cost_of_goods_sold: float = Field(..., description="营业成本")
    gross_profit: float = Field(..., description="毛利润")
    operating_expenses: float = Field(..., description="营业费用")
    operating_profit: float = Field(..., description="营业利润")
    other_income: float = Field(0, description="营业外收入")
    other_expenses: float = Field(0, description="营业外支出")
    net_profit: float = Field(..., description="利润总额")
    tax_expense: float = Field(..., description="所得税费用")
    net_profit_after_tax: float = Field(..., description="净利润")


class CashFlowResponse(BaseModel):
    """现金流量表响应模型"""
    period: str = Field(..., description="统计期间")
    # 经营活动现金流
    cash_from_operations: float = Field(..., description="经营活动现金流入")
    cash_paid_for_expenses: float = Field(..., description="经营活动现金流出")
    net_cash_from_operations: float = Field(..., description="经营活动现金净额")
    # 投资活动现金流
    cash_from_investing: float = Field(0, description="投资活动现金流入")
    cash_paid_for_investing: float = Field(0, description="投资活动现金流出")
    net_cash_from_investing: float = Field(0, description="投资活动现金净额")
    # 筹资活动现金流
    cash_from_financing: float = Field(0, description="筹资活动现金流入")
    cash_paid_for_financing: float = Field(0, description="筹资活动现金流出")
    net_cash_from_financing: float = Field(0, description="筹资活动现金净额")
    # 现金净变动
    net_change_in_cash: float = Field(..., description="现金净变动额")
    beginning_cash_balance: float = Field(..., description="期初现金余额")
    ending_cash_balance: float = Field(..., description="期末现金余额")


class FinanceReportExportRequest(BaseModel):
    """财务报表导出请求模型"""
    report_type: str = Field(..., description="报表类型")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    format: str = Field("excel", description="导出格式")
    include_details: bool = Field(True, description="包含明细")
    
    @validator('report_type')
    def validate_report_type(cls, v):
        allowed_types = ["profit_loss", "cash_flow", "revenue_detail", "cost_structure"]
        if v not in allowed_types:
            raise ValueError(f'报表类型必须是以下之一: {", ".join(allowed_types)}')
        return v
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ["excel", "pdf", "csv"]
        if v not in allowed_formats:
            raise ValueError(f'导出格式必须是以下之一: {", ".join(allowed_formats)}')
        return v


class PaymentStatusUpdate(BaseModel):
    """付款状态更新模型"""
    payment_status: PaymentStatus = Field(..., description="支付状态")
    payment_date: Optional[date] = Field(None, description="付款日期")
    notes: Optional[str] = Field(None, description="备注")


class FinanceStatistics(BaseModel):
    """财务统计模型"""
    current_month_revenue: float = Field(..., description="本月收入")
    last_month_revenue: float = Field(..., description="上月收入")
    revenue_growth_rate: float = Field(..., description="收入增长率（%）")
    current_month_profit: float = Field(..., description="本月利润")
    last_month_profit: float = Field(..., description="上月利润")
    profit_growth_rate: float = Field(..., description="利润增长率（%）")
    total_receivables: float = Field(..., description="总应收账款")
    overdue_receivables: float = Field(..., description="逾期应收账款")
    collection_rate: float = Field(..., description="回款率（%）") 
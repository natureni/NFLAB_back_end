from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.project import Currency


class SystemConfigBase(BaseModel):
    """系统配置基础模型"""
    app_name: str = Field(..., description="应用名称")
    company_name: str = Field(..., description="公司名称")
    contact_email: str = Field(..., description="联系邮箱")
    contact_phone: str = Field(..., description="联系电话")
    timezone: str = Field("Asia/Shanghai", description="时区")
    date_format: str = Field("YYYY-MM-DD", description="日期格式")
    currency_format: str = Field("symbol", description="货币格式")
    language: str = Field("zh-CN", description="语言")
    debug_mode: bool = Field(False, description="调试模式")
    maintenance_mode: bool = Field(False, description="维护模式")


class SystemConfigUpdate(BaseModel):
    """更新系统配置"""
    app_name: Optional[str] = Field(None, description="应用名称")
    company_name: Optional[str] = Field(None, description="公司名称")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    timezone: Optional[str] = Field(None, description="时区")
    date_format: Optional[str] = Field(None, description="日期格式")
    currency_format: Optional[str] = Field(None, description="货币格式")
    language: Optional[str] = Field(None, description="语言")
    debug_mode: Optional[bool] = Field(None, description="调试模式")
    maintenance_mode: Optional[bool] = Field(None, description="维护模式")


class SystemConfigResponse(SystemConfigBase):
    """系统配置响应模型"""
    last_updated: datetime = Field(..., description="最后更新时间")


class ExchangeRateUpdate(BaseModel):
    """更新汇率"""
    rates: Optional[Dict[Currency, float]] = Field(None, description="汇率配置")
    auto_sync: Optional[bool] = Field(None, description="自动同步")
    
    @validator('rates')
    def validate_rates(cls, v):
        if v:
            for currency, rate in v.items():
                if rate <= 0:
                    raise ValueError(f'{currency}的汇率必须大于0')
        return v


class ExchangeRateResponse(BaseModel):
    """汇率响应模型"""
    rates: Dict[Currency, float] = Field(..., description="汇率配置")
    base_currency: str = Field("USD", description="基准货币")  
    last_updated: datetime = Field(..., description="最后更新时间")
    auto_sync: bool = Field(True, description="自动同步")


class BusinessConfigBase(BaseModel):
    """业务配置基础模型"""
    default_currency: Currency = Field(Currency.CNY, description="默认货币")
    auto_exchange_rate_sync: bool = Field(True, description="自动汇率同步")
    project_deadline_buffer_days: int = Field(7, description="项目截止日期缓冲天数", ge=0)
    payment_reminder_days: List[int] = Field([7, 3, 1], description="付款提醒天数")
    default_project_status: str = Field("reporting", description="默认项目状态")
    require_client_approval: bool = Field(True, description="需要客户审批")
    auto_generate_protocol_number: bool = Field(True, description="自动生成协议编号")
    protocol_number_prefix: str = Field("NFLAB", description="协议编号前缀")
    tax_rate: float = Field(0.13, description="税率", ge=0, le=1)
    default_payment_terms: int = Field(30, description="默认付款条款(天)", ge=1)


class BusinessConfigUpdate(BaseModel):
    """更新业务配置"""
    default_currency: Optional[Currency] = Field(None, description="默认货币")
    auto_exchange_rate_sync: Optional[bool] = Field(None, description="自动汇率同步")
    project_deadline_buffer_days: Optional[int] = Field(None, description="项目截止日期缓冲天数", ge=0)
    payment_reminder_days: Optional[List[int]] = Field(None, description="付款提醒天数")
    default_project_status: Optional[str] = Field(None, description="默认项目状态")
    require_client_approval: Optional[bool] = Field(None, description="需要客户审批")
    auto_generate_protocol_number: Optional[bool] = Field(None, description="自动生成协议编号")
    protocol_number_prefix: Optional[str] = Field(None, description="协议编号前缀")
    tax_rate: Optional[float] = Field(None, description="税率", ge=0, le=1)
    default_payment_terms: Optional[int] = Field(None, description="默认付款条款(天)", ge=1)
    
    @validator('payment_reminder_days')
    def validate_reminder_days(cls, v):
        if v and any(day <= 0 for day in v):
            raise ValueError('提醒天数必须大于0')
        return v


class BusinessConfigResponse(BusinessConfigBase):
    """业务配置响应模型"""
    last_updated: datetime = Field(..., description="最后更新时间")


class SettingsExportResponse(BaseModel):
    """配置导出响应模型"""
    system_config: Dict[str, Any] = Field(..., description="系统配置")
    business_config: Dict[str, Any] = Field(..., description="业务配置")
    exchange_rates: Dict[Currency, float] = Field(..., description="汇率配置")
    export_time: datetime = Field(..., description="导出时间")
    version: str = Field("1.0", description="版本号")


class SettingsImportRequest(BaseModel):
    """配置导入请求模型"""
    system_config: Optional[Dict[str, Any]] = Field(None, description="系统配置")
    business_config: Optional[Dict[str, Any]] = Field(None, description="业务配置")
    exchange_rates: Optional[Dict[Currency, float]] = Field(None, description="汇率配置")


class ExchangeRateSyncResponse(BaseModel):
    """汇率同步响应模型"""
    message: str = Field(..., description="同步消息")
    updated_currencies: Optional[List[str]] = Field(None, description="更新的货币列表")
    sync_time: datetime = Field(..., description="同步时间")


class SettingsResetResponse(BaseModel):
    """配置重置响应模型"""
    message: str = Field(..., description="重置消息")
    reset_time: datetime = Field(..., description="重置时间") 
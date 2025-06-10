from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


class BaseResponse(BaseModel):
    """基础响应模型"""
    code: int = Field(200, description="响应代码")
    message: str = Field("success", description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class SuccessResponse(BaseResponse):
    """成功响应模型"""
    data: Optional[Any] = Field(None, description="响应数据")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    error: Optional[str] = Field(None, description="错误详情")


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(0, description="总数量")
    page: int = Field(1, description="当前页码")
    size: int = Field(20, description="每页数量")
    pages: int = Field(0, description="总页数")


class TimestampMixin(BaseModel):
    """时间戳混入类"""
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class StatusMixin(BaseModel):
    """状态混入类"""
    status: str = Field("active", description="状态")


class FinancialMixin(BaseModel):
    """财务混入类"""
    amount: float = Field(0.0, description="金额")
    currency: str = Field("CNY", description="货币类型")
    exchange_rate: Optional[float] = Field(None, description="汇率")


class ContactMixin(BaseModel):
    """联系信息混入类"""
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="地址") 
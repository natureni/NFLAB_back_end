from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional
from datetime import datetime

DataType = TypeVar('DataType')


class ResponseModel(BaseModel, Generic[DataType]):
    """通用响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[DataType] = None
    timestamp: datetime = datetime.now()


class PaginatedResponse(BaseModel, Generic[DataType]):
    """分页响应模型"""
    list: List[DataType]
    total: int
    page: int
    pageSize: int


class BaseSchema(BaseModel):
    """基础Schema"""
    class Config:
        from_attributes = True
        populate_by_name = True 
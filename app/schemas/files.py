from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime, date
from app.models.project import Currency


class FileInfoResponse(BaseModel):
    """文件信息响应模型"""
    id: int = Field(..., description="文件记录ID")
    file_id: str = Field(..., description="文件唯一标识")
    original_filename: str = Field(..., description="原始文件名")
    file_type: str = Field(..., description="文件类型")
    mime_type: str = Field(..., description="MIME类型")
    file_size: int = Field(..., description="文件大小（字节）")
    project_id: Optional[int] = Field(None, description="关联项目ID")
    description: Optional[str] = Field(None, description="文件描述")
    uploaded_by: int = Field(..., description="上传者ID")
    uploaded_at: datetime = Field(..., description="上传时间")


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: str = Field(..., description="文件唯一标识")
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小（字节）")
    upload_url: str = Field(..., description="文件访问URL")
    message: str = Field(..., description="上传结果消息")


class ContractGenerateRequest(BaseModel):
    """合同生成请求模型"""
    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    protocol_number: str = Field(..., description="协议编号")
    client_name: str = Field(..., description="客户名称")
    amount: float = Field(..., description="合同金额", gt=0)
    currency: Currency = Field(..., description="货币类型")
    deadline: date = Field(..., description="项目截止日期")
    services: str = Field(..., description="服务内容描述")
    payment_terms: str = Field(..., description="付款条款")
    
    @validator('services')
    def validate_services(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('服务内容描述过短，至少需要10个字符')
        return v


class ReportGenerateRequest(BaseModel):
    """报表生成请求模型"""
    report_type: str = Field(..., description="报表类型")
    report_title: str = Field(..., description="报表标题")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    data: Dict[str, Any] = Field(..., description="报表数据")
    
    @validator('report_type')
    def validate_report_type(cls, v):
        allowed_types = ["financial", "project", "client", "team"]
        if v not in allowed_types:
            raise ValueError(f'报表类型必须是以下之一: {", ".join(allowed_types)}')
        return v
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        if v > date.today():
            raise ValueError('日期不能超过今天')
        return v


class FileListResponse(BaseModel):
    """文件列表响应模型"""
    files: list[FileInfoResponse] = Field(..., description="文件列表")
    total_count: int = Field(..., description="文件总数")
    total_size: int = Field(..., description="总文件大小（字节）")


class StorageStatsResponse(BaseModel):
    """存储统计响应模型"""
    total_files: int = Field(..., description="文件总数")
    total_size: int = Field(..., description="总大小（字节）")
    total_size_mb: float = Field(..., description="总大小（MB）")
    file_types: Dict[str, Dict[str, int]] = Field(..., description="按类型统计")
    storage_limit: int = Field(..., description="存储限制（字节）")
    allowed_extensions: Dict[str, list[str]] = Field(..., description="支持的文件扩展名")


class PDFGenerateResponse(BaseModel):
    """PDF生成响应模型"""
    message: str = Field(..., description="生成结果消息")
    file_id: str = Field(..., description="生成的文件ID")
    download_url: str = Field(..., description="下载链接")


class FileDeleteResponse(BaseModel):
    """文件删除响应模型"""
    message: str = Field(..., description="删除结果消息")
    file_id: str = Field(..., description="删除的文件ID")


class FileTypeStats(BaseModel):
    """文件类型统计模型"""
    file_type: str = Field(..., description="文件类型")
    count: int = Field(..., description="文件数量")
    total_size: int = Field(..., description="总大小（字节）")
    percentage: float = Field(..., description="占比（%）") 
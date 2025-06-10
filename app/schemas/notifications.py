from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    """通知类型枚举"""
    PROJECT_UPDATE = "project_update"
    PAYMENT_REMINDER = "payment_reminder"
    DEADLINE_WARNING = "deadline_warning"
    TEAM_ASSIGNMENT = "team_assignment"
    SYSTEM_ALERT = "system_alert"
    CLIENT_MESSAGE = "client_message"

class NotificationPriority(str, Enum):
    """通知优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationBase(BaseModel):
    """通知基础模式"""
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    type: NotificationType = Field(..., description="通知类型")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM, description="优先级")
    target_user_id: Optional[int] = Field(None, description="目标用户ID，为空表示系统广播")
    related_project_id: Optional[int] = Field(None, description="相关项目ID")
    related_client_id: Optional[int] = Field(None, description="相关客户ID")
    action_url: Optional[str] = Field(None, description="操作链接")

class NotificationCreate(NotificationBase):
    """创建通知模式"""
    pass

class NotificationUpdate(BaseModel):
    """更新通知模式"""
    is_read: Optional[bool] = Field(None, description="是否已读")
    is_archived: Optional[bool] = Field(None, description="是否归档")

class NotificationInDB(NotificationBase):
    """数据库中的通知模式"""
    id: int
    is_read: bool = Field(default=False, description="是否已读")
    is_archived: bool = Field(default=False, description="是否归档")
    created_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class NotificationResponse(NotificationInDB):
    """通知响应模式"""
    # 关联数据
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    
class NotificationListResponse(BaseModel):
    """通知列表响应"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    size: int
    
class NotificationStats(BaseModel):
    """通知统计"""
    total_count: int = Field(..., description="总通知数")
    unread_count: int = Field(..., description="未读通知数")
    urgent_count: int = Field(..., description="紧急通知数")
    today_count: int = Field(..., description="今日通知数")
    by_type: dict = Field(..., description="按类型统计")
    by_priority: dict = Field(..., description="按优先级统计")

class NotificationSendRequest(BaseModel):
    """发送通知请求"""
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    type: NotificationType = Field(..., description="通知类型")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM, description="优先级")
    target_user_ids: Optional[List[int]] = Field(None, description="目标用户ID列表，为空表示全员通知")
    related_project_id: Optional[int] = Field(None, description="相关项目ID")
    related_client_id: Optional[int] = Field(None, description="相关客户ID")
    action_url: Optional[str] = Field(None, description="操作链接")
    send_immediately: bool = Field(default=True, description="是否立即发送")

class NotificationBatchOperation(BaseModel):
    """批量操作请求"""
    notification_ids: List[int] = Field(..., description="通知ID列表")
    operation: str = Field(..., description="操作类型: mark_read, mark_unread, archive, delete") 
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, update, delete
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_async_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.client import Client
from app.schemas.notifications import (
    NotificationResponse, NotificationListResponse, NotificationCreate,
    NotificationUpdate, NotificationSendRequest, NotificationBatchOperation,
    NotificationStats, NotificationType, NotificationPriority
)

router = APIRouter()

# 模拟通知数据存储（实际项目中应该使用数据库表）
notifications_storage = []
notification_id_counter = 1

def create_notification_dict(
    id: int,
    title: str,
    content: str,
    type: NotificationType,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    target_user_id: Optional[int] = None,
    related_project_id: Optional[int] = None,
    related_client_id: Optional[int] = None,
    action_url: Optional[str] = None,
    is_read: bool = False,
    is_archived: bool = False,
    created_at: Optional[datetime] = None,
    read_at: Optional[datetime] = None
) -> dict:
    """创建通知字典"""
    return {
        "id": id,
        "title": title,
        "content": content,
        "type": type,
        "priority": priority,
        "target_user_id": target_user_id,
        "related_project_id": related_project_id,
        "related_client_id": related_client_id,
        "action_url": action_url,
        "is_read": is_read,
        "is_archived": is_archived,
        "created_at": created_at or datetime.now(),
        "read_at": read_at,
        "project_name": None,
        "client_name": None
    }

# 初始化一些示例通知
def init_sample_notifications():
    global notifications_storage, notification_id_counter
    
    if not notifications_storage:
        sample_notifications = [
            create_notification_dict(
                id=1,
                title="项目进度更新",
                content="Sydney CBD Tower项目已进入渲染阶段，预计本周完成初版渲染",
                type=NotificationType.PROJECT_UPDATE,
                priority=NotificationPriority.MEDIUM,
                related_project_id=1,
                action_url="/projects/1",
                created_at=datetime.now() - timedelta(hours=2)
            ),
            create_notification_dict(
                id=2,
                title="付款提醒",
                content="万科翡翠公园项目首期款项即将到期，请及时跟进客户付款",
                type=NotificationType.PAYMENT_REMINDER,
                priority=NotificationPriority.HIGH,
                related_project_id=2,
                related_client_id=2,
                action_url="/finance/receivables",
                created_at=datetime.now() - timedelta(hours=6)
            ),
            create_notification_dict(
                id=3,
                title="截止日期警告",
                content="有3个项目将在本周内到达截止日期，请注意安排工作进度",
                type=NotificationType.DEADLINE_WARNING,
                priority=NotificationPriority.URGENT,
                action_url="/projects?filter=deadline_soon",
                created_at=datetime.now() - timedelta(hours=12)
            ),
            create_notification_dict(
                id=4,
                title="团队任务分配",
                content="您被分配到新项目：Melbourne Office Complex，请查看项目详情",
                type=NotificationType.TEAM_ASSIGNMENT,
                priority=NotificationPriority.MEDIUM,
                target_user_id=1,
                action_url="/team/assignments",
                created_at=datetime.now() - timedelta(days=1)
            ),
            create_notification_dict(
                id=5,
                title="系统维护通知",
                content="系统将于今晚23:00-01:00进行维护升级，期间可能影响服务访问",
                type=NotificationType.SYSTEM_ALERT,
                priority=NotificationPriority.HIGH,
                created_at=datetime.now() - timedelta(days=2),
                is_read=True,
                read_at=datetime.now() - timedelta(days=1)
            )
        ]
        
        notifications_storage.extend(sample_notifications)
        notification_id_counter = len(sample_notifications) + 1

@router.get("/", response_model=NotificationListResponse, summary="获取通知列表")
async def get_notifications(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    type: Optional[NotificationType] = Query(None, description="通知类型筛选"),
    priority: Optional[NotificationPriority] = Query(None, description="优先级筛选"),
    is_read: Optional[bool] = Query(None, description="已读状态筛选"),
    is_archived: Optional[bool] = Query(None, description="归档状态筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """获取当前用户的通知列表"""
    init_sample_notifications()
    
    # 筛选通知
    filtered_notifications = []
    for notification in notifications_storage:
        # 检查是否是目标用户的通知（为空表示全员通知）
        if notification["target_user_id"] and notification["target_user_id"] != current_user.id:
            continue
            
        # 应用筛选条件
        if type and notification["type"] != type:
            continue
        if priority and notification["priority"] != priority:
            continue
        if is_read is not None and notification["is_read"] != is_read:
            continue
        if is_archived is not None and notification["is_archived"] != is_archived:
            continue
            
        filtered_notifications.append(notification)
    
    # 按创建时间倒序排序
    filtered_notifications.sort(key=lambda x: x["created_at"], reverse=True)
    
    # 分页
    total = len(filtered_notifications)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    page_notifications = filtered_notifications[start_idx:end_idx]
    
    # 获取关联的项目和客户名称
    for notification in page_notifications:
        if notification["related_project_id"]:
            # 这里应该查询数据库获取项目名称
            notification["project_name"] = f"项目-{notification['related_project_id']}"
        if notification["related_client_id"]:
            # 这里应该查询数据库获取客户名称
            notification["client_name"] = f"客户-{notification['related_client_id']}"
    
    # 计算未读数量
    unread_count = sum(1 for n in filtered_notifications if not n["is_read"])
    
    return NotificationListResponse(
        notifications=[NotificationResponse(**n) for n in page_notifications],
        total=total,
        unread_count=unread_count,
        page=page,
        size=size
    )

@router.put("/{notification_id}/read", response_model=NotificationResponse, summary="标记通知已读")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """标记指定通知为已读"""
    init_sample_notifications()
    
    # 查找通知
    notification = None
    for i, n in enumerate(notifications_storage):
        if n["id"] == notification_id:
            # 检查权限
            if n["target_user_id"] and n["target_user_id"] != current_user.id:
                raise HTTPException(status_code=403, detail="无权限访问此通知")
            
            # 标记已读
            notifications_storage[i]["is_read"] = True
            notifications_storage[i]["read_at"] = datetime.now()
            notification = notifications_storage[i]
            break
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    return NotificationResponse(**notification)

@router.put("/{notification_id}/unread", response_model=NotificationResponse, summary="标记通知未读")
async def mark_notification_unread(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """标记指定通知为未读"""
    init_sample_notifications()
    
    # 查找通知
    notification = None
    for i, n in enumerate(notifications_storage):
        if n["id"] == notification_id:
            # 检查权限
            if n["target_user_id"] and n["target_user_id"] != current_user.id:
                raise HTTPException(status_code=403, detail="无权限访问此通知")
            
            # 标记未读
            notifications_storage[i]["is_read"] = False
            notifications_storage[i]["read_at"] = None
            notification = notifications_storage[i]
            break
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    return NotificationResponse(**notification)

@router.post("/send", response_model=dict, summary="发送通知")
async def send_notification(
    request: NotificationSendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """发送新通知"""
    global notification_id_counter
    init_sample_notifications()
    
    # 检查权限（只有管理员可以发送系统通知）
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以发送通知")
    
    sent_count = 0
    
    if request.target_user_ids:
        # 发送给指定用户
        for user_id in request.target_user_ids:
            notification = create_notification_dict(
                id=notification_id_counter,
                title=request.title,
                content=request.content,
                type=request.type,
                priority=request.priority,
                target_user_id=user_id,
                related_project_id=request.related_project_id,
                related_client_id=request.related_client_id,
                action_url=request.action_url
            )
            notifications_storage.append(notification)
            notification_id_counter += 1
            sent_count += 1
    else:
        # 全员通知
        notification = create_notification_dict(
            id=notification_id_counter,
            title=request.title,
            content=request.content,
            type=request.type,
            priority=request.priority,
            target_user_id=None,  # 全员通知
            related_project_id=request.related_project_id,
            related_client_id=request.related_client_id,
            action_url=request.action_url
        )
        notifications_storage.append(notification)
        notification_id_counter += 1
        sent_count = 1  # 全员通知算作1条
    
    return {
        "message": "通知发送成功",
        "sent_count": sent_count,
        "notification_type": request.type,
        "priority": request.priority
    }

@router.post("/batch", response_model=dict, summary="批量操作通知")
async def batch_operation_notifications(
    request: NotificationBatchOperation,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """批量操作通知（标记已读、归档、删除等）"""
    init_sample_notifications()
    
    if not request.notification_ids:
        raise HTTPException(status_code=400, detail="请选择要操作的通知")
    
    affected_count = 0
    
    for notification_id in request.notification_ids:
        for i, notification in enumerate(notifications_storage):
            if notification["id"] == notification_id:
                # 检查权限
                if notification["target_user_id"] and notification["target_user_id"] != current_user.id:
                    continue
                
                if request.operation == "mark_read":
                    notifications_storage[i]["is_read"] = True
                    notifications_storage[i]["read_at"] = datetime.now()
                elif request.operation == "mark_unread":
                    notifications_storage[i]["is_read"] = False
                    notifications_storage[i]["read_at"] = None
                elif request.operation == "archive":
                    notifications_storage[i]["is_archived"] = True
                elif request.operation == "delete":
                    notifications_storage.pop(i)
                
                affected_count += 1
                break
    
    return {
        "message": f"批量操作完成",
        "operation": request.operation,
        "affected_count": affected_count
    }

@router.get("/stats", response_model=NotificationStats, summary="获取通知统计")
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """获取当前用户的通知统计信息"""
    init_sample_notifications()
    
    # 筛选当前用户的通知
    user_notifications = []
    for notification in notifications_storage:
        if notification["target_user_id"] is None or notification["target_user_id"] == current_user.id:
            user_notifications.append(notification)
    
    total_count = len(user_notifications)
    unread_count = sum(1 for n in user_notifications if not n["is_read"])
    urgent_count = sum(1 for n in user_notifications if n["priority"] == NotificationPriority.URGENT)
    
    # 今日通知数
    today = datetime.now().date()
    today_count = sum(1 for n in user_notifications if n["created_at"].date() == today)
    
    # 按类型统计
    by_type = {}
    for notification_type in NotificationType:
        by_type[notification_type.value] = sum(1 for n in user_notifications if n["type"] == notification_type)
    
    # 按优先级统计
    by_priority = {}
    for priority in NotificationPriority:
        by_priority[priority.value] = sum(1 for n in user_notifications if n["priority"] == priority)
    
    return NotificationStats(
        total_count=total_count,
        unread_count=unread_count,
        urgent_count=urgent_count,
        today_count=today_count,
        by_type=by_type,
        by_priority=by_priority
    )

@router.delete("/{notification_id}", response_model=dict, summary="删除通知")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """删除指定通知"""
    init_sample_notifications()
    
    for i, notification in enumerate(notifications_storage):
        if notification["id"] == notification_id:
            # 检查权限
            if notification["target_user_id"] and notification["target_user_id"] != current_user.id:
                raise HTTPException(status_code=403, detail="无权限删除此通知")
            
            notifications_storage.pop(i)
            return {"message": "通知删除成功"}
    
    raise HTTPException(status_code=404, detail="通知不存在") 
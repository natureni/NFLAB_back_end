from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class RoleType(str, Enum):
    """角色类型枚举"""
    ADMIN = "admin"
    MANAGER = "manager"
    DESIGNER = "designer"
    RENDERER = "renderer"
    SALES = "sales"
    VIEWER = "viewer"

class PermissionType(str, Enum):
    """权限类型枚举"""
    # 项目管理权限
    PROJECT_CREATE = "project_create"
    PROJECT_READ = "project_read"
    PROJECT_UPDATE = "project_update"
    PROJECT_DELETE = "project_delete"
    PROJECT_STATUS_UPDATE = "project_status_update"
    
    # 客户管理权限
    CLIENT_CREATE = "client_create"
    CLIENT_READ = "client_read"
    CLIENT_UPDATE = "client_update"
    CLIENT_DELETE = "client_delete"
    CLIENT_EXPORT = "client_export"
    
    # 团队管理权限
    TEAM_CREATE = "team_create"
    TEAM_READ = "team_read"
    TEAM_UPDATE = "team_update"
    TEAM_DELETE = "team_delete"
    TEAM_SALARY_VIEW = "team_salary_view"
    TEAM_SALARY_MANAGE = "team_salary_manage"
    
    # 财务管理权限
    FINANCE_READ = "finance_read"
    FINANCE_UPDATE = "finance_update"
    FINANCE_EXPORT = "finance_export"
    FINANCE_COST_MANAGE = "finance_cost_manage"
    
    # 系统设置权限
    SETTINGS_READ = "settings_read"
    SETTINGS_UPDATE = "settings_update"
    SETTINGS_EXCHANGE_RATE = "settings_exchange_rate"
    
    # 文件管理权限
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"
    FILE_GENERATE_PDF = "file_generate_pdf"
    
    # 通知权限
    NOTIFICATION_SEND = "notification_send"
    NOTIFICATION_MANAGE = "notification_manage"
    
    # 系统管理权限
    USER_MANAGE = "user_manage"
    ROLE_MANAGE = "role_manage"
    SYSTEM_ADMIN = "system_admin"

class PermissionBase(BaseModel):
    """权限基础模式"""
    name: PermissionType = Field(..., description="权限名称")
    description: str = Field(..., description="权限描述")
    category: str = Field(..., description="权限分类")

class PermissionResponse(PermissionBase):
    """权限响应模式"""
    id: int
    
    class Config:
        from_attributes = True

class RolePermissionBase(BaseModel):
    """角色权限基础模式"""
    role: RoleType = Field(..., description="角色类型")
    permissions: List[PermissionType] = Field(..., description="权限列表")

class RolePermissionCreate(RolePermissionBase):
    """创建角色权限模式"""
    pass

class RolePermissionUpdate(BaseModel):
    """更新角色权限模式"""
    permissions: List[PermissionType] = Field(..., description="权限列表")

class RolePermissionResponse(RolePermissionBase):
    """角色权限响应模式"""
    id: int
    role_name: str = Field(..., description="角色名称")
    role_description: str = Field(..., description="角色描述")
    permission_count: int = Field(..., description="权限数量")
    
    class Config:
        from_attributes = True

class RoleInfo(BaseModel):
    """角色信息"""
    role: RoleType
    name: str
    description: str
    level: int  # 权限级别，数字越大权限越高
    default_permissions: List[PermissionType]

class UserPermissionCheck(BaseModel):
    """用户权限检查"""
    user_id: int
    permission: PermissionType
    has_permission: bool
    role: RoleType
    reason: Optional[str] = None

class PermissionMatrix(BaseModel):
    """权限矩阵"""
    roles: List[RoleInfo]
    permissions: List[PermissionResponse]
    matrix: Dict[str, List[str]]  # role -> permissions mapping 
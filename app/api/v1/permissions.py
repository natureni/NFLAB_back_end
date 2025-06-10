from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_async_session
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.permissions import (
    RolePermissionResponse, RolePermissionUpdate, PermissionMatrix,
    RoleInfo, PermissionResponse, UserPermissionCheck,
    RoleType, PermissionType
)

router = APIRouter()

# 预定义的角色信息
ROLE_DEFINITIONS = {
    RoleType.ADMIN: RoleInfo(
        role=RoleType.ADMIN,
        name="系统管理员",
        description="拥有系统所有权限，可以管理用户、角色和系统设置",
        level=100,
        default_permissions=[perm for perm in PermissionType]  # 所有权限
    ),
    RoleType.MANAGER: RoleInfo(
        role=RoleType.MANAGER,
        name="项目经理",
        description="负责项目管理、客户关系和团队协调",
        level=80,
        default_permissions=[
            PermissionType.PROJECT_CREATE, PermissionType.PROJECT_READ,
            PermissionType.PROJECT_UPDATE, PermissionType.PROJECT_STATUS_UPDATE,
            PermissionType.CLIENT_CREATE, PermissionType.CLIENT_READ,
            PermissionType.CLIENT_UPDATE, PermissionType.TEAM_READ,
            PermissionType.TEAM_UPDATE, PermissionType.FINANCE_READ,
            PermissionType.FILE_UPLOAD, PermissionType.FILE_DOWNLOAD,
            PermissionType.NOTIFICATION_SEND
        ]
    ),
    RoleType.DESIGNER: RoleInfo(
        role=RoleType.DESIGNER,
        name="设计师",
        description="负责项目设计和建模工作",
        level=60,
        default_permissions=[
            PermissionType.PROJECT_READ, PermissionType.PROJECT_UPDATE,
            PermissionType.CLIENT_READ, PermissionType.TEAM_READ,
            PermissionType.FILE_UPLOAD, PermissionType.FILE_DOWNLOAD,
            PermissionType.FILE_GENERATE_PDF
        ]
    ),
    RoleType.RENDERER: RoleInfo(
        role=RoleType.RENDERER,
        name="渲染师",
        description="负责项目渲染和后期制作",
        level=60,
        default_permissions=[
            PermissionType.PROJECT_READ, PermissionType.PROJECT_UPDATE,
            PermissionType.CLIENT_READ, PermissionType.TEAM_READ,
            PermissionType.FILE_UPLOAD, PermissionType.FILE_DOWNLOAD,
            PermissionType.FILE_GENERATE_PDF
        ]
    ),
    RoleType.SALES: RoleInfo(
        role=RoleType.SALES,
        name="销售人员",
        description="负责客户开发和项目销售",
        level=50,
        default_permissions=[
            PermissionType.PROJECT_READ, PermissionType.PROJECT_CREATE,
            PermissionType.CLIENT_CREATE, PermissionType.CLIENT_READ,
            PermissionType.CLIENT_UPDATE, PermissionType.FINANCE_READ,
            PermissionType.FILE_DOWNLOAD
        ]
    ),
    RoleType.VIEWER: RoleInfo(
        role=RoleType.VIEWER,
        name="查看者",
        description="只能查看基本信息，无修改权限",
        level=10,
        default_permissions=[
            PermissionType.PROJECT_READ, PermissionType.CLIENT_READ,
            PermissionType.TEAM_READ, PermissionType.FILE_DOWNLOAD
        ]
    )
}

# 权限定义
PERMISSION_DEFINITIONS = [
    PermissionResponse(id=1, name=PermissionType.PROJECT_CREATE, description="创建项目", category="项目管理"),
    PermissionResponse(id=2, name=PermissionType.PROJECT_READ, description="查看项目", category="项目管理"),
    PermissionResponse(id=3, name=PermissionType.PROJECT_UPDATE, description="更新项目", category="项目管理"),
    PermissionResponse(id=4, name=PermissionType.PROJECT_DELETE, description="删除项目", category="项目管理"),
    PermissionResponse(id=5, name=PermissionType.PROJECT_STATUS_UPDATE, description="更新项目状态", category="项目管理"),
    
    PermissionResponse(id=6, name=PermissionType.CLIENT_CREATE, description="创建客户", category="客户管理"),
    PermissionResponse(id=7, name=PermissionType.CLIENT_READ, description="查看客户", category="客户管理"),
    PermissionResponse(id=8, name=PermissionType.CLIENT_UPDATE, description="更新客户", category="客户管理"),
    PermissionResponse(id=9, name=PermissionType.CLIENT_DELETE, description="删除客户", category="客户管理"),
    PermissionResponse(id=10, name=PermissionType.CLIENT_EXPORT, description="导出客户数据", category="客户管理"),
    
    PermissionResponse(id=11, name=PermissionType.TEAM_CREATE, description="添加团队成员", category="团队管理"),
    PermissionResponse(id=12, name=PermissionType.TEAM_READ, description="查看团队信息", category="团队管理"),
    PermissionResponse(id=13, name=PermissionType.TEAM_UPDATE, description="更新团队信息", category="团队管理"),
    PermissionResponse(id=14, name=PermissionType.TEAM_DELETE, description="删除团队成员", category="团队管理"),
    PermissionResponse(id=15, name=PermissionType.TEAM_SALARY_VIEW, description="查看薪资信息", category="团队管理"),
    PermissionResponse(id=16, name=PermissionType.TEAM_SALARY_MANAGE, description="管理薪资支付", category="团队管理"),
    
    PermissionResponse(id=17, name=PermissionType.FINANCE_READ, description="查看财务信息", category="财务管理"),
    PermissionResponse(id=18, name=PermissionType.FINANCE_UPDATE, description="更新财务信息", category="财务管理"),
    PermissionResponse(id=19, name=PermissionType.FINANCE_EXPORT, description="导出财务报表", category="财务管理"),
    PermissionResponse(id=20, name=PermissionType.FINANCE_COST_MANAGE, description="管理成本结构", category="财务管理"),
    
    PermissionResponse(id=21, name=PermissionType.SETTINGS_READ, description="查看系统设置", category="系统设置"),
    PermissionResponse(id=22, name=PermissionType.SETTINGS_UPDATE, description="更新系统设置", category="系统设置"),
    PermissionResponse(id=23, name=PermissionType.SETTINGS_EXCHANGE_RATE, description="管理汇率设置", category="系统设置"),
    
    PermissionResponse(id=24, name=PermissionType.FILE_UPLOAD, description="上传文件", category="文件管理"),
    PermissionResponse(id=25, name=PermissionType.FILE_DOWNLOAD, description="下载文件", category="文件管理"),
    PermissionResponse(id=26, name=PermissionType.FILE_DELETE, description="删除文件", category="文件管理"),
    PermissionResponse(id=27, name=PermissionType.FILE_GENERATE_PDF, description="生成PDF文件", category="文件管理"),
    
    PermissionResponse(id=28, name=PermissionType.NOTIFICATION_SEND, description="发送通知", category="通知管理"),
    PermissionResponse(id=29, name=PermissionType.NOTIFICATION_MANAGE, description="管理通知", category="通知管理"),
    
    PermissionResponse(id=30, name=PermissionType.USER_MANAGE, description="管理用户", category="系统管理"),
    PermissionResponse(id=31, name=PermissionType.ROLE_MANAGE, description="管理角色权限", category="系统管理"),
    PermissionResponse(id=32, name=PermissionType.SYSTEM_ADMIN, description="系统管理员权限", category="系统管理"),
]

def check_user_permission(user: User, permission: PermissionType) -> bool:
    """检查用户是否有指定权限"""
    if user.role == "admin":
        return True
    
    user_role = RoleType(user.role) if user.role in [r.value for r in RoleType] else RoleType.VIEWER
    role_info = ROLE_DEFINITIONS.get(user_role)
    
    if not role_info:
        return False
    
    return permission in role_info.default_permissions

@router.get("/roles", response_model=List[RolePermissionResponse], summary="获取角色权限配置")
async def get_roles_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """获取所有角色的权限配置"""
    # 检查权限
    if not check_user_permission(current_user, PermissionType.ROLE_MANAGE):
        raise HTTPException(status_code=403, detail="无权限查看角色配置")
    
    roles_permissions = []
    for role_type, role_info in ROLE_DEFINITIONS.items():
        roles_permissions.append(RolePermissionResponse(
            id=role_info.level,
            role=role_type,
            permissions=role_info.default_permissions,
            role_name=role_info.name,
            role_description=role_info.description,
            permission_count=len(role_info.default_permissions)
        ))
    
    return roles_permissions

@router.put("/roles/{role_id}", response_model=RolePermissionResponse, summary="更新角色权限")
async def update_role_permissions(
    role_id: str,
    update_data: RolePermissionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """更新指定角色的权限配置"""
    # 检查权限
    if not check_user_permission(current_user, PermissionType.ROLE_MANAGE):
        raise HTTPException(status_code=403, detail="无权限修改角色配置")
    
    # 验证角色是否存在
    try:
        role_type = RoleType(role_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role_type not in ROLE_DEFINITIONS:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 不允许修改管理员角色权限
    if role_type == RoleType.ADMIN and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限修改管理员角色")
    
    # 更新角色权限（这里只是模拟，实际应该更新数据库）
    role_info = ROLE_DEFINITIONS[role_type]
    role_info.default_permissions = update_data.permissions
    
    return RolePermissionResponse(
        id=role_info.level,
        role=role_type,
        permissions=role_info.default_permissions,
        role_name=role_info.name,
        role_description=role_info.description,
        permission_count=len(role_info.default_permissions)
    )

@router.get("/matrix", response_model=PermissionMatrix, summary="获取权限矩阵")
async def get_permission_matrix(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """获取完整的权限矩阵"""
    # 检查权限
    if not check_user_permission(current_user, PermissionType.ROLE_MANAGE):
        raise HTTPException(status_code=403, detail="无权限查看权限矩阵")
    
    # 构建权限矩阵
    matrix = {}
    for role_type, role_info in ROLE_DEFINITIONS.items():
        matrix[role_type.value] = [perm.value for perm in role_info.default_permissions]
    
    return PermissionMatrix(
        roles=list(ROLE_DEFINITIONS.values()),
        permissions=PERMISSION_DEFINITIONS,
        matrix=matrix
    )

@router.get("/check/{permission}", response_model=UserPermissionCheck, summary="检查用户权限")
async def check_permission(
    permission: PermissionType,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """检查当前用户是否有指定权限"""
    has_permission = check_user_permission(current_user, permission)
    
    user_role = RoleType(current_user.role) if current_user.role in [r.value for r in RoleType] else RoleType.VIEWER
    
    reason = None
    if not has_permission:
        reason = f"角色 '{ROLE_DEFINITIONS[user_role].name}' 没有 '{permission.value}' 权限"
    
    return UserPermissionCheck(
        user_id=current_user.id,
        permission=permission,
        has_permission=has_permission,
        role=user_role,
        reason=reason
    )

@router.get("/permissions", response_model=List[PermissionResponse], summary="获取所有权限列表")
async def get_all_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """获取系统中所有可用的权限列表"""
    # 检查权限
    if not check_user_permission(current_user, PermissionType.ROLE_MANAGE):
        raise HTTPException(status_code=403, detail="无权限查看权限列表")
    
    return PERMISSION_DEFINITIONS

@router.get("/user/permissions", response_model=List[PermissionType], summary="获取当前用户权限")
async def get_user_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """获取当前用户拥有的所有权限"""
    user_role = RoleType(current_user.role) if current_user.role in [r.value for r in RoleType] else RoleType.VIEWER
    role_info = ROLE_DEFINITIONS.get(user_role, ROLE_DEFINITIONS[RoleType.VIEWER])
    
    return role_info.default_permissions 
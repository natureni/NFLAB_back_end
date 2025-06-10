from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo, Permission, ProfileUpdateRequest
from app.schemas.common import ResponseModel
from app.api.deps import get_current_active_user

router = APIRouter()


@router.post("/login", response_model=ResponseModel[LoginResponse])
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    # 查询用户
    stmt = select(User).where(User.username == login_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    
    # 创建访问令牌
    access_token = create_access_token(data={"user_id": user.id})
    
    # 更新最后登录时间
    stmt = update(User).where(User.id == user.id).values(last_login_at=datetime.utcnow())
    await db.execute(stmt)
    await db.commit()
    
    # 构造用户信息
    user_info = UserInfo.model_validate(user)
    
    # 构造权限信息（简化版）
    permissions = [
        Permission(module="dashboard", actions=["view"]),
        Permission(module="projects", actions=["view", "create", "edit", "delete"]),
        Permission(module="clients", actions=["view", "create", "edit", "delete"]),
        Permission(module="team", actions=["view", "create", "edit", "delete"]),
        Permission(module="finance", actions=["view", "create", "edit", "delete"]),
    ]
    
    # 如果是管理员，给予所有权限
    if user.role == "admin":
        for perm in permissions:
            perm.actions.extend(["export", "import", "manage"])
    
    login_response = LoginResponse(
        token=access_token,
        user=user_info,
        permissions=permissions
    )
    
    return ResponseModel[LoginResponse](data=login_response)


@router.post("/logout", response_model=ResponseModel[dict])
async def logout(current_user: User = Depends(get_current_active_user)):
    """用户登出"""
    # 在实际应用中，可能需要将token加入黑名单
    return ResponseModel[dict](data={"message": "登出成功"})


@router.get("/profile", response_model=ResponseModel[UserInfo])
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    user_info = UserInfo.model_validate(current_user)
    return ResponseModel[UserInfo](data=user_info)


@router.put("/profile", response_model=ResponseModel[UserInfo])
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户信息"""
    update_data = profile_data.model_dump(exclude_unset=True)
    
    if update_data:
        stmt = update(User).where(User.id == current_user.id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        
        # 重新查询用户信息
        stmt = select(User).where(User.id == current_user.id)
        result = await db.execute(stmt)
        updated_user = result.scalar_one()
        
        user_info = UserInfo.model_validate(updated_user)
        return ResponseModel[UserInfo](data=user_info)
    
    user_info = UserInfo.model_validate(current_user)
    return ResponseModel[UserInfo](data=user_info) 
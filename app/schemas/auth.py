from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
from app.schemas.common import BaseSchema
from app.models.user import UserRole, UserStatus


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str
    remember: bool = False


class UserInfo(BaseSchema):
    """用户信息"""
    id: int
    username: str
    name: str
    email: EmailStr
    role: UserRole
    department: Optional[str] = None
    avatar: Optional[str] = None
    last_login_at: Optional[datetime] = None
    status: UserStatus


class Permission(BaseModel):
    """权限信息"""
    module: str
    actions: List[str]


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    user: UserInfo
    permissions: List[Permission]


class ProfileUpdateRequest(BaseModel):
    """用户信息更新请求"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    avatar: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    """密码修改请求"""
    old_password: str
    new_password: str 
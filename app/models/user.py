from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    MANAGER = "manager"
    DESIGNER = "designer"
    MODELER = "modeler"
    RENDERER = "renderer"
    SALES = "sales"


class UserStatus(str, enum.Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.DESIGNER)
    department = Column(String(50), nullable=True)
    avatar = Column(String(255), nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    
    # 关联关系
    # projects = relationship("Project", back_populates="manager")
    
    def __repr__(self):
        return f"<User(username='{self.username}', name='{self.name}')>" 
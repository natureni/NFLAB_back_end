from sqlalchemy import Column, String, Integer, Float, Date, JSON, Enum
from app.models.base import BaseModel
import enum


class Department(str, enum.Enum):
    """部门枚举"""
    MODELING = "modeling"       # 建模部
    RENDERING = "rendering"     # 渲染部
    DESIGN = "design"          # 设计部
    SALES = "sales"            # 销售部
    MANAGEMENT = "management"   # 管理部


class PriceType(str, enum.Enum):
    """计价类型枚举"""
    FIXED = "fixed"            # 固定价格
    HOURLY = "hourly"          # 小时计价
    PROJECT = "project"        # 项目计价


class MemberStatus(str, enum.Enum):
    """成员状态枚举"""
    ACTIVE = "active"          # 在职
    INACTIVE = "inactive"      # 离职
    SUSPENDED = "suspended"    # 暂停


class TeamMember(BaseModel):
    """团队成员模型"""
    __tablename__ = "team_members"
    
    # 基本信息
    name = Column(String(100), nullable=False)
    department = Column(Enum(Department), nullable=False)
    phone = Column(String(50), nullable=True)
    id_card = Column(String(100), nullable=True)
    
    # 价格信息
    unit_price = Column(Float, nullable=False, default=0)
    price_type = Column(Enum(PriceType), nullable=False, default=PriceType.FIXED)
    bird_view_price = Column(Float, nullable=True)  # 鸟瞰图价格
    human_view_price = Column(Float, nullable=True)  # 人视图价格
    animation_price = Column(Float, nullable=True)   # 动画价格
    custom_price = Column(Float, nullable=True)      # 自定义价格
    
    # 支付信息
    bank_info = Column(String(500), nullable=True)
    payment_cycle = Column(Integer, nullable=False, default=30)  # 支付周期（天）
    
    # 技能和经验
    skills = Column(JSON, nullable=True)  # 技能列表
    join_date = Column(Date, nullable=True)
    status = Column(Enum(MemberStatus), nullable=False, default=MemberStatus.ACTIVE)
    
    # 当前项目
    current_projects = Column(JSON, nullable=True)  # 当前项目列表
    
    def __repr__(self):
        return f"<TeamMember(name='{self.name}', department='{self.department}')>" 
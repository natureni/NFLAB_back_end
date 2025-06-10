from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class ProjectStatus(str, enum.Enum):
    """项目状态枚举"""
    REPORTING = "reporting"     # 报备中
    MODELING = "modeling"       # 建模中
    RENDERING = "rendering"     # 渲染中
    DELIVERING = "delivering"   # 交付中
    COMPLETED = "completed"     # 已完成
    CANCELLED = "cancelled"     # 已取消


class PaymentStatus(str, enum.Enum):
    """付款状态枚举"""
    UNPAID = "unpaid"           # 未付款
    PARTIAL = "partial"         # 部分付款
    PAID = "paid"               # 已付款
    OVERDUE = "overdue"         # 逾期


class Currency(str, enum.Enum):
    """货币枚举"""
    USD = "USD"
    EUR = "EUR"
    AUD = "AUD"
    CNY = "CNY"
    CAD = "CAD"
    GBP = "GBP"
    SGD = "SGD"
    AED = "AED"


class Project(BaseModel):
    """项目模型"""
    __tablename__ = "projects"
    
    protocol_number = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.REPORTING)
    deadline = Column(DateTime, nullable=True)
    budget = Column(Float, nullable=False, default=0)
    currency = Column(Enum(Currency), nullable=False, default=Currency.CNY)
    exchange_rate = Column(Float, nullable=False, default=1.0)
    budget_cny = Column(Float, nullable=False, default=0)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.UNPAID)
    progress = Column(Integer, nullable=False, default=0)  # 0-100
    project_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    services = Column(JSON, nullable=True)  # 服务项目列表
    
    # 关联关系
    client = relationship("Client", back_populates="projects")
    
    def __repr__(self):
        return f"<Project(protocol_number='{self.protocol_number}', name='{self.name}')>" 
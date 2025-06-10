from sqlalchemy import Column, String, Text, JSON, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class ClientStatus(str, enum.Enum):
    """客户状态枚举"""
    ACTIVE = "active"           # 活跃
    INACTIVE = "inactive"       # 不活跃
    SUSPENDED = "suspended"     # 暂停


class Region(str, enum.Enum):
    """地区枚举"""
    ASIA_PACIFIC = "Asia-Pacific"
    NORTH_AMERICA = "North America"
    EUROPE = "Europe"
    MIDDLE_EAST = "Middle East"
    AFRICA = "Africa"
    SOUTH_AMERICA = "South America"


class Client(BaseModel):
    """客户模型"""
    __tablename__ = "clients"
    
    # 公司信息
    company_name = Column(String(200), nullable=False)
    company_name_cn = Column(String(200), nullable=True)
    
    # 联系人信息
    contact_person = Column(String(100), nullable=False)
    contact_person_cn = Column(String(100), nullable=True)
    title = Column(String(100), nullable=True)
    title_cn = Column(String(100), nullable=True)
    email = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)
    fax = Column(String(50), nullable=True)
    website = Column(String(200), nullable=True)
    
    # 地址信息
    business_address = Column(JSON, nullable=True)  # 详细地址JSON
    region = Column(Enum(Region), nullable=False)
    timezone = Column(String(50), nullable=True)
    language = Column(JSON, nullable=True)  # 语言列表
    
    # 业务信息
    business_type = Column(JSON, nullable=True)  # 业务类型列表
    project_preferences = Column(JSON, nullable=True)  # 项目偏好JSON
    project_history = Column(JSON, nullable=True)  # 项目历史统计JSON
    payment_info = Column(JSON, nullable=True)  # 支付信息JSON
    bank_info = Column(JSON, nullable=True)  # 银行信息JSON
    
    # 其他信息
    tags = Column(JSON, nullable=True)  # 标签列表
    notes = Column(Text, nullable=True)  # 备注
    status = Column(Enum(ClientStatus), nullable=False, default=ClientStatus.ACTIVE)
    last_contact = Column(String, nullable=True)  # 最后联系时间
    
    # 关联关系
    projects = relationship("Project", back_populates="client")
    
    def __repr__(self):
        return f"<Client(company_name='{self.company_name}', contact_person='{self.contact_person}')>" 
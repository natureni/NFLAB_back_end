from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.common import BaseSchema
from app.models.client import ClientStatus, Region


class BusinessAddress(BaseModel):
    """业务地址"""
    street: str
    city: str
    state: Optional[str] = None
    postcode: str
    country: str


class ProjectPreferences(BaseModel):
    """项目偏好"""
    style: List[str] = []
    budget: Optional[str] = None
    timeline: Optional[str] = None
    communication: List[str] = []


class ProjectHistory(BaseModel):
    """项目历史"""
    total: int = 0
    completed: int = 0
    ongoing: int = 0
    value: float = 0


class PaymentInfo(BaseModel):
    """支付信息"""
    terms: Optional[str] = None
    method: Optional[str] = None
    currency: Optional[str] = None
    credit_rating: Optional[str] = None


class BankInfo(BaseModel):
    """银行信息"""
    beneficiary_bank_name: Optional[str] = None
    beneficiary_bank_address: Optional[str] = None
    beneficiary_bank_code: Optional[str] = None
    swift_code: Optional[str] = None
    beneficiary_account_name: Optional[str] = None
    beneficiary_account_number: Optional[str] = None


class ClientCreate(BaseModel):
    """创建客户请求"""
    company_name: str
    company_name_cn: Optional[str] = None
    contact_person: str
    contact_person_cn: Optional[str] = None
    title: Optional[str] = None
    title_cn: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[str] = None
    business_address: Optional[BusinessAddress] = None
    region: Region
    timezone: Optional[str] = None
    language: Optional[List[str]] = None
    business_type: Optional[List[str]] = None
    project_preferences: Optional[ProjectPreferences] = None
    payment_info: Optional[PaymentInfo] = None
    bank_info: Optional[BankInfo] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    """更新客户请求"""
    company_name: Optional[str] = None
    company_name_cn: Optional[str] = None
    contact_person: Optional[str] = None
    contact_person_cn: Optional[str] = None
    title: Optional[str] = None
    title_cn: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[str] = None
    business_address: Optional[BusinessAddress] = None
    region: Optional[Region] = None
    timezone: Optional[str] = None
    language: Optional[List[str]] = None
    business_type: Optional[List[str]] = None
    project_preferences: Optional[ProjectPreferences] = None
    payment_info: Optional[PaymentInfo] = None
    bank_info: Optional[BankInfo] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ClientResponse(BaseSchema):
    """客户响应"""
    id: int
    company_name: str
    company_name_cn: Optional[str]
    contact_person: str
    contact_person_cn: Optional[str]
    title: Optional[str]
    title_cn: Optional[str]
    email: str
    phone: Optional[str]
    fax: Optional[str]
    website: Optional[str]
    business_address: Optional[Dict[str, Any]]
    region: Region
    timezone: Optional[str]
    language: Optional[List[str]]
    business_type: Optional[List[str]]
    project_preferences: Optional[Dict[str, Any]]
    project_history: Optional[Dict[str, Any]]
    payment_info: Optional[Dict[str, Any]]
    bank_info: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    notes: Optional[str]
    status: ClientStatus
    last_contact: Optional[str]
    created_at: datetime
    updated_at: datetime


class ClientListQuery(BaseModel):
    """客户列表查询参数"""
    page: int = 1
    page_size: int = 20
    region: Optional[Region] = None
    status: Optional[ClientStatus] = None
    search: Optional[str] = None 
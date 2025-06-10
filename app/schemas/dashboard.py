from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class ProjectStats(BaseModel):
    """项目统计"""
    total: int
    growth: int  # 增长百分比


class RevenueStats(BaseModel):
    """收入统计"""
    monthly: float
    growth: int  # 增长百分比


class TeamStats(BaseModel):
    """团队统计"""
    members: int
    workload: int  # 工作负载百分比


class ProjectStatusItem(BaseModel):
    """项目状态项"""
    name: str
    value: int


class MonthlyTrendItem(BaseModel):
    """月度趋势项"""
    month: str
    revenue: float
    projects: int


class DashboardStats(BaseModel):
    """仪表板统计数据"""
    projects: ProjectStats
    revenue: RevenueStats
    team: TeamStats
    success_rate: float
    project_status: List[ProjectStatusItem]
    monthly_trend: List[MonthlyTrendItem]


class FinanceOverview(BaseModel):
    """财务概览"""
    period: str
    revenue: Dict[str, float]
    costs: Dict[str, float]
    profit: Dict[str, float]
    projects: Dict[str, int]


class ExchangeRates(BaseModel):
    """汇率数据"""
    base_currency: str
    rates: Dict[str, float]
    last_updated: datetime 
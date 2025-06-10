from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.client import Client
from app.models.team import TeamMember
from app.schemas.dashboard import DashboardStats, ProjectStats, RevenueStats, TeamStats, ProjectStatusItem, MonthlyTrendItem, FinanceOverview, ExchangeRates
from app.schemas.common import ResponseModel
from app.api.deps import get_current_active_user

router = APIRouter()


@router.get("/stats", response_model=ResponseModel[DashboardStats])
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取仪表板统计数据"""
    
    now = datetime.now()
    current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    # 项目统计
    total_projects_query = select(func.count(Project.id))
    total_projects = await db.execute(total_projects_query)
    total_projects_count = total_projects.scalar()
    
    # 本月新项目
    current_month_projects_query = select(func.count(Project.id)).where(
        Project.created_at >= current_month
    )
    current_month_projects = await db.execute(current_month_projects_query)
    current_month_count = current_month_projects.scalar()
    
    # 上月项目
    last_month_projects_query = select(func.count(Project.id)).where(
        and_(
            Project.created_at >= last_month,
            Project.created_at < current_month
        )
    )
    last_month_projects = await db.execute(last_month_projects_query)
    last_month_count = last_month_projects.scalar()
    
    # 项目增长率
    project_growth = 0
    if last_month_count > 0:
        project_growth = int(((current_month_count - last_month_count) / last_month_count) * 100)
    elif current_month_count > 0:
        project_growth = 100
    
    # 收入统计
    current_month_revenue_query = select(func.sum(Project.budget_cny)).where(
        Project.created_at >= current_month
    )
    current_month_revenue = await db.execute(current_month_revenue_query)
    monthly_revenue = current_month_revenue.scalar() or 0
    
    last_month_revenue_query = select(func.sum(Project.budget_cny)).where(
        and_(
            Project.created_at >= last_month,
            Project.created_at < current_month
        )
    )
    last_month_revenue = await db.execute(last_month_revenue_query)
    last_month_revenue_amount = last_month_revenue.scalar() or 0
    
    # 收入增长率
    revenue_growth = 0
    if last_month_revenue_amount > 0:
        revenue_growth = int(((monthly_revenue - last_month_revenue_amount) / last_month_revenue_amount) * 100)
    elif monthly_revenue > 0:
        revenue_growth = 100
    
    # 团队统计
    team_count_query = select(func.count(TeamMember.id)).where(TeamMember.status == "active")
    team_count = await db.execute(team_count_query)
    team_members = team_count.scalar() or 0
    
    # 项目状态分布
    status_mapping = {
        "reporting": "报备中",
        "modeling": "建模中", 
        "rendering": "渲染中",
        "delivering": "交付中",
        "completed": "已完成"
    }
    
    project_status = []
    for status, name in status_mapping.items():
        status_count_query = select(func.count(Project.id)).where(Project.status == status)
        status_count = await db.execute(status_count_query)
        count = status_count.scalar() or 0
        project_status.append(ProjectStatusItem(name=name, value=count))
    
    # 月度趋势（最近6个月）
    monthly_trend = []
    for i in range(6):
        month_start = (current_month - timedelta(days=i*30)).replace(day=1)
        month_end = month_start.replace(month=month_start.month+1) if month_start.month < 12 else month_start.replace(year=month_start.year+1, month=1)
        
        month_projects_query = select(func.count(Project.id)).where(
            and_(
                Project.created_at >= month_start,
                Project.created_at < month_end
            )
        )
        month_projects = await db.execute(month_projects_query)
        month_project_count = month_projects.scalar() or 0
        
        month_revenue_query = select(func.sum(Project.budget_cny)).where(
            and_(
                Project.created_at >= month_start,
                Project.created_at < month_end
            )
        )
        month_revenue = await db.execute(month_revenue_query)
        month_revenue_amount = month_revenue.scalar() or 0
        
        monthly_trend.append(MonthlyTrendItem(
            month=month_start.strftime("%Y-%m"),
            revenue=float(month_revenue_amount),
            projects=month_project_count
        ))
    
    monthly_trend.reverse()  # 最新的在后面
    
    # 成功率（已完成项目比例）
    completed_projects_query = select(func.count(Project.id)).where(Project.status == "completed")
    completed_projects = await db.execute(completed_projects_query)
    completed_count = completed_projects.scalar() or 0
    
    success_rate = 0
    if total_projects_count > 0:
        success_rate = round((completed_count / total_projects_count) * 100, 1)
    
    dashboard_data = DashboardStats(
        projects=ProjectStats(total=total_projects_count, growth=project_growth),
        revenue=RevenueStats(monthly=monthly_revenue, growth=revenue_growth),
        team=TeamStats(members=team_members, workload=80),  # 假设80%工作负载
        success_rate=success_rate,
        project_status=project_status,
        monthly_trend=monthly_trend
    )
    
    return ResponseModel[DashboardStats](data=dashboard_data)


@router.get("/finance/overview", response_model=ResponseModel[FinanceOverview])
async def get_finance_overview(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取财务概览数据"""
    
    now = datetime.now()
    current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period = now.strftime("%Y-%m")
    
    # 收入统计
    total_revenue_query = select(func.sum(Project.budget_cny))
    total_revenue = await db.execute(total_revenue_query)
    total_revenue_amount = total_revenue.scalar() or 0
    
    completed_revenue_query = select(func.sum(Project.budget_cny)).where(
        Project.status == "completed"
    )
    completed_revenue = await db.execute(completed_revenue_query)
    completed_revenue_amount = completed_revenue.scalar() or 0
    
    pending_revenue = total_revenue_amount - completed_revenue_amount
    
    # 成本统计（简化版本）
    costs = {
        "project_manager": 17000,
        "modeling": 25000,
        "rendering": 35000,
        "sales": 8500,
        "fixed": 95000,
        "total": 180500
    }
    
    # 利润计算
    gross_profit = completed_revenue_amount - costs["total"]
    profit_margin = 0
    if completed_revenue_amount > 0:
        profit_margin = round((gross_profit / completed_revenue_amount) * 100, 1)
    
    # 项目统计
    total_projects_query = select(func.count(Project.id))
    total_projects = await db.execute(total_projects_query)
    total_projects_count = total_projects.scalar() or 0
    
    completed_projects_query = select(func.count(Project.id)).where(Project.status == "completed")
    completed_projects = await db.execute(completed_projects_query)
    completed_projects_count = completed_projects.scalar() or 0
    
    ongoing_projects = total_projects_count - completed_projects_count
    
    finance_data = FinanceOverview(
        period=period,
        revenue={
            "total": float(total_revenue_amount),
            "completed": float(completed_revenue_amount),
            "pending": float(pending_revenue)
        },
        costs=costs,
        profit={
            "gross": float(gross_profit),
            "margin": profit_margin
        },
        projects={
            "total": total_projects_count,
            "completed": completed_projects_count,
            "ongoing": ongoing_projects
        }
    )
    
    return ResponseModel[FinanceOverview](data=finance_data)


@router.get("/settings/exchange-rates", response_model=ResponseModel[ExchangeRates])
async def get_exchange_rates(
    current_user: User = Depends(get_current_active_user)
):
    """获取汇率配置"""
    
    # 模拟汇率数据，实际应用中应该从外部API获取
    exchange_rates = ExchangeRates(
        base_currency="CNY",
        rates={
            "USD": 7.24,
            "EUR": 7.85,
            "AUD": 4.78,
            "CAD": 5.32,
            "GBP": 9.12,
            "SGD": 5.36,
            "AED": 1.97
        },
        last_updated=datetime.now()
    )
    
    return ResponseModel[ExchangeRates](data=exchange_rates) 
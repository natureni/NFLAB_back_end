from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.api.deps import get_current_user, get_async_session
from app.schemas.finance import (
    FinanceOverviewResponse, RevenueDetailResponse, CostStructureResponse,
    FixedCostCreate, FixedCostUpdate, FixedCostResponse,
    ReceivableResponse, PaymentReminderRequest,
    ProfitLossResponse, CashFlowResponse, FinanceReportExportRequest
)
from app.models.project import Project, PaymentStatus, Currency
from app.models.client import Client
from app.models.user import User
from app.schemas.base import PaginatedResponse

router = APIRouter()

# 模拟固定成本数据存储
_fixed_costs = [
    {
        "id": 1,
        "category": "租金",
        "description": "办公室租金",
        "amount": 15000.0,
        "currency": Currency.CNY,
        "frequency": "monthly",
        "start_date": date(2024, 1, 1),
        "end_date": None,
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "category": "人员",
        "description": "基础工资",
        "amount": 50000.0,
        "currency": Currency.CNY,
        "frequency": "monthly",
        "start_date": date(2024, 1, 1),
        "end_date": None,
        "created_at": datetime.now()
    }
]


@router.get("/overview", response_model=FinanceOverviewResponse)
async def get_finance_overview(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    currency: Optional[Currency] = Query(Currency.CNY, description="显示货币"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """获取财务概览"""
    
    # 设置默认日期范围（当前年度）
    if not start_date:
        start_date = date(datetime.now().year, 1, 1)
    if not end_date:
        end_date = date.today()
    
    # 获取项目收入数据
    query = select(Project).where(
        and_(
            Project.created_at >= start_date,
            Project.created_at <= end_date
        )
    )
    result = await db.execute(query)
    projects = result.scalars().all()
    
    # 计算收入统计
    total_projects = len(projects)
    total_revenue = sum(p.budget_cny for p in projects)
    paid_revenue = sum(p.budget_cny for p in projects if p.payment_status == PaymentStatus.PAID)
    pending_revenue = sum(p.budget_cny for p in projects if p.payment_status == PaymentStatus.PENDING)
    
    # 计算固定成本
    monthly_fixed_costs = sum(cost["amount"] for cost in _fixed_costs if cost["frequency"] == "monthly")
    months_count = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    total_fixed_costs = monthly_fixed_costs * months_count
    
    # 计算项目成本（估算）
    project_costs = total_revenue * 0.6  # 假设项目成本为收入的60%
    
    total_costs = total_fixed_costs + project_costs
    net_profit = total_revenue - total_costs
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return FinanceOverviewResponse(
        period=f"{start_date} 至 {end_date}",
        currency=currency,
        total_revenue=total_revenue,
        paid_revenue=paid_revenue,
        pending_revenue=pending_revenue,
        total_costs=total_costs,
        fixed_costs=total_fixed_costs,
        project_costs=project_costs,
        net_profit=net_profit,
        profit_margin=profit_margin,
        total_projects=total_projects,
        paid_projects=len([p for p in projects if p.payment_status == PaymentStatus.PAID]),
        pending_projects=len([p for p in projects if p.payment_status == PaymentStatus.PENDING])
    )


@router.get("/revenue", response_model=PaginatedResponse[RevenueDetailResponse])
async def get_revenue_details(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="每页记录数"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    payment_status: Optional[PaymentStatus] = Query(None, description="支付状态"),
    client_id: Optional[int] = Query(None, description="客户ID"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """获取收入明细"""
    
    # 构建查询
    query = select(Project).join(Client, Project.client_id == Client.id)
    
    conditions = []
    if start_date:
        conditions.append(Project.created_at >= start_date)
    if end_date:
        conditions.append(Project.created_at <= end_date)
    if payment_status:
        conditions.append(Project.payment_status == payment_status)
    if client_id:
        conditions.append(Project.client_id == client_id)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 应用分页和排序
    query = query.order_by(desc(Project.created_at)).offset(skip).limit(limit)
    
    # 执行查询
    result = await db.execute(query)
    projects = result.scalars().all()
    
    # 构建响应数据
    revenue_details = []
    for project in projects:
        # 获取客户信息
        client_query = select(Client).where(Client.id == project.client_id)
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()
        
        revenue_details.append(RevenueDetailResponse(
            project_id=project.id,
            project_name=project.name,
            protocol_number=project.protocol_number,
            client_name=client.company_name if client else "未知客户",
            amount=project.budget,
            currency=project.currency,
            amount_cny=project.budget_cny,
            payment_status=project.payment_status,
            invoice_date=project.created_at.date(),
            payment_date=project.updated_at.date() if project.payment_status == PaymentStatus.PAID else None,
            payment_terms=30  # 默认30天付款期
        ))
    
    return PaginatedResponse(
        items=revenue_details,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.put("/projects/{project_id}/payment")
async def update_payment_status(
    project_id: int,
    payment_status: PaymentStatus,
    payment_date: Optional[date] = None,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """更新项目付款状态"""
    
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 更新支付状态
    project.payment_status = payment_status
    if payment_date:
        project.updated_at = datetime.combine(payment_date, datetime.min.time())
    
    await db.commit()
    await db.refresh(project)
    
    return {
        "message": "付款状态更新成功",
        "project_id": project_id,
        "payment_status": payment_status,
        "updated_at": project.updated_at
    }


@router.get("/costs", response_model=CostStructureResponse)
async def get_cost_structure(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """获取成本结构"""
    
    # 设置默认日期范围
    if not start_date:
        start_date = date(datetime.now().year, 1, 1)
    if not end_date:
        end_date = date.today()
    
    # 计算固定成本
    monthly_costs = {}
    for cost in _fixed_costs:
        category = cost["category"]
        if category not in monthly_costs:
            monthly_costs[category] = 0
        if cost["frequency"] == "monthly":
            monthly_costs[category] += cost["amount"]
    
    months_count = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    fixed_costs = {category: amount * months_count for category, amount in monthly_costs.items()}
    
    # 计算项目成本
    query = select(Project).where(
        and_(
            Project.created_at >= start_date,
            Project.created_at <= end_date
        )
    )
    result = await db.execute(query)
    projects = result.scalars().all()
    
    total_revenue = sum(p.budget_cny for p in projects)
    project_costs = {
        "人工成本": total_revenue * 0.4,
        "软件许可": total_revenue * 0.1,
        "硬件设备": total_revenue * 0.05,
        "其他费用": total_revenue * 0.05
    }
    
    # 合并成本
    all_costs = {**fixed_costs, **project_costs}
    total_costs = sum(all_costs.values())
    
    cost_breakdown = [
        {"category": category, "amount": amount, "percentage": (amount / total_costs * 100) if total_costs > 0 else 0}
        for category, amount in all_costs.items()
    ]
    
    return CostStructureResponse(
        period=f"{start_date} 至 {end_date}",
        total_costs=total_costs,
        fixed_costs=sum(fixed_costs.values()),
        variable_costs=sum(project_costs.values()),
        cost_breakdown=cost_breakdown
    )


@router.get("/costs/fixed", response_model=List[FixedCostResponse])
async def get_fixed_costs(
    current_user: User = Depends(get_current_user)
):
    """获取固定成本列表"""
    return [FixedCostResponse(**cost) for cost in _fixed_costs]


@router.post("/costs/fixed", response_model=FixedCostResponse)
async def create_fixed_cost(
    cost_data: FixedCostCreate,
    current_user: User = Depends(get_current_user)
):
    """录入固定成本"""
    
    new_cost = {
        "id": max([cost["id"] for cost in _fixed_costs], default=0) + 1,
        **cost_data.dict(),
        "created_at": datetime.now()
    }
    _fixed_costs.append(new_cost)
    
    return FixedCostResponse(**new_cost)


@router.put("/costs/fixed/{cost_id}", response_model=FixedCostResponse)
async def update_fixed_cost(
    cost_id: int,
    cost_data: FixedCostUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新固定成本"""
    
    cost = next((c for c in _fixed_costs if c["id"] == cost_id), None)
    if not cost:
        raise HTTPException(status_code=404, detail="固定成本记录不存在")
    
    update_data = cost_data.dict(exclude_unset=True)
    cost.update(update_data)
    
    return FixedCostResponse(**cost)


@router.get("/receivables", response_model=List[ReceivableResponse])
async def get_receivables(
    overdue_only: bool = Query(False, description="仅显示逾期账款"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """获取应收账款明细"""
    
    query = select(Project).join(Client, Project.client_id == Client.id).where(
        Project.payment_status.in_([PaymentStatus.PENDING, PaymentStatus.OVERDUE])
    )
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    receivables = []
    for project in projects:
        # 获取客户信息
        client_query = select(Client).where(Client.id == project.client_id)
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()
        
        # 计算逾期天数
        days_overdue = 0
        if project.payment_status == PaymentStatus.OVERDUE:
            expected_payment_date = project.created_at.date() + timedelta(days=30)
            days_overdue = (date.today() - expected_payment_date).days
        
        # 过滤逾期账款
        if overdue_only and days_overdue <= 0:
            continue
        
        receivables.append(ReceivableResponse(
            project_id=project.id,
            project_name=project.name,
            protocol_number=project.protocol_number,
            client_name=client.company_name if client else "未知客户",
            client_contact=client.contact_person if client else "",
            amount=project.budget_cny,
            currency=Currency.CNY,
            invoice_date=project.created_at.date(),
            due_date=project.created_at.date() + timedelta(days=30),
            days_overdue=max(0, days_overdue),
            payment_status=project.payment_status
        ))
    
    return receivables


@router.put("/receivables/{project_id}/reminder")
async def send_payment_reminder(
    project_id: int,
    reminder_data: PaymentReminderRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """发送付款提醒"""
    
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 这里应该实现实际的邮件/短信发送逻辑
    # 暂时返回模拟响应
    
    return {
        "message": "付款提醒已发送",
        "project_id": project_id,
        "reminder_type": reminder_data.reminder_type,
        "sent_at": datetime.now()
    }


@router.get("/reports/profit-loss", response_model=ProfitLossResponse)
async def get_profit_loss_report(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """获取利润表"""
    
    # 获取收入数据
    query = select(Project).where(
        and_(
            Project.created_at >= start_date,
            Project.created_at <= end_date
        )
    )
    result = await db.execute(query)
    projects = result.scalars().all()
    
    total_revenue = sum(p.budget_cny for p in projects)
    
    # 计算成本
    months_count = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    monthly_fixed_costs = sum(cost["amount"] for cost in _fixed_costs if cost["frequency"] == "monthly")
    fixed_costs = monthly_fixed_costs * months_count
    variable_costs = total_revenue * 0.6
    
    gross_profit = total_revenue - variable_costs
    operating_profit = gross_profit - fixed_costs
    
    return ProfitLossResponse(
        period=f"{start_date} 至 {end_date}",
        total_revenue=total_revenue,
        cost_of_goods_sold=variable_costs,
        gross_profit=gross_profit,
        operating_expenses=fixed_costs,
        operating_profit=operating_profit,
        other_income=0,
        other_expenses=0,
        net_profit=operating_profit,
        tax_expense=operating_profit * 0.25 if operating_profit > 0 else 0,
        net_profit_after_tax=operating_profit * 0.75 if operating_profit > 0 else operating_profit
    )


@router.get("/reports/cash-flow", response_model=CashFlowResponse)
async def get_cash_flow_report(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """获取现金流量表"""
    
    # 经营活动现金流
    query = select(Project).where(
        and_(
            Project.created_at >= start_date,
            Project.created_at <= end_date,
            Project.payment_status == PaymentStatus.PAID
        )
    )
    result = await db.execute(query)
    paid_projects = result.scalars().all()
    
    cash_from_operations = sum(p.budget_cny for p in paid_projects)
    
    # 计算支出
    months_count = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    monthly_fixed_costs = sum(cost["amount"] for cost in _fixed_costs if cost["frequency"] == "monthly")
    cash_paid_for_expenses = monthly_fixed_costs * months_count
    
    net_cash_from_operations = cash_from_operations - cash_paid_for_expenses
    
    return CashFlowResponse(
        period=f"{start_date} 至 {end_date}",
        cash_from_operations=cash_from_operations,
        cash_paid_for_expenses=cash_paid_for_expenses,
        net_cash_from_operations=net_cash_from_operations,
        cash_from_investing=0,
        cash_paid_for_investing=0,
        net_cash_from_investing=0,
        cash_from_financing=0,
        cash_paid_for_financing=0,
        net_cash_from_financing=0,
        net_change_in_cash=net_cash_from_operations,
        beginning_cash_balance=100000,  # 假设期初现金
        ending_cash_balance=100000 + net_cash_from_operations
    ) 
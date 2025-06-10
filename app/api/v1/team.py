from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional
from datetime import datetime, date
import calendar

from app.core.database import get_async_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.team import TeamMember, Department, MemberStatus
from app.models.project import Project
from app.schemas.team import (
    TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse,
    TeamMemberList, WorkloadResponse, PaymentCreate, PaymentResponse,
    PaymentStatus as PaymentStatusEnum, PaymentStatus, PaymentStatusUpdate,
    PaymentHistoryResponse
)
from app.schemas.common import PaginatedResponse

router = APIRouter()

# 薪资支付记录存储（实际应用中应该用数据库表）
_payment_records = {}
_payment_id_counter = 1


@router.get("/members", response_model=PaginatedResponse[TeamMemberResponse])
async def get_team_members(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="每页记录数"),
    department: Optional[Department] = Query(None, description="部门筛选"),
    status: Optional[MemberStatus] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """获取团队成员列表"""
    
    # 构建查询
    query = select(TeamMember)
    
    # 添加筛选条件
    conditions = []
    if department:
        conditions.append(TeamMember.department == department)
    if status:
        conditions.append(TeamMember.status == status)
    if search:
        conditions.append(
            or_(
                TeamMember.name.ilike(f"%{search}%"),
                TeamMember.phone.ilike(f"%{search}%")
            )
        )
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 应用分页和排序
    query = query.order_by(desc(TeamMember.created_at)).offset(skip).limit(limit)
    
    # 执行查询
    result = await db.execute(query)
    members = result.scalars().all()
    
    return PaginatedResponse(
        items=[TeamMemberResponse.from_orm(member) for member in members],
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.post("/members", response_model=TeamMemberResponse)
async def create_team_member(
    member_data: TeamMemberCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """添加团队成员"""
    
    # 检查是否重复
    existing_query = select(TeamMember).where(TeamMember.name == member_data.name)
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="团队成员已存在")
    
    # 创建新成员
    member = TeamMember(**member_data.dict())
    db.add(member)
    await db.commit()
    await db.refresh(member)
    
    return TeamMemberResponse.from_orm(member)


@router.get("/members/{member_id}", response_model=TeamMemberResponse)
async def get_team_member(
    member_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """获取团队成员详情"""
    
    query = select(TeamMember).where(TeamMember.id == member_id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="团队成员不存在")
    
    return TeamMemberResponse.from_orm(member)


@router.put("/members/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: int,
    member_data: TeamMemberUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """更新团队成员信息"""
    
    query = select(TeamMember).where(TeamMember.id == member_id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="团队成员不存在")
    
    # 更新字段
    update_data = member_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)
    
    await db.commit()
    await db.refresh(member)
    
    return TeamMemberResponse.from_orm(member)


@router.delete("/members/{member_id}")
async def delete_team_member(
    member_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """删除团队成员"""
    
    query = select(TeamMember).where(TeamMember.id == member_id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="团队成员不存在")
    
    await db.delete(member)
    await db.commit()
    
    return {"message": "团队成员已删除"}


@router.get("/workload", response_model=List[WorkloadResponse])
async def get_team_workload(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    department: Optional[Department] = Query(None, description="部门筛选"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """获取团队工作量统计"""
    
    # 获取团队成员
    query = select(TeamMember)
    if department:
        query = query.where(TeamMember.department == department)
    query = query.where(TeamMember.status == MemberStatus.ACTIVE)
    
    result = await db.execute(query)
    members = result.scalars().all()
    
    workload_data = []
    for member in members:
        # 获取项目工作量
        current_projects = member.current_projects or []
        
        # 计算工作量
        total_workload = len(current_projects)
        estimated_hours = total_workload * 40  # 假设每个项目40小时
        
        workload_data.append(WorkloadResponse(
            member_id=member.id,
            member_name=member.name,
            department=member.department,
            current_projects=current_projects,
            total_workload=total_workload,
            estimated_hours=estimated_hours,
            utilization_rate=min(total_workload * 0.8, 1.0)  # 假设利用率
        ))
    
    return workload_data


@router.put("/members/{member_id}/workload")
async def assign_member_workload(
    member_id: int,
    project_ids: List[int],
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """分配项目工作量"""
    
    query = select(TeamMember).where(TeamMember.id == member_id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="团队成员不存在")
    
    # 验证项目是否存在
    project_query = select(Project).where(Project.id.in_(project_ids))
    project_result = await db.execute(project_query)
    projects = project_result.scalars().all()
    
    if len(projects) != len(project_ids):
        raise HTTPException(status_code=400, detail="部分项目不存在")
    
    # 更新成员的当前项目
    member.current_projects = [{"id": p.id, "name": p.name} for p in projects]
    await db.commit()
    
    return {"message": "工作量分配成功", "assigned_projects": len(project_ids)}


@router.post("/payments/calculate")
async def calculate_monthly_salary(
    year: int = Query(..., description="年份"),
    month: int = Query(..., description="月份", ge=1, le=12),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """计算月度薪资"""
    
    # 获取所有活跃成员
    query = select(TeamMember).where(TeamMember.status == MemberStatus.ACTIVE)
    result = await db.execute(query)
    members = result.scalars().all()
    
    salary_calculations = []
    global _payment_id_counter
    
    for member in members:
        # 计算基础薪资
        base_salary = member.unit_price
        
        # 根据工作量计算奖金
        current_projects = member.current_projects or []
        project_bonus = len(current_projects) * 500  # 每个项目500元奖金
        
        total_salary = base_salary + project_bonus
        
        # 创建薪资支付记录
        payment_record = {
            "payment_id": _payment_id_counter,
            "member_id": member.id,
            "member_name": member.name,
            "department": member.department,
            "year": year,
            "month": month,
            "base_salary": base_salary,
            "project_bonus": project_bonus,
            "total_salary": total_salary,
            "payment_status": PaymentStatus.PENDING,
            "calculated_at": datetime.now(),
            "paid_at": None,
            "notes": ""
        }
        
        _payment_records[_payment_id_counter] = payment_record
        _payment_id_counter += 1
        
        salary_calculations.append({
            "payment_id": payment_record["payment_id"],
            "member_id": member.id,
            "member_name": member.name,
            "base_salary": base_salary,
            "project_bonus": project_bonus,
            "total_salary": total_salary,
            "calculation_date": datetime.now().date()
        })
    
    return {
        "year": year,
        "month": month,
        "calculations": salary_calculations,
        "total_amount": sum(calc["total_salary"] for calc in salary_calculations),
        "created_payments": len(salary_calculations)
    }


@router.put("/payments/{payment_id}/status", response_model=PaymentResponse)
async def update_payment_status(
    payment_id: int,
    status_data: PaymentStatusUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新薪资支付状态"""
    
    if payment_id not in _payment_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="薪资支付记录不存在"
        )
    
    payment_record = _payment_records[payment_id]
    
    # 更新状态
    payment_record["payment_status"] = status_data.payment_status
    payment_record["notes"] = status_data.notes or payment_record["notes"]
    
    # 如果状态改为已支付，记录支付时间
    if status_data.payment_status == PaymentStatus.PAID:
        payment_record["paid_at"] = datetime.now()
    elif status_data.payment_status == PaymentStatus.PENDING:
        payment_record["paid_at"] = None
    
    return PaymentResponse(
        payment_id=payment_record["payment_id"],
        member_id=payment_record["member_id"],
        member_name=payment_record["member_name"],
        department=payment_record["department"],
        year=payment_record["year"],
        month=payment_record["month"],
        base_salary=payment_record["base_salary"],
        project_bonus=payment_record["project_bonus"],
        total_salary=payment_record["total_salary"],
        payment_status=payment_record["payment_status"],
        calculated_at=payment_record["calculated_at"],
        paid_at=payment_record["paid_at"],
        notes=payment_record["notes"]
    )


@router.get("/payments/history", response_model=List[PaymentHistoryResponse])
async def get_payment_history(
    member_id: Optional[int] = Query(None, description="成员ID"),
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, description="月份"),
    payment_status: Optional[PaymentStatus] = Query(None, description="支付状态"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    current_user: User = Depends(get_current_user)
):
    """获取薪资支付历史记录"""
    
    # 筛选记录
    filtered_records = []
    
    for payment_record in _payment_records.values():
        # 应用筛选条件
        if member_id and payment_record["member_id"] != member_id:
            continue
        if year and payment_record["year"] != year:
            continue
        if month and payment_record["month"] != month:
            continue
        if payment_status and payment_record["payment_status"] != payment_status:
            continue
        
        filtered_records.append(payment_record)
    
    # 按时间倒序排序
    filtered_records.sort(key=lambda x: x["calculated_at"], reverse=True)
    
    # 限制返回数量
    filtered_records = filtered_records[:limit]
    
    # 转换为响应格式
    history_records = []
    for record in filtered_records:
        # 计算工作天数（简化计算）
        working_days = 22  # 假设每月22个工作日
        daily_rate = record["total_salary"] / working_days if working_days > 0 else 0
        
        history_records.append(PaymentHistoryResponse(
            payment_id=record["payment_id"],
            member_id=record["member_id"],
            member_name=record["member_name"],
            department=record["department"],
            period=f"{record['year']}-{record['month']:02d}",
            total_salary=record["total_salary"],
            payment_status=record["payment_status"],
            paid_at=record["paid_at"],
            working_days=working_days,
            daily_rate=daily_rate,
            notes=record["notes"]
        ))
    
    return history_records


@router.get("/payments/summary")
async def get_payment_summary(
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, description="月份"),
    current_user: User = Depends(get_current_user)
):
    """获取薪资支付汇总统计"""
    
    # 筛选记录
    filtered_records = []
    for payment_record in _payment_records.values():
        if year and payment_record["year"] != year:
            continue
        if month and payment_record["month"] != month:
            continue
        filtered_records.append(payment_record)
    
    if not filtered_records:
        return {
            "period": f"{year}-{month:02d}" if year and month else "全部",
            "total_payments": 0,
            "total_amount": 0,
            "paid_amount": 0,
            "pending_amount": 0,
            "payment_statistics": {
                "paid": 0,
                "pending": 0,
                "cancelled": 0
            },
            "department_breakdown": {}
        }
    
    # 统计数据
    total_payments = len(filtered_records)
    total_amount = sum(record["total_salary"] for record in filtered_records)
    paid_amount = sum(record["total_salary"] for record in filtered_records 
                     if record["payment_status"] == PaymentStatus.PAID)
    pending_amount = sum(record["total_salary"] for record in filtered_records 
                        if record["payment_status"] == PaymentStatus.PENDING)
    
    # 状态统计
    payment_statistics = {
        "paid": len([r for r in filtered_records if r["payment_status"] == PaymentStatus.PAID]),
        "pending": len([r for r in filtered_records if r["payment_status"] == PaymentStatus.PENDING]),
        "cancelled": len([r for r in filtered_records if r["payment_status"] == PaymentStatus.CANCELLED])
    }
    
    # 部门统计
    department_breakdown = {}
    for record in filtered_records:
        dept = record["department"]
        if dept not in department_breakdown:
            department_breakdown[dept] = {
                "count": 0,
                "total_amount": 0,
                "paid_amount": 0
            }
        department_breakdown[dept]["count"] += 1
        department_breakdown[dept]["total_amount"] += record["total_salary"]
        if record["payment_status"] == PaymentStatus.PAID:
            department_breakdown[dept]["paid_amount"] += record["total_salary"]
    
    return {
        "period": f"{year}-{month:02d}" if year and month else "全部",
        "total_payments": total_payments,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
        "payment_rate": (paid_amount / total_amount * 100) if total_amount > 0 else 0,
        "payment_statistics": payment_statistics,
        "department_breakdown": department_breakdown
    }


@router.get("/payments", response_model=List[PaymentResponse])
async def get_payment_records(
    member_id: Optional[int] = Query(None, description="成员ID"),
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, description="月份"),
    payment_status: Optional[PaymentStatus] = Query(None, description="支付状态"),
    current_user: User = Depends(get_current_user)
):
    """获取薪资支付记录"""
    
    # 筛选记录
    filtered_records = []
    
    for payment_record in _payment_records.values():
        # 应用筛选条件
        if member_id and payment_record["member_id"] != member_id:
            continue
        if year and payment_record["year"] != year:
            continue
        if month and payment_record["month"] != month:
            continue
        if payment_status and payment_record["payment_status"] != payment_status:
            continue
        
        filtered_records.append(payment_record)
    
    # 按时间倒序排序
    filtered_records.sort(key=lambda x: x["calculated_at"], reverse=True)
    
    # 转换为响应格式
    payment_responses = []
    for record in filtered_records:
        payment_responses.append(PaymentResponse(
            payment_id=record["payment_id"],
            member_id=record["member_id"],
            member_name=record["member_name"],
            department=record["department"],
            year=record["year"],
            month=record["month"],
            base_salary=record["base_salary"],
            project_bonus=record["project_bonus"],
            total_salary=record["total_salary"],
            payment_status=record["payment_status"],
            calculated_at=record["calculated_at"],
            paid_at=record["paid_at"],
            notes=record["notes"]
        ))
    
    return payment_responses 
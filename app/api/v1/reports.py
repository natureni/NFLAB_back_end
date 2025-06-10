from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
import uuid
import json
import pandas as pd
from pathlib import Path
import asyncio

from app.core.database import get_async_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.project import Project, PaymentStatus
from app.models.client import Client
from app.models.team import TeamMember
from app.schemas.reports import (
    ReportExportRequest, ReportExportResponse, ReportType, ExportFormat,
    ProjectReportData, ClientReportData, FinanceReportData, TeamReportData
)

router = APIRouter()

# 报表导出任务存储
_export_tasks = {}

# 导出文件存储目录
EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

async def generate_projects_report(
    db: AsyncSession,
    start_date: date = None,
    end_date: date = None,
    filters: Dict[str, Any] = None
) -> List[ProjectReportData]:
    """生成项目报表数据"""
    query = select(Project).join(Client, Project.client_id == Client.id)
    
    # 应用日期筛选
    conditions = []
    if start_date:
        conditions.append(Project.created_at >= start_date)
    if end_date:
        conditions.append(Project.created_at <= end_date)
    
    # 应用其他筛选条件
    if filters:
        if filters.get("status"):
            conditions.append(Project.status == filters["status"])
        if filters.get("client_id"):
            conditions.append(Project.client_id == filters["client_id"])
        if filters.get("payment_status"):
            conditions.append(Project.payment_status == filters["payment_status"])
    
    if conditions:
        query = query.where(*conditions)
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    report_data = []
    for project in projects:
        # 获取客户信息
        client_query = select(Client).where(Client.id == project.client_id)
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()
        
        report_data.append(ProjectReportData(
            project_id=project.id,
            project_name=project.name,
            protocol_number=project.protocol_number,
            client_name=client.company_name if client else "未知客户",
            status=project.status,
            progress=project.progress,
            budget=project.budget,
            currency=project.currency,
            budget_cny=project.budget_cny,
            payment_status=project.payment_status,
            deadline=project.deadline,
            created_at=project.created_at
        ))
    
    return report_data

async def generate_clients_report(
    db: AsyncSession,
    start_date: date = None,
    end_date: date = None,
    filters: Dict[str, Any] = None
) -> List[ClientReportData]:
    """生成客户报表数据"""
    query = select(Client)
    
    # 应用日期筛选
    conditions = []
    if start_date:
        conditions.append(Client.created_at >= start_date)
    if end_date:
        conditions.append(Client.created_at <= end_date)
    
    # 应用其他筛选条件
    if filters:
        if filters.get("region"):
            conditions.append(Client.region == filters["region"])
    
    if conditions:
        query = query.where(*conditions)
    
    result = await db.execute(query)
    clients = result.scalars().all()
    
    report_data = []
    for client in clients:
        # 统计客户项目信息
        projects_query = select(func.count(), func.sum(Project.budget_cny)).select_from(Project).where(
            Project.client_id == client.id
        )
        projects_result = await db.execute(projects_query)
        total_projects, total_revenue = projects_result.first()
        total_projects = total_projects or 0
        total_revenue = total_revenue or 0.0
        
        # 统计活跃项目
        active_projects_query = select(func.count()).select_from(Project).where(
            Project.client_id == client.id,
            Project.status.in_(["reporting", "modeling", "rendering", "delivery"])
        )
        active_projects_result = await db.execute(active_projects_query)
        active_projects = active_projects_result.scalar() or 0
        
        report_data.append(ClientReportData(
            client_id=client.id,
            company_name=client.company_name,
            contact_person=client.contact_person,
            email=client.email,
            phone=client.phone,
            region=client.region,
            total_projects=total_projects,
            total_revenue=total_revenue,
            active_projects=active_projects,
            created_at=client.created_at
        ))
    
    return report_data

async def generate_team_report(
    db: AsyncSession,
    start_date: date = None,
    end_date: date = None,
    filters: Dict[str, Any] = None
) -> List[TeamReportData]:
    """生成团队报表数据"""
    query = select(TeamMember)
    
    # 应用筛选条件
    conditions = []
    if filters:
        if filters.get("department"):
            conditions.append(TeamMember.department == filters["department"])
        if filters.get("status"):
            conditions.append(TeamMember.status == filters["status"])
    
    if conditions:
        query = query.where(*conditions)
    
    result = await db.execute(query)
    members = result.scalars().all()
    
    report_data = []
    for member in members:
        current_projects = member.current_projects or []
        workload = len(current_projects)
        
        # 计算月度薪资
        monthly_salary = member.unit_price + (workload * 500)  # 基础薪资 + 项目奖金
        
        report_data.append(TeamReportData(
            member_id=member.id,
            member_name=member.name,
            department=member.department,
            unit_price=member.unit_price,
            current_projects=workload,
            workload=workload * 0.8,  # 假设利用率
            monthly_salary=monthly_salary,
            status=member.status
        ))
    
    return report_data

async def export_to_excel(data: List[Any], filename: str) -> str:
    """导出到Excel文件"""
    df = pd.DataFrame([item.dict() for item in data])
    
    file_path = EXPORT_DIR / filename
    df.to_excel(file_path, index=False, engine='openpyxl')
    
    return str(file_path)

async def export_to_csv(data: List[Any], filename: str) -> str:
    """导出到CSV文件"""
    df = pd.DataFrame([item.dict() for item in data])
    
    file_path = EXPORT_DIR / filename
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    return str(file_path)

async def export_to_json(data: List[Any], filename: str) -> str:
    """导出到JSON文件"""
    file_path = EXPORT_DIR / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump([item.dict() for item in data], f, ensure_ascii=False, indent=2, default=str)
    
    return str(file_path)

async def process_export_task(
    task_id: str,
    request: ReportExportRequest,
    db: AsyncSession
):
    """处理导出任务"""
    try:
        # 更新任务状态
        _export_tasks[task_id]["status"] = "processing"
        
        # 生成报表数据
        if request.report_type == ReportType.PROJECTS:
            data = await generate_projects_report(db, request.start_date, request.end_date, request.filters)
        elif request.report_type == ReportType.CLIENTS:
            data = await generate_clients_report(db, request.start_date, request.end_date, request.filters)
        elif request.report_type == ReportType.TEAM:
            data = await generate_team_report(db, request.start_date, request.end_date, request.filters)
        else:
            # 其他报表类型的数据生成逻辑
            data = []
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{request.report_type.value}_report_{timestamp}.{request.format.value}"
        
        # 根据格式导出文件
        if request.format == ExportFormat.EXCEL:
            file_path = await export_to_excel(data, filename)
        elif request.format == ExportFormat.CSV:
            file_path = await export_to_csv(data, filename)
        elif request.format == ExportFormat.JSON:
            file_path = await export_to_json(data, filename)
        else:
            raise ValueError(f"不支持的导出格式: {request.format}")
        
        # 更新任务状态
        _export_tasks[task_id]["status"] = "completed"
        _export_tasks[task_id]["file_path"] = file_path
        _export_tasks[task_id]["file_url"] = f"/api/reports/download/{task_id}"
        _export_tasks[task_id]["completed_at"] = datetime.now()
        
    except Exception as e:
        # 更新任务状态为失败
        _export_tasks[task_id]["status"] = "failed"
        _export_tasks[task_id]["error"] = str(e)

@router.post("/export", response_model=ReportExportResponse, summary="导出报表")
async def export_report(
    request: ReportExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """导出指定类型的报表"""
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 创建导出任务
    task_info = {
        "task_id": task_id,
        "report_type": request.report_type,
        "format": request.format,
        "status": "pending",
        "created_by": current_user.id,
        "created_at": datetime.now(),
        "estimated_completion": datetime.now() + timedelta(minutes=5),
        "file_url": None,
        "file_path": None
    }
    
    _export_tasks[task_id] = task_info
    
    # 添加后台任务
    background_tasks.add_task(process_export_task, task_id, request, db)
    
    return ReportExportResponse(
        task_id=task_id,
        report_type=request.report_type,
        format=request.format,
        status="pending",
        created_at=task_info["created_at"],
        estimated_completion=task_info["estimated_completion"]
    )

@router.get("/export/{task_id}/status", response_model=ReportExportResponse, summary="查询导出任务状态")
async def get_export_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """查询导出任务的状态"""
    
    if task_id not in _export_tasks:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    
    task_info = _export_tasks[task_id]
    
    # 检查权限
    if task_info["created_by"] != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限查看此任务")
    
    return ReportExportResponse(
        task_id=task_id,
        report_type=task_info["report_type"],
        format=task_info["format"],
        status=task_info["status"],
        file_url=task_info.get("file_url"),
        created_at=task_info["created_at"],
        estimated_completion=task_info.get("estimated_completion")
    )

@router.get("/download/{task_id}", summary="下载导出文件")
async def download_export_file(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """下载导出的文件"""
    
    if task_id not in _export_tasks:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    
    task_info = _export_tasks[task_id]
    
    # 检查权限
    if task_info["created_by"] != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限下载此文件")
    
    # 检查任务状态
    if task_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="文件尚未生成完成")
    
    file_path = Path(task_info["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )

@router.get("/tasks", response_model=List[ReportExportResponse], summary="获取导出任务列表")
async def get_export_tasks(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的导出任务列表"""
    
    user_tasks = []
    for task_id, task_info in _export_tasks.items():
        # 只显示当前用户的任务（管理员可以看到所有任务）
        if task_info["created_by"] == current_user.id or current_user.role == "admin":
            user_tasks.append(ReportExportResponse(
                task_id=task_id,
                report_type=task_info["report_type"],
                format=task_info["format"],
                status=task_info["status"],
                file_url=task_info.get("file_url"),
                created_at=task_info["created_at"],
                estimated_completion=task_info.get("estimated_completion")
            ))
    
    # 按创建时间倒序排序
    user_tasks.sort(key=lambda x: x.created_at, reverse=True)
    
    return user_tasks

@router.delete("/tasks/{task_id}", summary="删除导出任务")
async def delete_export_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除导出任务和相关文件"""
    
    if task_id not in _export_tasks:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    
    task_info = _export_tasks[task_id]
    
    # 检查权限
    if task_info["created_by"] != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限删除此任务")
    
    # 删除文件
    if task_info.get("file_path"):
        file_path = Path(task_info["file_path"])
        if file_path.exists():
            file_path.unlink()
    
    # 删除任务记录
    del _export_tasks[task_id]
    
    return {"message": "导出任务已删除", "task_id": task_id} 
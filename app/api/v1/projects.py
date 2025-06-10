from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json
from pathlib import Path

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.client import Client
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListQuery,
    ProjectStatusUpdate, ProjectProgressUpdate, GanttProject
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.api.deps import get_current_active_user

router = APIRouter()

# 服务模板存储
SERVICE_TEMPLATES = {
    "商业综合体": [
        {"camera": "Bird's Eye View", "unit_price": 8000, "description": "鸟瞰视角展示整体规划"},
        {"camera": "Human View", "unit_price": 6000, "description": "人视角展示建筑细节"},
        {"camera": "Interior View", "unit_price": 5000, "description": "室内空间展示"}
    ],
    "住宅项目": [
        {"camera": "Aerial View", "unit_price": 7000, "description": "空中视角展示住宅布局"},
        {"camera": "Street View", "unit_price": 5500, "description": "街道视角展示建筑外观"},
        {"camera": "Garden View", "unit_price": 4500, "description": "花园景观展示"}
    ],
    "办公建筑": [
        {"camera": "Corporate View", "unit_price": 9000, "description": "企业形象展示视角"},
        {"camera": "Plaza View", "unit_price": 7500, "description": "广场视角展示"},
        {"camera": "Interior Office", "unit_price": 6000, "description": "办公室内部展示"}
    ],
    "文化建筑": [
        {"camera": "Landmark View", "unit_price": 10000, "description": "地标建筑展示"},
        {"camera": "Cultural Atmosphere", "unit_price": 8500, "description": "文化氛围营造"},
        {"camera": "Public Space", "unit_price": 7000, "description": "公共空间展示"}
    ]
}

# 合同模板存储目录
CONTRACTS_DIR = Path("contracts")
CONTRACTS_DIR.mkdir(exist_ok=True)


def generate_protocol_number() -> str:
    """生成项目协议号"""
    now = datetime.now()
    # 格式: NF + 年月 + 4位随机数
    return f"NF{now.strftime('%y%m')}{str(uuid.uuid4().int)[:4]}"


@router.get("/", response_model=ResponseModel[PaginatedResponse[ProjectResponse]])
async def get_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    client: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取项目列表"""
    
    # 构建查询条件
    query = select(Project).options(selectinload(Project.client))
    conditions = []
    
    if status:
        conditions.append(Project.status == status)
    
    if client:
        # 通过客户名称搜索
        client_query = select(Client.id).where(
            or_(
                Client.company_name.ilike(f"%{client}%"),
                Client.company_name_cn.ilike(f"%{client}%")
            )
        )
        client_result = await db.execute(client_query)
        client_ids = [row[0] for row in client_result.fetchall()]
        if client_ids:
            conditions.append(Project.client_id.in_(client_ids))
        else:
            # 如果没有找到匹配的客户，返回空结果
            return ResponseModel[PaginatedResponse[ProjectResponse]](
                data=PaginatedResponse[ProjectResponse](
                    list=[], total=0, page=page, pageSize=page_size
                )
            )
    
    if search:
        conditions.append(
            or_(
                Project.name.ilike(f"%{search}%"),
                Project.protocol_number.ilike(f"%{search}%"),
                Project.description.ilike(f"%{search}%")
            )
        )
    
    if start_date:
        conditions.append(Project.created_at >= start_date)
    
    if end_date:
        conditions.append(Project.created_at <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 获取总数
    count_query = select(func.count(Project.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Project.created_at.desc())
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    # 转换为响应格式
    project_list = [ProjectResponse.model_validate(project) for project in projects]
    
    return ResponseModel[PaginatedResponse[ProjectResponse]](
        data=PaginatedResponse[ProjectResponse](
            list=project_list,
            total=total,
            page=page,
            pageSize=page_size
        )
    )


@router.post("/", response_model=ResponseModel[ProjectResponse])
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新项目"""
    
    # 检查客户是否存在
    client_query = select(Client).where(Client.id == project_data.client_id)
    client_result = await db.execute(client_query)
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客户不存在"
        )
    
    # 生成协议号
    protocol_number = generate_protocol_number()
    
    # 计算人民币预算
    budget_cny = project_data.budget * project_data.exchange_rate
    
    # 创建项目
    project = Project(
        protocol_number=protocol_number,
        name=project_data.name,
        client_id=project_data.client_id,
        deadline=project_data.deadline,
        budget=project_data.budget,
        currency=project_data.currency,
        exchange_rate=project_data.exchange_rate,
        budget_cny=budget_cny,
        project_type=project_data.project_type,
        description=project_data.description,
        services=[item.dict() for item in project_data.services] if project_data.services else None
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return ResponseModel[ProjectResponse](
        data=ProjectResponse.model_validate(project)
    )


@router.get("/{project_id}", response_model=ResponseModel[ProjectResponse])
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取项目详情"""
    
    query = select(Project).options(selectinload(Project.client)).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    return ResponseModel[ProjectResponse](
        data=ProjectResponse.model_validate(project)
    )


@router.put("/{project_id}", response_model=ResponseModel[ProjectResponse])
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新项目信息"""
    
    # 检查项目是否存在
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 更新数据
    update_data = project_data.model_dump(exclude_unset=True)
    
    # 如果更新了预算或汇率，重新计算人民币预算
    if 'budget' in update_data or 'exchange_rate' in update_data:
        budget = update_data.get('budget', project.budget)
        exchange_rate = update_data.get('exchange_rate', project.exchange_rate)
        update_data['budget_cny'] = budget * exchange_rate
    
    # 处理services字段
    if 'services' in update_data and update_data['services']:
        update_data['services'] = [item.dict() for item in update_data['services']]
    
    if update_data:
        stmt = update(Project).where(Project.id == project_id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        
        # 重新查询更新后的项目
        result = await db.execute(query)
        project = result.scalar_one()
    
    return ResponseModel[ProjectResponse](
        data=ProjectResponse.model_validate(project)
    )


@router.delete("/{project_id}", response_model=ResponseModel[dict])
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除项目"""
    
    # 检查项目是否存在
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 删除项目
    stmt = delete(Project).where(Project.id == project_id)
    await db.execute(stmt)
    await db.commit()
    
    return ResponseModel[dict](
        data={"message": "项目删除成功"}
    )


@router.put("/{project_id}/status", response_model=ResponseModel[ProjectResponse])
async def update_project_status(
    project_id: int,
    status_data: ProjectStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新项目状态"""
    
    # 检查项目是否存在
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 更新状态
    stmt = update(Project).where(Project.id == project_id).values(status=status_data.status)
    await db.execute(stmt)
    await db.commit()
    
    # 重新查询项目
    result = await db.execute(query)
    project = result.scalar_one()
    
    return ResponseModel[ProjectResponse](
        data=ProjectResponse.model_validate(project)
    )


@router.put("/{project_id}/progress", response_model=ResponseModel[ProjectResponse])
async def update_project_progress(
    project_id: int,
    progress_data: ProjectProgressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新项目进度"""
    
    # 检查项目是否存在
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 更新进度
    stmt = update(Project).where(Project.id == project_id).values(progress=progress_data.progress)
    await db.execute(stmt)
    await db.commit()
    
    # 重新查询项目
    result = await db.execute(query)
    project = result.scalar_one()
    
    return ResponseModel[ProjectResponse](
        data=ProjectResponse.model_validate(project)
    )


@router.get("/gantt/data", response_model=ResponseModel[List[GanttProject]])
async def get_gantt_data(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取甘特图数据"""
    
    # 查询所有项目
    query = select(Project).where(Project.deadline.isnot(None))
    result = await db.execute(query)
    projects = result.scalars().all()
    
    gantt_data = []
    for project in projects:
        # 简化的甘特图数据，实际应用中可能需要更复杂的任务分解
        gantt_project = GanttProject(
            id=project.protocol_number,
            name=project.name,
            start=project.created_at.strftime("%Y-%m-%d"),
            end=project.deadline.strftime("%Y-%m-%d") if project.deadline else project.created_at.strftime("%Y-%m-%d"),
            progress=project.progress,
            dependencies=[],
            tasks=[
                {
                    "id": f"{project.protocol_number}_task1",
                    "name": "需求分析",
                    "start": project.created_at.strftime("%Y-%m-%d"),
                    "end": (project.created_at).strftime("%Y-%m-%d"),
                    "progress": 100 if project.progress > 10 else project.progress * 10
                }
            ]
        )
        gantt_data.append(gantt_project)
    
    return ResponseModel[List[GanttProject]](data=gantt_data)


@router.get("/{project_id}/contract", response_model=ResponseModel[dict])
async def get_project_contract(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取项目合同信息"""
    
    # 检查项目是否存在
    query = select(Project).options(selectinload(Project.client)).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 构建合同信息
    contract_info = {
        "contract_number": f"NFLAB-{project.protocol_number}",
        "project_info": {
            "name": project.name,
            "protocol_number": project.protocol_number,
            "type": project.project_type,
            "deadline": project.deadline.isoformat() if project.deadline else None,
            "description": project.description
        },
        "client_info": {
            "company_name": project.client.company_name if project.client else "未知客户",
            "company_name_cn": project.client.company_name_cn if project.client else None,
            "contact_person": project.client.contact_person if project.client else None,
            "email": project.client.email if project.client else None,
            "phone": project.client.phone if project.client else None
        },
        "financial_info": {
            "budget": project.budget,
            "currency": project.currency,
            "exchange_rate": project.exchange_rate,
            "budget_cny": project.budget_cny,
            "payment_terms": "预付30%，完成阶段50%，交付完成20%"
        },
        "services": project.services or [],
        "terms_and_conditions": [
            "甲方应按时提供项目所需的技术资料和设计要求",
            "乙方保证按照合同约定的时间和质量完成项目交付",
            "项目修改超过3次将产生额外费用",
            "最终交付物包括高清渲染图和源文件",
            "版权归属甲方，乙方保留作品展示权利"
        ],
        "created_at": project.created_at.isoformat(),
        "status": "草稿" if project.status == "reporting" else "正式"
    }
    
    return ResponseModel[dict](data=contract_info)


@router.post("/{project_id}/contract/generate")
async def generate_project_contract(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成项目合同PDF"""
    
    # 检查项目是否存在
    query = select(Project).options(selectinload(Project.client)).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 生成合同文件名
    contract_filename = f"NFLAB_Contract_{project.protocol_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
    contract_path = CONTRACTS_DIR / contract_filename
    
    # 模拟PDF生成过程
    # 实际应用中应该使用专业的PDF生成库如reportlab
    contract_content = f"""
NFLAB 建筑渲染服务合同

合同编号: NFLAB-{project.protocol_number}
项目名称: {project.name}
客户公司: {project.client.company_name if project.client else '未知客户'}
联系人: {project.client.contact_person if project.client else 'N/A'}

项目预算: {project.currency} {project.budget:,.2f} (约合人民币 ¥{project.budget_cny:,.2f})
截止日期: {project.deadline.strftime('%Y年%m月%d日') if project.deadline else '待定'}

服务内容:
{json.dumps(project.services, ensure_ascii=False, indent=2) if project.services else '待定'}

合同条款:
1. 甲方应按时提供项目所需的技术资料和设计要求
2. 乙方保证按照合同约定的时间和质量完成项目交付
3. 项目修改超过3次将产生额外费用
4. 最终交付物包括高清渲染图和源文件
5. 版权归属甲方，乙方保留作品展示权利

签约日期: {datetime.now().strftime('%Y年%m月%d日')}

甲方签字:________________  乙方签字:________________
    """
    
    # 写入文件（实际应用中应生成PDF）
    with open(contract_path, 'w', encoding='utf-8') as f:
        f.write(contract_content)
    
    # 返回文件下载响应
    return FileResponse(
        path=contract_path,
        filename=contract_filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={contract_filename}"}
    )


@router.get("/services/templates", response_model=ResponseModel[Dict[str, List[Dict[str, Any]]]])
async def get_service_templates(
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    current_user: User = Depends(get_current_active_user)
):
    """获取服务项目模板"""
    
    if project_type and project_type in SERVICE_TEMPLATES:
        # 返回指定类型的模板
        templates = {project_type: SERVICE_TEMPLATES[project_type]}
    else:
        # 返回所有模板
        templates = SERVICE_TEMPLATES
    
    # 添加使用统计信息
    for category, services in templates.items():
        for service in services:
            service["usage_count"] = 25 + hash(service["camera"]) % 50  # 模拟使用次数
            service["category"] = category
    
    return ResponseModel[Dict[str, List[Dict[str, Any]]]](
        data=templates,
        message=f"共获取到 {len(templates)} 个类别的服务模板"
    ) 
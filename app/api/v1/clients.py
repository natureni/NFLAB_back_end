from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from typing import List, Optional
from datetime import datetime
import pandas as pd
import io
from pathlib import Path

from app.core.database import get_db
from app.models.user import User
from app.models.client import Client
from app.models.project import Project
from app.schemas.client import (
    ClientCreate, ClientUpdate, ClientResponse, ClientListQuery
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.api.deps import get_current_active_user

router = APIRouter()

# 客户模板和导出文件存储目录
EXPORTS_DIR = Path("exports/clients")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


# 具体路径的路由必须放在动态路径之前
@router.get("/statistics", response_model=ResponseModel[dict])
async def get_client_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取客户统计数据"""
    
    try:
        # 总客户数
        total_clients_query = select(func.count(Client.id))
        total_result = await db.execute(total_clients_query)
        total_clients = total_result.scalar() or 0
        
        # 活跃客户数
        active_clients_query = select(func.count(Client.id)).where(Client.status == "active")
        active_result = await db.execute(active_clients_query)
        active_clients = active_result.scalar() or 0
        
        # 按地区统计
        region_query = select(Client.region, func.count(Client.id)).group_by(Client.region)
        region_result = await db.execute(region_query)
        region_stats = [{"region": row[0] or "未知", "count": row[1]} for row in region_result.fetchall()]
        
        # 按业务类型统计 (简化处理)
        business_type_stats = []
        
        # 月度新增客户趋势 - 使用SQLite兼容的方式
        monthly_query = select(
            func.strftime('%Y-%m', Client.created_at).label('month'),
            func.count(Client.id).label('count')
        ).group_by(func.strftime('%Y-%m', Client.created_at)).order_by('month')
        
        monthly_result = await db.execute(monthly_query)
        monthly_stats = []
        for row in monthly_result.fetchall():
            if row[0]:  # 确保月份不为空
                monthly_stats.append({
                    "month": row[0],
                    "count": row[1]
                })
        
        return ResponseModel[dict](
            data={
                "total_clients": total_clients,
                "active_clients": active_clients,
                "inactive_clients": total_clients - active_clients,
                "region_distribution": region_stats,
                "business_type_distribution": business_type_stats,
                "monthly_growth": monthly_stats
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取客户统计失败: {str(e)}"
        )


@router.get("/template", response_model=ResponseModel[dict])
async def download_client_template(
    current_user: User = Depends(get_current_active_user)
):
    """获取客户信息导入模板"""
    
    try:
        # 返回模板结构和示例数据
        template_structure = {
            "required_fields": [
                "company_name",
                "contact_person", 
                "email",
                "phone"
            ],
            "optional_fields": [
                "company_name_cn",
                "contact_person_cn",
                "title",
                "title_cn",
                "fax",
                "website",
                "region",
                "timezone",
                "language",
                "business_type",
                "tags",
                "notes",
                "status"
            ],
            "sample_data": [
                {
                    "company_name": "URBIS",
                    "company_name_cn": "优比思",
                    "contact_person": "John Smith",
                    "contact_person_cn": "约翰·史密斯",
                    "title": "Project Manager",
                    "title_cn": "项目经理",
                    "email": "john@urbis.com.au",
                    "phone": "+61 7 3007 3800",
                    "fax": "+61 7 3007 3801",
                    "website": "https://urbis.com.au",
                    "region": "Asia-Pacific",
                    "timezone": "AEST (UTC+10)",
                    "language": "English,Mandarin",
                    "business_type": "Real Estate,Commercial Development",
                    "tags": "VIP客户,长期合作",
                    "notes": "重要客户备注",
                    "status": "active"
                },
                {
                    "company_name": "万科集团",
                    "company_name_cn": "万科集团",
                    "contact_person": "张经理",
                    "contact_person_cn": "张经理",
                    "title": "项目总监",
                    "title_cn": "项目总监",
                    "email": "zhang@vanke.com",
                    "phone": "+86 755 2560 1888",
                    "fax": "+86 755 2560 1889",
                    "website": "https://www.vanke.com",
                    "region": "中国大陆",
                    "timezone": "CST (UTC+8)",
                    "language": "Chinese",
                    "business_type": "房地产开发",
                    "tags": "重点客户",
                    "notes": "合作多年的老客户",
                    "status": "active"
                }
            ],
            "field_descriptions": {
                "company_name": "公司名称 (必填)",
                "company_name_cn": "公司中文名称",
                "contact_person": "联系人 (必填)",
                "contact_person_cn": "联系人中文名称",
                "title": "职位",
                "title_cn": "职位中文名称",
                "email": "邮箱 (必填，唯一)",
                "phone": "电话 (必填)",
                "fax": "传真",
                "website": "网站",
                "region": "地区 (Asia-Pacific, North America, Europe, 中国大陆等)",
                "timezone": "时区",
                "language": "语言 (多个用逗号分隔)",
                "business_type": "业务类型 (多个用逗号分隔)",
                "tags": "标签 (多个用逗号分隔)",
                "notes": "备注",
                "status": "状态 (active或inactive)"
            },
            "import_instructions": [
                "1. 请按照模板格式填写客户信息",
                "2. 标记为必填的字段不能为空",
                "3. language和business_type多个值用英文逗号分隔",
                "4. status可选值：active, inactive",
                "5. region建议值：Asia-Pacific, North America, Europe, 中国大陆",
                "6. 邮箱必须唯一，重复的邮箱将跳过导入",
                "7. 建议单次导入不超过1000条记录"
            ]
        }
        
        return ResponseModel[dict](
            data=template_structure,
            message="客户导入模板结构获取成功"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板失败: {str(e)}"
        )


@router.post("/import", response_model=ResponseModel[dict])
async def import_clients(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """导入客户数据"""
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件格式不支持，请上传Excel或CSV文件"
        )
    
    try:
        # 读取文件内容
        content = await file.read()
        
        # 根据文件类型读取数据
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # 验证必需列
        required_columns = ['company_name', 'contact_person', 'email', 'phone']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需列: {', '.join(missing_columns)}"
            )
        
        success_count = 0
        error_count = 0
        errors = []
        
        # 逐行处理数据
        for index, row in df.iterrows():
            try:
                # 检查必填字段
                if pd.isna(row['company_name']) or pd.isna(row['contact_person']) or \
                   pd.isna(row['email']) or pd.isna(row['phone']):
                    errors.append(f"第{index+2}行: 必填字段不能为空")
                    error_count += 1
                    continue
                
                # 检查邮箱是否已存在
                existing_query = select(Client).where(Client.email == row['email'])
                existing_result = await db.execute(existing_query)
                existing_client = existing_result.scalar_one_or_none()
                
                if existing_client:
                    errors.append(f"第{index+2}行: 邮箱 {row['email']} 已存在")
                    error_count += 1
                    continue
                
                # 创建客户
                client_data = {
                    'company_name': row['company_name'],
                    'company_name_cn': row.get('company_name_cn', ''),
                    'contact_person': row['contact_person'],
                    'contact_person_cn': row.get('contact_person_cn', ''),
                    'title': row.get('title', ''),
                    'title_cn': row.get('title_cn', ''),
                    'email': row['email'],
                    'phone': row['phone'],
                    'fax': row.get('fax', ''),
                    'website': row.get('website', ''),
                    'region': row.get('region', 'Asia-Pacific'),
                    'timezone': row.get('timezone', 'UTC+8'),
                    'language': row.get('language', 'English').split(',') if row.get('language') else ['English'],
                    'business_type': row.get('business_type', 'Real Estate').split(',') if row.get('business_type') else ['Real Estate'],
                    'tags': row.get('tags', '').split(',') if row.get('tags') else [],
                    'notes': row.get('notes', ''),
                    'status': row.get('status', 'active')
                }
                
                client = Client(**client_data)
                db.add(client)
                success_count += 1
                
            except Exception as e:
                errors.append(f"第{index+2}行: {str(e)}")
                error_count += 1
        
        # 提交所有成功的导入
        if success_count > 0:
            await db.commit()
        
        return ResponseModel[dict](
            data={
                "success_count": success_count,
                "error_count": error_count,
                "total_count": len(df),
                "errors": errors[:10]  # 只返回前10个错误
            },
            message=f"导入完成: 成功 {success_count} 条，失败 {error_count} 条"
        )
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件为空或格式错误"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@router.get("/export")
async def export_clients(
    format: str = Query("excel", regex="^(excel|csv)$"),
    region: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """导出客户数据"""
    
    # 构建查询条件
    query = select(Client)
    conditions = []
    
    if region:
        conditions.append(Client.region == region)
    if status:
        conditions.append(Client.status == status)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 查询客户数据
    result = await db.execute(query)
    clients = result.scalars().all()
    
    if not clients:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到符合条件的客户数据"
        )
    
    # 准备导出数据
    export_data = []
    for client in clients:
        export_data.append({
            'ID': client.id,
            'company_name': client.company_name,
            'company_name_cn': client.company_name_cn or '',
            'contact_person': client.contact_person,
            'contact_person_cn': client.contact_person_cn or '',
            'title': client.title or '',
            'title_cn': client.title_cn or '',
            'email': client.email,
            'phone': client.phone,
            'fax': client.fax or '',
            'website': client.website or '',
            'region': client.region,
            'timezone': client.timezone or '',
            'language': ','.join(client.language) if client.language else '',
            'business_type': ','.join(client.business_type) if client.business_type else '',
            'tags': ','.join(client.tags) if client.tags else '',
            'notes': client.notes or '',
            'status': client.status,
            'created_at': client.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'total_projects': client.project_history.get('total', 0) if client.project_history else 0,
            'total_value': client.project_history.get('value', 0) if client.project_history else 0
        })
    
    # 创建DataFrame
    df = pd.DataFrame(export_data)
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if format == "excel":
        filename = f"clients_export_{timestamp}.xlsx"
        filepath = EXPORTS_DIR / filename
        df.to_excel(filepath, index=False, engine='openpyxl')
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        filename = f"clients_export_{timestamp}.csv"
        filepath = EXPORTS_DIR / filename
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        media_type = "text/csv"
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# 现在放置动态路径的路由
@router.get("/", response_model=ResponseModel[PaginatedResponse[ClientResponse]])
async def get_clients(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    region: Optional[str] = Query(None, description="地区筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取客户列表"""
    
    try:
        # 构建查询条件
        query = select(Client)
        conditions = []
        
        if region:
            conditions.append(Client.region == region)
        
        if status:
            conditions.append(Client.status == status)
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    Client.company_name.ilike(search_term),
                    Client.company_name_cn.ilike(search_term),
                    Client.contact_person.ilike(search_term),
                    Client.contact_person_cn.ilike(search_term),
                    Client.email.ilike(search_term)
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 获取总数
        count_query = select(func.count(Client.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页查询
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Client.created_at.desc())
        
        result = await db.execute(query)
        clients = result.scalars().all()
        
        # 转换为响应格式
        client_list = []
        for client in clients:
            try:
                client_response = ClientResponse.model_validate(client)
                client_list.append(client_response)
            except Exception as e:
                # 记录但不中断处理
                print(f"Client {client.id} validation error: {e}")
                continue
        
        return ResponseModel[PaginatedResponse[ClientResponse]](
            data=PaginatedResponse[ClientResponse](
                list=client_list,
                total=total,
                page=page,
                pageSize=page_size
            )
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取客户列表失败: {str(e)}"
        )


@router.post("/", response_model=ResponseModel[ClientResponse])
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新客户"""
    
    # 检查邮箱是否已存在
    existing_query = select(Client).where(Client.email == client_data.email)
    existing_result = await db.execute(existing_query)
    existing_client = existing_result.scalar_one_or_none()
    
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被使用"
        )
    
    # 创建客户数据字典
    client_dict = client_data.model_dump()
    
    # 处理嵌套对象，转换为JSON
    if client_dict.get('business_address'):
        client_dict['business_address'] = client_dict['business_address']
    
    if client_dict.get('project_preferences'):
        client_dict['project_preferences'] = client_dict['project_preferences']
    
    if client_dict.get('payment_info'):
        client_dict['payment_info'] = client_dict['payment_info']
    
    if client_dict.get('bank_info'):
        client_dict['bank_info'] = client_dict['bank_info']
    
    # 初始化项目历史
    client_dict['project_history'] = {
        "total": 0,
        "completed": 0,
        "ongoing": 0,
        "value": 0
    }
    
    # 创建客户
    client = Client(**client_dict)
    
    db.add(client)
    await db.commit()
    await db.refresh(client)
    
    return ResponseModel[ClientResponse](
        data=ClientResponse.model_validate(client)
    )


@router.get("/{client_id}", response_model=ResponseModel[ClientResponse])
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取客户详情"""
    
    query = select(Client).where(Client.id == client_id)
    result = await db.execute(query)
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客户不存在"
        )
    
    return ResponseModel[ClientResponse](
        data=ClientResponse.model_validate(client)
    )


@router.put("/{client_id}", response_model=ResponseModel[ClientResponse])
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新客户信息"""
    
    # 检查客户是否存在
    query = select(Client).where(Client.id == client_id)
    result = await db.execute(query)
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客户不存在"
        )
    
    # 如果更新邮箱，检查是否已被其他客户使用
    if client_data.email and client_data.email != client.email:
        existing_query = select(Client).where(
            and_(Client.email == client_data.email, Client.id != client_id)
        )
        existing_result = await db.execute(existing_query)
        existing_client = existing_result.scalar_one_or_none()
        
        if existing_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被使用"
            )
    
    # 更新数据
    update_data = client_data.model_dump(exclude_unset=True)
    
    if update_data:
        stmt = update(Client).where(Client.id == client_id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        
        # 重新查询更新后的客户
        result = await db.execute(query)
        client = result.scalar_one()
    
    return ResponseModel[ClientResponse](
        data=ClientResponse.model_validate(client)
    )


@router.delete("/{client_id}", response_model=ResponseModel[dict])
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除客户"""
    
    # 检查客户是否存在
    query = select(Client).where(Client.id == client_id)
    result = await db.execute(query)
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客户不存在"
        )
    
    # 检查是否有关联的项目
    project_query = select(Project).where(Project.client_id == client_id)
    project_result = await db.execute(project_query)
    projects = project_result.scalars().all()
    
    if projects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法删除客户，该客户有 {len(projects)} 个关联项目"
        )
    
    # 删除客户
    stmt = delete(Client).where(Client.id == client_id)
    await db.execute(stmt)
    await db.commit()
    
    return ResponseModel[dict](
        data={"message": "客户删除成功"}
    )


@router.get("/{client_id}/projects", response_model=ResponseModel[List[dict]])
async def get_client_projects(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取客户相关项目"""
    
    # 检查客户是否存在
    client_query = select(Client).where(Client.id == client_id)
    client_result = await db.execute(client_query)
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客户不存在"
        )
    
    # 查询客户项目
    project_query = select(Project).where(Project.client_id == client_id)
    project_result = await db.execute(project_query)
    projects = project_result.scalars().all()
    
    # 简化的项目信息
    project_list = []
    for project in projects:
        project_list.append({
            "id": project.id,
            "protocol_number": project.protocol_number,
            "name": project.name,
            "status": project.status,
            "budget": project.budget,
            "currency": project.currency,
            "progress": project.progress,
            "created_at": project.created_at
        })
    
    return ResponseModel[List[dict]](data=project_list)


@router.put("/{client_id}/project-history", response_model=ResponseModel[ClientResponse])
async def update_client_project_history(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """自动更新客户项目历史"""
    
    # 检查客户是否存在
    client_query = select(Client).where(Client.id == client_id)
    client_result = await db.execute(client_query)
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客户不存在"
        )
    
    # 统计项目信息
    project_query = select(Project).where(Project.client_id == client_id)
    project_result = await db.execute(project_query)
    projects = project_result.scalars().all()
    
    total = len(projects)
    completed = len([p for p in projects if p.status == "completed"])
    ongoing = len([p for p in projects if p.status in ["reporting", "modeling", "rendering", "delivering"]])
    value = sum(p.budget_cny for p in projects)
    
    # 更新项目历史
    project_history = {
        "total": total,
        "completed": completed,
        "ongoing": ongoing,
        "value": value
    }
    
    stmt = update(Client).where(Client.id == client_id).values(project_history=project_history)
    await db.execute(stmt)
    await db.commit()
    
    # 重新查询客户
    result = await db.execute(client_query)
    client = result.scalar_one()
    
    return ResponseModel[ClientResponse](
        data=ClientResponse.model_validate(client)
    ) 
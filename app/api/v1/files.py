from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import os
import uuid
import aiofiles
from pathlib import Path
import mimetypes
from io import BytesIO

from app.api.deps import get_current_user, get_async_session
from app.schemas.files import (
    FileInfoResponse, FileUploadResponse, 
    ContractGenerateRequest, ReportGenerateRequest
)
from app.models.user import User

router = APIRouter()

# 文件存储配置
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 支持的文件类型
ALLOWED_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
    'spreadsheet': ['.xls', '.xlsx', '.csv'],
    'archive': ['.zip', '.rar', '.7z'],
    'cad': ['.dwg', '.dxf', '.skp', '.3ds', '.max']
}

# 最大文件大小 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# 模拟文件数据库
_file_storage = []


def get_file_type(extension: str) -> str:
    """根据文件扩展名获取文件类型"""
    extension = extension.lower()
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if extension in extensions:
            return file_type
    return 'other'


def is_allowed_file(filename: str) -> bool:
    """检查文件是否被允许上传"""
    if not filename:
        return False
    
    extension = os.path.splitext(filename)[1].lower()
    all_extensions = []
    for extensions in ALLOWED_EXTENSIONS.values():
        all_extensions.extend(extensions)
    
    return extension in all_extensions


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    project_id: Optional[int] = None,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """上传文件"""
    
    # 检查文件类型
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型。支持的类型：{', '.join(sum(ALLOWED_EXTENSIONS.values(), []))}"
        )
    
    # 检查文件大小
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // (1024*1024)}MB）"
        )
    
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1]
    stored_filename = f"{file_id}{extension}"
    file_path = UPLOAD_DIR / stored_filename
    
    # 保存文件
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    # 获取文件信息
    file_type = get_file_type(extension)
    mime_type, _ = mimetypes.guess_type(file.filename)
    
    # 保存文件信息到模拟数据库
    file_info = {
        "id": len(_file_storage) + 1,
        "file_id": file_id,
        "original_filename": file.filename,
        "stored_filename": stored_filename,
        "file_path": str(file_path),
        "file_type": file_type,
        "mime_type": mime_type or "application/octet-stream",
        "file_size": len(file_content),
        "project_id": project_id,
        "description": description,
        "uploaded_by": current_user.id,
        "uploaded_at": datetime.now()
    }
    
    _file_storage.append(file_info)
    
    return FileUploadResponse(
        file_id=file_id,
        filename=file.filename,
        file_type=file_type,
        file_size=len(file_content),
        upload_url=f"/api/files/{file_id}",
        message="文件上传成功"
    )


@router.get("/{file_id}", response_model=FileInfoResponse)
async def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取文件信息"""
    
    file_info = next((f for f in _file_storage if f["file_id"] == file_id), None)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileInfoResponse(**file_info)


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """下载文件"""
    
    file_info = next((f for f in _file_storage if f["file_id"] == file_id), None)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_path = Path(file_info["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件已被删除")
    
    return FileResponse(
        path=file_path,
        filename=file_info["original_filename"],
        media_type=file_info["mime_type"]
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除文件"""
    
    file_info = next((f for f in _file_storage if f["file_id"] == file_id), None)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 检查权限（只有上传者或管理员可以删除）
    if file_info["uploaded_by"] != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限删除此文件")
    
    # 删除物理文件
    file_path = Path(file_info["file_path"])
    if file_path.exists():
        os.remove(file_path)
    
    # 从模拟数据库中删除
    _file_storage.remove(file_info)
    
    return {"message": "文件删除成功", "file_id": file_id}


@router.get("/", response_model=List[FileInfoResponse])
async def list_files(
    project_id: Optional[int] = None,
    file_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取文件列表"""
    
    files = _file_storage.copy()
    
    # 按条件筛选
    if project_id:
        files = [f for f in files if f.get("project_id") == project_id]
    
    if file_type:
        files = [f for f in files if f["file_type"] == file_type]
    
    return [FileInfoResponse(**f) for f in files]


# PDF生成功能（需要安装reportlab库）
@router.post("/pdf/contract")
async def generate_contract_pdf(
    contract_data: ContractGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """生成合同PDF"""
    
    # 这里应该使用reportlab等库生成PDF
    # 为了演示，我们返回一个模拟响应
    
    contract_content = f"""
    建筑渲染服务合同
    
    甲方：{contract_data.client_name}
    乙方：NFLAB建筑渲染公司
    
    项目名称：{contract_data.project_name}
    项目金额：{contract_data.amount} {contract_data.currency}
    项目期限：{contract_data.deadline}
    
    服务内容：
    {contract_data.services}
    
    付款方式：{contract_data.payment_terms}
    
    合同编号：{contract_data.protocol_number}
    签署日期：{datetime.now().strftime('%Y年%m月%d日')}
    """
    
    # 生成PDF文件
    pdf_id = str(uuid.uuid4())
    pdf_filename = f"contract_{pdf_id}.pdf"
    pdf_path = UPLOAD_DIR / pdf_filename
    
    # 这里应该使用reportlab生成实际的PDF
    # 暂时创建一个文本文件作为演示
    async with aiofiles.open(pdf_path, 'w', encoding='utf-8') as f:
        await f.write(contract_content)
    
    # 保存到文件存储
    file_info = {
        "id": len(_file_storage) + 1,
        "file_id": pdf_id,
        "original_filename": pdf_filename,
        "stored_filename": pdf_filename,
        "file_path": str(pdf_path),
        "file_type": "document",
        "mime_type": "application/pdf",
        "file_size": len(contract_content.encode('utf-8')),
        "project_id": contract_data.project_id,
        "description": f"项目合同 - {contract_data.project_name}",
        "uploaded_by": current_user.id,
        "uploaded_at": datetime.now()
    }
    
    _file_storage.append(file_info)
    
    return {
        "message": "合同PDF生成成功",
        "file_id": pdf_id,
        "download_url": f"/api/files/{pdf_id}/download"
    }


@router.post("/pdf/report")
async def generate_report_pdf(
    report_data: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """生成报表PDF"""
    
    # 生成报表内容
    report_content = f"""
    {report_data.report_title}
    
    报表类型：{report_data.report_type}
    统计期间：{report_data.start_date} 至 {report_data.end_date}
    生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    报表数据：
    {report_data.data}
    
    生成人：{current_user.username}
    """
    
    # 生成PDF文件
    pdf_id = str(uuid.uuid4())
    pdf_filename = f"report_{pdf_id}.pdf"
    pdf_path = UPLOAD_DIR / pdf_filename
    
    # 暂时创建一个文本文件作为演示
    async with aiofiles.open(pdf_path, 'w', encoding='utf-8') as f:
        await f.write(report_content)
    
    # 保存到文件存储
    file_info = {
        "id": len(_file_storage) + 1,
        "file_id": pdf_id,
        "original_filename": pdf_filename,
        "stored_filename": pdf_filename,
        "file_path": str(pdf_path),
        "file_type": "document",
        "mime_type": "application/pdf",
        "file_size": len(report_content.encode('utf-8')),
        "project_id": None,
        "description": f"财务报表 - {report_data.report_title}",
        "uploaded_by": current_user.id,
        "uploaded_at": datetime.now()
    }
    
    _file_storage.append(file_info)
    
    return {
        "message": "报表PDF生成成功",
        "file_id": pdf_id,
        "download_url": f"/api/files/{pdf_id}/download"
    }


@router.get("/storage/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user)
):
    """获取存储统计信息"""
    
    total_files = len(_file_storage)
    total_size = sum(f["file_size"] for f in _file_storage)
    
    # 按类型统计
    type_stats = {}
    for file_info in _file_storage:
        file_type = file_info["file_type"]
        if file_type not in type_stats:
            type_stats[file_type] = {"count": 0, "size": 0}
        type_stats[file_type]["count"] += 1
        type_stats[file_type]["size"] += file_info["file_size"]
    
    return {
        "total_files": total_files,
        "total_size": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "file_types": type_stats,
        "storage_limit": MAX_FILE_SIZE,
        "allowed_extensions": ALLOWED_EXTENSIONS
    } 
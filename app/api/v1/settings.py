from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
import json

from app.api.deps import get_current_user, get_async_session
from app.schemas.settings import (
    SystemConfigResponse, SystemConfigUpdate,
    ExchangeRateResponse, ExchangeRateUpdate,
    BusinessConfigResponse, BusinessConfigUpdate
)
from app.models.user import User
from app.models.project import Currency

router = APIRouter()

# 汇率API源（示例使用免费API）
EXCHANGE_RATE_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

# 默认汇率配置（当API不可用时的备用汇率）
DEFAULT_EXCHANGE_RATES = {
    Currency.USD: 1.0,      # 美元为基准
    Currency.EUR: 0.85,     # 欧元
    Currency.AUD: 1.35,     # 澳元
    Currency.CNY: 7.2,      # 人民币
    Currency.CAD: 1.25,     # 加元
    Currency.GBP: 0.75,     # 英镑
    Currency.SGD: 1.35,     # 新加坡元
    Currency.AED: 3.67,     # 阿联酋迪拉姆
}

# 内存中的配置缓存
_config_cache = {
    "exchange_rates": DEFAULT_EXCHANGE_RATES.copy(),
    "system_config": {
        "app_name": "NFLAB项目管理系统",
        "company_name": "NFLAB建筑渲染公司",
        "contact_email": "info@nflab.com",
        "contact_phone": "+86-123-4567-8900",
        "timezone": "Asia/Shanghai",
        "date_format": "YYYY-MM-DD",
        "currency_format": "symbol",
        "language": "zh-CN",
        "debug_mode": False,
        "maintenance_mode": False
    },
    "business_config": {
        "default_currency": Currency.CNY,
        "auto_exchange_rate_sync": True,
        "project_deadline_buffer_days": 7,
        "payment_reminder_days": [7, 3, 1],
        "default_project_status": "reporting",
        "require_client_approval": True,
        "auto_generate_protocol_number": True,
        "protocol_number_prefix": "NFLAB",
        "tax_rate": 0.13,
        "default_payment_terms": 30
    },
    "last_updated": datetime.now()
}


@router.get("/system", response_model=SystemConfigResponse)
async def get_system_config(
    current_user: User = Depends(get_current_user)
):
    """获取系统配置"""
    return SystemConfigResponse(
        **_config_cache["system_config"],
        last_updated=_config_cache["last_updated"]
    )


@router.put("/system", response_model=SystemConfigResponse)
async def update_system_config(
    config_data: SystemConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新系统配置"""
    
    # 更新配置
    update_data = config_data.dict(exclude_unset=True)
    _config_cache["system_config"].update(update_data)
    _config_cache["last_updated"] = datetime.now()
    
    return SystemConfigResponse(
        **_config_cache["system_config"],
        last_updated=_config_cache["last_updated"]
    )


@router.get("/exchange-rates", response_model=ExchangeRateResponse)
async def get_exchange_rates(
    current_user: User = Depends(get_current_user)
):
    """获取汇率配置"""
    return ExchangeRateResponse(
        rates=_config_cache["exchange_rates"],
        base_currency="USD",
        last_updated=_config_cache["last_updated"],
        auto_sync=_config_cache["business_config"]["auto_exchange_rate_sync"]
    )


@router.put("/exchange-rates", response_model=ExchangeRateResponse)
async def update_exchange_rates(
    rate_data: ExchangeRateUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新汇率"""
    
    # 更新汇率
    if rate_data.rates:
        _config_cache["exchange_rates"].update(rate_data.rates)
    
    # 更新自动同步设置
    if rate_data.auto_sync is not None:
        _config_cache["business_config"]["auto_exchange_rate_sync"] = rate_data.auto_sync
    
    _config_cache["last_updated"] = datetime.now()
    
    return ExchangeRateResponse(
        rates=_config_cache["exchange_rates"],
        base_currency="USD",
        last_updated=_config_cache["last_updated"],
        auto_sync=_config_cache["business_config"]["auto_exchange_rate_sync"]
    )


async def fetch_live_exchange_rates() -> Dict[str, float]:
    """获取实时汇率"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(EXCHANGE_RATE_API_URL, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = data.get("rates", {})
                    
                    # 转换为我们支持的货币
                    supported_rates = {}
                    for currency in Currency:
                        if currency.value.upper() in rates:
                            supported_rates[currency] = rates[currency.value.upper()]
                        elif currency == Currency.USD:
                            supported_rates[currency] = 1.0
                    
                    return supported_rates
    except Exception as e:
        print(f"获取实时汇率失败: {e}")
    
    return {}


@router.post("/exchange-rates/sync")
async def sync_exchange_rates(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """同步实时汇率"""
    
    # 获取实时汇率
    live_rates = await fetch_live_exchange_rates()
    
    if live_rates:
        # 更新汇率
        _config_cache["exchange_rates"].update(live_rates)
        _config_cache["last_updated"] = datetime.now()
        
        return {
            "message": "汇率同步成功",
            "updated_currencies": list(live_rates.keys()),
            "sync_time": _config_cache["last_updated"]
        }
    else:
        return {
            "message": "汇率同步失败，使用默认汇率",
            "sync_time": datetime.now()
        }


@router.get("/business", response_model=BusinessConfigResponse)
async def get_business_config(
    current_user: User = Depends(get_current_user)
):
    """获取业务配置"""
    return BusinessConfigResponse(
        **_config_cache["business_config"],
        last_updated=_config_cache["last_updated"]
    )


@router.put("/business", response_model=BusinessConfigResponse)
async def update_business_config(
    config_data: BusinessConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新业务配置"""
    
    # 更新配置
    update_data = config_data.dict(exclude_unset=True)
    _config_cache["business_config"].update(update_data)
    _config_cache["last_updated"] = datetime.now()
    
    return BusinessConfigResponse(
        **_config_cache["business_config"],
        last_updated=_config_cache["last_updated"]
    )


@router.get("/export")
async def export_all_settings(
    current_user: User = Depends(get_current_user)
):
    """导出所有配置"""
    return {
        "system_config": _config_cache["system_config"],
        "business_config": _config_cache["business_config"],
        "exchange_rates": _config_cache["exchange_rates"],
        "export_time": datetime.now(),
        "version": "1.0"
    }


@router.post("/import")
async def import_settings(
    settings_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """导入配置"""
    
    try:
        # 验证配置数据
        if "system_config" in settings_data:
            _config_cache["system_config"].update(settings_data["system_config"])
        
        if "business_config" in settings_data:
            _config_cache["business_config"].update(settings_data["business_config"])
        
        if "exchange_rates" in settings_data:
            _config_cache["exchange_rates"].update(settings_data["exchange_rates"])
        
        _config_cache["last_updated"] = datetime.now()
        
        return {"message": "配置导入成功", "import_time": _config_cache["last_updated"]}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置导入失败: {str(e)}")


@router.post("/reset")
async def reset_settings(
    setting_type: str,
    current_user: User = Depends(get_current_user)
):
    """重置配置到默认值"""
    
    if setting_type == "exchange_rates":
        _config_cache["exchange_rates"] = DEFAULT_EXCHANGE_RATES.copy()
        message = "汇率配置已重置为默认值"
    
    elif setting_type == "system":
        _config_cache["system_config"] = {
            "app_name": "NFLAB项目管理系统",
            "company_name": "NFLAB建筑渲染公司",
            "contact_email": "info@nflab.com",
            "contact_phone": "+86-123-4567-8900",
            "timezone": "Asia/Shanghai",
            "date_format": "YYYY-MM-DD",
            "currency_format": "symbol",
            "language": "zh-CN",
            "debug_mode": False,
            "maintenance_mode": False
        }
        message = "系统配置已重置为默认值"
    
    elif setting_type == "business":
        _config_cache["business_config"] = {
            "default_currency": Currency.CNY,
            "auto_exchange_rate_sync": True,
            "project_deadline_buffer_days": 7,
            "payment_reminder_days": [7, 3, 1],
            "default_project_status": "reporting",
            "require_client_approval": True,
            "auto_generate_protocol_number": True,
            "protocol_number_prefix": "NFLAB",
            "tax_rate": 0.13,
            "default_payment_terms": 30
        }
        message = "业务配置已重置为默认值"
    
    else:
        raise HTTPException(status_code=400, detail="不支持的配置类型")
    
    _config_cache["last_updated"] = datetime.now()
    
    return {"message": message, "reset_time": _config_cache["last_updated"]} 
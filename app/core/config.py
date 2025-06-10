from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "NFLAB 项目管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    # 如果远程PostgreSQL不可用，使用SQLite作为备用
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./nflab.db"  # 本地SQLite数据库
    )
    
    # 远程PostgreSQL配置（备用）
    POSTGRES_URL: str = "postgresql://postgres:5d5c47hl@dbconn.sealosbja.site:39540/nflab"
    
    # JWT配置
    SECRET_KEY: str = "nflab-secret-key-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 24 * 60  # 24小时
    
    # CORS配置 - 支持前端开发环境
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite开发服务器
        "http://localhost:8080",
        "http://127.0.0.1:5173",  # 同时支持127.0.0.1
        "http://127.0.0.1:3000",
        "https://nflab.com"
    ]
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"
    
    # 文件上传配置
    UPLOAD_MAX_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "uploads"
    
    # 汇率API配置
    EXCHANGE_RATE_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"


settings = Settings() 
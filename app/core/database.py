from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# 根据数据库URL类型选择合适的连接字符串
if settings.DATABASE_URL.startswith("postgresql://"):
    # PostgreSQL 异步连接
    database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif settings.DATABASE_URL.startswith("sqlite"):
    # SQLite 异步连接
    database_url = settings.DATABASE_URL
else:
    # 默认使用SQLite
    database_url = "sqlite+aiosqlite:///./nflab.db"

# 创建异步数据库引擎
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True if "postgresql" in database_url else False
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 创建数据库基类
Base = declarative_base()


# 数据库依赖
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# 数据库依赖别名 (为了兼容不同的引用方式)
async def get_async_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 
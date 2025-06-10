#!/usr/bin/env python3
"""
创建管理员账户脚本
使用方法: python create_admin.py
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole, UserStatus


async def create_admin_user():
    """创建管理员用户"""
    async with AsyncSessionLocal() as session:
        try:
            # 检查是否已存在管理员
            from sqlalchemy import select
            stmt = select(User).where(User.username == "admin")
            result = await session.execute(stmt)
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print("管理员账户已存在!")
                print(f"用户名: {existing_admin.username}")
                print(f"姓名: {existing_admin.name}")
                print(f"邮箱: {existing_admin.email}")
                return
            
            # 创建管理员账户
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                name="系统管理员",
                email="admin@nflab.com",
                role=UserRole.ADMIN,
                department="管理部",
                status=UserStatus.ACTIVE
            )
            
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            print("✅ 管理员账户创建成功!")
            print(f"用户名: {admin_user.username}")
            print(f"密码: admin123")
            print(f"姓名: {admin_user.name}")
            print(f"邮箱: {admin_user.email}")
            print(f"角色: {admin_user.role}")
            print("\n⚠️  请登录后立即修改默认密码!")
            
        except Exception as e:
            print(f"❌ 创建管理员账户失败: {e}")
            await session.rollback()


if __name__ == "__main__":
    print("正在创建管理员账户...")
    asyncio.run(create_admin_user()) 
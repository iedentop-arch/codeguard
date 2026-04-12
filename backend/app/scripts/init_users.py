"""
初始化用户数据脚本
"""
import asyncio
import bcrypt

from app.core.database import async_session_maker
from app.models.models import User


def hash_password(password: str) -> str:
    """生成密码哈希"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def create_initial_users():
    """创建初始用户"""
    users_data = [
        {
            "email": "admin@codeguard.com",
            "name": "系统管理员",
            "password": "admin123",
            "role": "admin",
        },
        {
            "email": "vendor_admin@company-a.com",
            "name": "乙方管理员-A",
            "password": "vendor123",
            "role": "vendor_admin",
        },
        {
            "email": "dev@company-a.com",
            "name": "开发人员-A",
            "password": "dev123",
            "role": "vendor_dev",
        },
    ]

    async with async_session_maker() as session:
        for user_data in users_data:
            # 检查用户是否存在
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"用户 {user_data['email']} 已存在，跳过")
                continue

            # 创建新用户
            user = User(
                email=user_data["email"],
                name=user_data["name"],
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"],
                is_active=True,
                is_deleted=False,
            )
            session.add(user)
            print(f"创建用户: {user_data['email']} (密码: {user_data['password']})")

        await session.commit()
        print("初始用户创建完成！")


if __name__ == "__main__":
    asyncio.run(create_initial_users())
import asyncio

from db.models import Base
from db.session import engine


async def init_models():
    async with engine.begin() as conn:
        # 简单粗暴：如果表存在就删了重建（开发初期用）
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created!")

if __name__ == "__main__":
    asyncio.run(init_models())
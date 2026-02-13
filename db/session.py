from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 数据库 URL (这里用的是 Docker 默认配置，稍后我们会用 Docker 启动它)
# 格式: postgresql+asyncpg://user:password@host:port/dbname
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/acelogic_db"

# 1. 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False, # 设为 True 可以看到生成的 SQL，调试很有用
    future=True
)

# 2. 创建 Session 工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 3. 依赖注入函数 (Dependency) - 给 FastAPI 用
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
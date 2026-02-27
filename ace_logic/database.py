# ace_logic/database.py

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# 🚨 极其关键：导入刚才写的 Base 基类，以及所有用到了 Base 的模型文件！
# 只有在这里显式导入了，SQLAlchemy 才能在内存里“扫描”到你要建哪些表。
from ace_logic.models.auth import Base
import ace_logic.models.wallet
import ace_logic.models.game
# ==========================================
# 1. 智能识别数据库 URL
# ==========================================
# 如果系统环境变量里有 DATABASE_URL (Docker 传进来的)，就用 Docker 的；
# 如果没有，说明你在本地终端跑，就默认连本地的 5432 端口。
DEFAULT_DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/acelogic_db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# ==========================================
# 2. 创建异步引擎 (AsyncEngine)
# ==========================================
# echo=True 是开发神器！它会在控制台把底层的真实 SQL 语句全部打印出来，方便你查错。
# 生产环境部署时，改成 False 即可。
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# ==========================================
# 3. 创建异步会话工厂 (SessionMaker)
# ==========================================
# expire_on_commit=False 防止在提交事务后，对象属性过期报错（异步环境必备）
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ==========================================
# 4. 初始化建表函数 (系统启动时调用)
# ==========================================
async def init_models():
    """根据我们写的 ORM 模型，真正在 Postgres 里创建这些表"""
    async with engine.begin() as conn:
        # run_sync 是把同步的建表操作包装成异步的
        print("[数据库] 正在扫描并创建数据表...")
        await conn.run_sync(Base.metadata.create_all)
        print("[数据库] 数据表创建完成！")

# ==========================================
# 5. FastAPI 的依赖注入函数 (Dependency)
# ==========================================
async def get_db():
    """
    不管是谁（玩家查询、扣钱、存战绩），只要想用数据库，就调用这个函数。
    它会安全地分配一个连接，并在用完后自动归还给连接池。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
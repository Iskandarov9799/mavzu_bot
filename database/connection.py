from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import Base
from config import config

_engine = None
AsyncSessionLocal = None

def init_engine():
    global _engine, AsyncSessionLocal
    _engine = create_async_engine(
        config.DATABASE_URL, echo=False,
        pool_size=5, max_overflow=10,
        pool_recycle=300, pool_pre_ping=True
    )
    AsyncSessionLocal = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )

async def init_db():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tayyor!")
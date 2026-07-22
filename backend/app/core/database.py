from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from app.core.config import settings

async_engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=20, max_overflow=10)
sync_engine = create_engine(settings.DATABASE_URL_SYNC, echo=False)

AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    from app.models.all import Base as ModelBase
    async with async_engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)

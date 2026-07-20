from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession

from app.config.settings import settings


engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

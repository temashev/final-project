from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models


async def create_user(db: AsyncSession, db_user: models.User):
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


async def get_user_by_email(db: AsyncSession, email: str):
    stmt = select(models.User).where(models.User.email == email)
    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def add_token_to_blacklist(db: AsyncSession, token: models.BlackListTokens):
    db.add(token)
    await db.commit()

    return token


async def get_blacklisted_token(db: AsyncSession, token: str):
    stmt = select(models.BlackListTokens).where(models.BlackListTokens.token == token)
    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def update_user(user: models.User, db: AsyncSession):
    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user
